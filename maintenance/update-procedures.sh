#!/bin/bash

# Linux Patching Automation - Update Procedures Script
# This script automates the update process for the Linux Patching Automation system

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/var/backups/linux-patching"
LOG_FILE="/var/log/linux-patching/update.log"
DATE=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    echo -e "${level}[$(date '+%Y-%m-%d %H:%M:%S')] $message${NC}" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "$RED" "ERROR: $1"
    exit 1
}

# Success message
success() {
    log "$GREEN" "SUCCESS: $1"
}

# Warning message
warn() {
    log "$YELLOW" "WARNING: $1"
}

# Info message
info() {
    log "" "INFO: $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "This script must be run as root"
    fi
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if services are running
    if ! systemctl is-active --quiet linux-patching; then
        error_exit "Linux Patching service is not running"
    fi
    
    # Check disk space
    local available_space=$(df /var | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 1048576 ]]; then  # 1GB in KB
        error_exit "Insufficient disk space (need at least 1GB)"
    fi
    
    # Check backup directory
    mkdir -p "$BACKUP_DIR"
    
    success "Prerequisites check passed"
}

# Create backup
create_backup() {
    info "Creating backup..."
    
    local backup_name="backup-$DATE"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup database
    if command -v pg_dump &> /dev/null; then
        info "Backing up PostgreSQL database..."
        pg_dump -h localhost -U postgres linux_patching > "$backup_path/database.sql"
    elif command -v mysqldump &> /dev/null; then
        info "Backing up MySQL database..."
        mysqldump -u root -p linux_patching > "$backup_path/database.sql"
    else
        warn "No database backup tool found"
    fi
    
    # Backup configuration
    info "Backing up configuration files..."
    tar -czf "$backup_path/config.tar.gz" \
        /etc/linux-patching/ \
        /etc/prometheus/ \
        /etc/grafana/ \
        2>/dev/null || warn "Some configuration files may not exist"
    
    # Backup data
    info "Backing up data files..."
    tar -czf "$backup_path/data.tar.gz" \
        /var/lib/linux-patching/ \
        /var/log/linux-patching/ \
        2>/dev/null || warn "Some data files may not exist"
    
    # Backup source code
    info "Backing up source code..."
    tar -czf "$backup_path/source.tar.gz" \
        -C "$PROJECT_ROOT" \
        --exclude=node_modules \
        --exclude=.git \
        --exclude=__pycache__ \
        --exclude=build \
        --exclude=dist \
        .
    
    success "Backup created: $backup_path"
    echo "$backup_path" > "$BACKUP_DIR/latest-backup.txt"
}

# Update frontend
update_frontend() {
    info "Updating frontend..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Check current version
    local current_version=$(npm list --depth=0 2>/dev/null | head -1 || echo "unknown")
    info "Current frontend version: $current_version"
    
    # Update package.json
    info "Updating npm dependencies..."
    npm update
    
    # Run security audit
    info "Running security audit..."
    npm audit fix
    
    # Run tests
    info "Running tests..."
    npm test -- --watchAll=false
    
    # Build for production
    info "Building for production..."
    npm run build:secure
    
    success "Frontend update completed"
}

# Update backend
update_backend() {
    info "Updating backend..."
    
    cd "$PROJECT_ROOT/linux_patching_cli"
    
    # Check current version
    local current_version=$(pip list | grep linux-patching-cli || echo "unknown")
    info "Current backend version: $current_version"
    
    # Update dependencies
    info "Updating Python dependencies..."
    pip install --upgrade -r requirements.txt
    pip install --upgrade -r requirements-dev.txt
    
    # Run security checks
    info "Running security checks..."
    bandit -r . -x tests/ || warn "Security check completed with warnings"
    safety check || warn "Safety check completed with warnings"
    
    # Run tests
    info "Running tests..."
    pytest -v
    
    # Install updated package
    info "Installing updated package..."
    pip install -e .
    
    success "Backend update completed"
}

# Update system dependencies
update_system() {
    info "Updating system dependencies..."
    
    # Update package manager
    if command -v apt &> /dev/null; then
        info "Updating apt packages..."
        apt update
        apt upgrade -y
    elif command -v yum &> /dev/null; then
        info "Updating yum packages..."
        yum update -y
    elif command -v dnf &> /dev/null; then
        info "Updating dnf packages..."
        dnf update -y
    fi
    
    # Update Docker images if Docker is installed
    if command -v docker &> /dev/null; then
        info "Updating Docker images..."
        cd "$PROJECT_ROOT/monitoring"
        docker-compose pull
        docker-compose up -d
    fi
    
    success "System update completed"
}

# Update database schema
update_database() {
    info "Updating database schema..."
    
    # Run migration scripts if they exist
    if [[ -d "$PROJECT_ROOT/migrations" ]]; then
        info "Running database migrations..."
        cd "$PROJECT_ROOT/migrations"
        for migration in *.sql; do
            if [[ -f "$migration" ]]; then
                info "Running migration: $migration"
                if command -v psql &> /dev/null; then
                    psql -h localhost -U postgres -d linux_patching -f "$migration"
                elif command -v mysql &> /dev/null; then
                    mysql -u root -p linux_patching < "$migration"
                fi
            fi
        done
    fi
    
    success "Database update completed"
}

# Restart services
restart_services() {
    info "Restarting services..."
    
    # Stop services
    info "Stopping services..."
    systemctl stop linux-patching || warn "Failed to stop linux-patching service"
    systemctl stop prometheus || warn "Failed to stop prometheus service"
    systemctl stop grafana-server || warn "Failed to stop grafana service"
    
    # Wait for services to stop
    sleep 5
    
    # Start services
    info "Starting services..."
    systemctl start linux-patching || error_exit "Failed to start linux-patching service"
    systemctl start prometheus || warn "Failed to start prometheus service"
    systemctl start grafana-server || warn "Failed to start grafana service"
    
    # Wait for services to start
    sleep 10
    
    # Check service status
    if systemctl is-active --quiet linux-patching; then
        success "Linux Patching service is running"
    else
        error_exit "Linux Patching service failed to start"
    fi
    
    success "Services restarted"
}

# Post-update verification
verify_update() {
    info "Verifying update..."
    
    # Check service status
    if ! systemctl is-active --quiet linux-patching; then
        error_exit "Linux Patching service is not running after update"
    fi
    
    # Check API health
    if command -v curl &> /dev/null; then
        info "Checking API health..."
        local api_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
        if [[ "$api_response" != "200" ]]; then
            error_exit "API health check failed (HTTP $api_response)"
        fi
    fi
    
    # Check frontend
    if [[ -f "$PROJECT_ROOT/frontend/build/index.html" ]]; then
        success "Frontend build exists"
    else
        error_exit "Frontend build not found"
    fi
    
    # Check database connectivity
    if command -v psql &> /dev/null; then
        if psql -h localhost -U postgres -d linux_patching -c "SELECT 1;" &> /dev/null; then
            success "Database connectivity verified"
        else
            error_exit "Database connectivity check failed"
        fi
    fi
    
    success "Update verification completed"
}

# Clean up old backups
cleanup_backups() {
    info "Cleaning up old backups..."
    
    # Keep last 7 backups
    find "$BACKUP_DIR" -name "backup-*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    success "Backup cleanup completed"
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    info "Sending notification..."
    
    # Send email notification if configured
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "Linux Patching Update: $status" admin@company.com
    fi
    
    # Send Slack notification if configured
    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Linux Patching Update: $status - $message\"}" \
            "$SLACK_WEBHOOK"
    fi
    
    success "Notification sent"
}

# Main update process
main() {
    info "Starting Linux Patching Automation update process..."
    
    # Check if running as root
    check_root
    
    # Check prerequisites
    check_prerequisites
    
    # Create backup
    create_backup
    
    # Update components
    update_frontend
    update_backend
    update_system
    update_database
    
    # Restart services
    restart_services
    
    # Verify update
    verify_update
    
    # Clean up
    cleanup_backups
    
    # Send success notification
    send_notification "SUCCESS" "Update completed successfully"
    
    success "Update process completed successfully!"
}

# Rollback function
rollback() {
    info "Starting rollback process..."
    
    local backup_path
    if [[ -f "$BACKUP_DIR/latest-backup.txt" ]]; then
        backup_path=$(cat "$BACKUP_DIR/latest-backup.txt")
    else
        error_exit "No backup path found"
    fi
    
    if [[ ! -d "$backup_path" ]]; then
        error_exit "Backup directory not found: $backup_path"
    fi
    
    info "Rolling back from: $backup_path"
    
    # Stop services
    systemctl stop linux-patching
    
    # Restore database
    if [[ -f "$backup_path/database.sql" ]]; then
        info "Restoring database..."
        if command -v psql &> /dev/null; then
            dropdb -h localhost -U postgres linux_patching
            createdb -h localhost -U postgres linux_patching
            psql -h localhost -U postgres -d linux_patching < "$backup_path/database.sql"
        fi
    fi
    
    # Restore configuration
    if [[ -f "$backup_path/config.tar.gz" ]]; then
        info "Restoring configuration..."
        tar -xzf "$backup_path/config.tar.gz" -C /
    fi
    
    # Restore source code
    if [[ -f "$backup_path/source.tar.gz" ]]; then
        info "Restoring source code..."
        tar -xzf "$backup_path/source.tar.gz" -C "$PROJECT_ROOT"
    fi
    
    # Start services
    systemctl start linux-patching
    
    success "Rollback completed"
}

# Script usage
usage() {
    echo "Usage: $0 [update|rollback|help]"
    echo "  update   - Run full update process"
    echo "  rollback - Rollback to previous version"
    echo "  help     - Show this help message"
    exit 1
}

# Main script logic
case "${1:-update}" in
    update)
        main
        ;;
    rollback)
        rollback
        ;;
    help)
        usage
        ;;
    *)
        usage
        ;;
esac