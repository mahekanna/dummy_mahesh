#!/bin/bash

# Linux Patching Automation Cleanup Script
# Removes failed or unwanted installations completely
# Use with caution - this will delete all data!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration - Update these if you changed defaults during installation
INSTALL_DIR="/opt/linux_patching_automation"
SERVICE_USER="patchadmin"
SERVICE_GROUP="patchadmin"
LOG_DIR="/var/log/patching"
BACKUP_DIR="/backup/patching"
CONFIG_DIR="/etc/patching"
DB_NAME="patching_db"
DB_USER="patchadmin"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
}

prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    local response
    
    while true; do
        if [[ "$default" == "y" ]]; then
            echo -e "${BLUE}[INPUT]${NC} $prompt [Y/n]: "
        else
            echo -e "${BLUE}[INPUT]${NC} $prompt [y/N]: "
        fi
        read response
        
        # Use default if empty
        if [[ -z "$response" ]]; then
            response="$default"
        fi
        
        case "$response" in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo]) return 1 ;;
            *) log_error "Please answer yes or no." ;;
        esac
    done
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Show what will be removed
show_cleanup_summary() {
    log_section "CLEANUP SUMMARY"
    echo -e "${RED}WARNING: This will permanently remove:${NC}"
    echo
    echo "Services:"
    echo "  • patching-portal systemd service"
    echo "  • patching-monitor systemd service"
    echo
    echo "System User & Group:"
    echo "  • User: $SERVICE_USER"
    echo "  • Group: $SERVICE_GROUP"
    echo
    echo "Directories & Files:"
    echo "  • $INSTALL_DIR (application files)"
    echo "  • $LOG_DIR (log files)"
    echo "  • $BACKUP_DIR (backup files)"
    echo "  • $CONFIG_DIR (configuration files)"
    echo "  • /etc/systemd/system/patching-*.service"
    echo "  • /etc/sudoers.d/patching"
    echo "  • /etc/logrotate.d/patching"
    echo
    echo "Database (Optional):"
    echo "  • PostgreSQL database: $DB_NAME"
    echo "  • PostgreSQL user: $DB_USER"
    echo
    echo "Network & Firewall:"
    echo "  • Firewall rules for port 5001"
    echo
    echo -e "${RED}This action cannot be undone!${NC}"
    echo
}

# Stop and remove services
cleanup_services() {
    log_section "Removing Services"
    
    for service in patching-portal patching-monitor; do
        if systemctl is-active --quiet $service 2>/dev/null; then
            log_info "Stopping service: $service"
            systemctl stop $service || true
        fi
        
        if systemctl is-enabled --quiet $service 2>/dev/null; then
            log_info "Disabling service: $service"
            systemctl disable $service || true
        fi
        
        if [[ -f "/etc/systemd/system/$service.service" ]]; then
            log_info "Removing service file: $service.service"
            rm -f "/etc/systemd/system/$service.service"
        fi
    done
    
    # Reload systemd
    systemctl daemon-reload || true
    log_info "Services removed successfully"
}

# Remove directories and files
cleanup_files() {
    log_section "Removing Files and Directories"
    
    # Remove main installation directory
    if [[ -d "$INSTALL_DIR" ]]; then
        log_info "Removing installation directory: $INSTALL_DIR"
        rm -rf "$INSTALL_DIR"
    fi
    
    # Remove log directory
    if [[ -d "$LOG_DIR" ]]; then
        log_info "Removing log directory: $LOG_DIR"
        rm -rf "$LOG_DIR"
    fi
    
    # Remove backup directory
    if [[ -d "$BACKUP_DIR" ]]; then
        log_info "Removing backup directory: $BACKUP_DIR"
        rm -rf "$BACKUP_DIR"
    fi
    
    # Remove config directory
    if [[ -d "$CONFIG_DIR" ]]; then
        log_info "Removing config directory: $CONFIG_DIR"
        rm -rf "$CONFIG_DIR"
    fi
    
    # Remove sudoers file
    if [[ -f "/etc/sudoers.d/patching" ]]; then
        log_info "Removing sudoers file: /etc/sudoers.d/patching"
        rm -f "/etc/sudoers.d/patching"
    fi
    
    # Remove logrotate file
    if [[ -f "/etc/logrotate.d/patching" ]]; then
        log_info "Removing logrotate file: /etc/logrotate.d/patching"
        rm -f "/etc/logrotate.d/patching"
    fi
    
    # Remove environment file
    if [[ -f "/opt/linux_patching_automation/.env" ]]; then
        log_info "Removing environment file: .env"
        rm -f "/opt/linux_patching_automation/.env"
    fi
    
    # Remove temporary files
    rm -f /tmp/patching_paused /tmp/schedule_frozen 2>/dev/null || true
    
    log_info "Files and directories removed successfully"
}

# Remove user and group
cleanup_user() {
    log_section "Removing User and Group"
    
    # Remove user
    if id -u "$SERVICE_USER" &>/dev/null; then
        log_info "Removing user: $SERVICE_USER"
        # Kill any processes running as this user
        pkill -u "$SERVICE_USER" 2>/dev/null || true
        sleep 2
        userdel -r "$SERVICE_USER" 2>/dev/null || userdel "$SERVICE_USER" 2>/dev/null || true
    else
        log_warn "User $SERVICE_USER does not exist"
    fi
    
    # Remove group
    if getent group "$SERVICE_GROUP" &>/dev/null; then
        log_info "Removing group: $SERVICE_GROUP"
        groupdel "$SERVICE_GROUP" 2>/dev/null || true
    else
        log_warn "Group $SERVICE_GROUP does not exist"
    fi
    
    log_info "User and group cleanup completed"
}

# Database cleanup
cleanup_database() {
    log_section "Database Cleanup"
    
    if prompt_yes_no "Remove PostgreSQL database '$DB_NAME' and user '$DB_USER'?" "n"; then
        log_warn "Removing PostgreSQL database and user..."
        
        # Check if PostgreSQL is running
        if systemctl is-active --quiet postgresql 2>/dev/null || systemctl is-active --quiet postgresql-* 2>/dev/null; then
            # Drop database
            sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
            log_info "Database '$DB_NAME' removed"
            
            # Drop user
            sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" 2>/dev/null || true
            log_info "Database user '$DB_USER' removed"
        else
            log_warn "PostgreSQL service is not running, skipping database cleanup"
        fi
    else
        log_info "Skipping database cleanup"
    fi
}

# Firewall cleanup
cleanup_firewall() {
    log_section "Firewall Cleanup"
    
    if command -v firewall-cmd &> /dev/null; then
        log_info "Removing firewall rules for port 5001..."
        firewall-cmd --permanent --remove-port=5001/tcp 2>/dev/null || true
        firewall-cmd --reload 2>/dev/null || true
        log_info "Firewall rules removed"
    elif command -v ufw &> /dev/null; then
        log_info "Removing UFW rules for port 5001..."
        ufw delete allow 5001 2>/dev/null || true
        log_info "UFW rules removed"
    elif command -v iptables &> /dev/null; then
        log_info "Removing iptables rules for port 5001..."
        iptables -D INPUT -p tcp --dport 5001 -j ACCEPT 2>/dev/null || true
        log_info "iptables rules removed (not persistent)"
    else
        log_warn "No supported firewall found"
    fi
}

# Python cleanup
cleanup_python() {
    log_section "Python Cleanup"
    
    if [[ -d "/opt/python311" ]]; then
        if prompt_yes_no "Remove custom Python 3.11 installation at /opt/python311?" "n"; then
            log_info "Removing custom Python installation..."
            rm -rf "/opt/python311"
            
            # Remove from PATH in system files
            sed -i '/\/opt\/python311\/bin/d' /etc/profile 2>/dev/null || true
            sed -i '/\/opt\/python311\/bin/d' /etc/bash.bashrc 2>/dev/null || true
            sed -i '/\/opt\/python311\/bin/d' /root/.bashrc 2>/dev/null || true
            
            log_info "Custom Python installation removed"
        fi
    fi
}

# Cron jobs cleanup
cleanup_cron() {
    log_section "Cron Jobs Cleanup"
    
    # Remove cron jobs for patchadmin user
    if id -u "$SERVICE_USER" &>/dev/null; then
        log_info "Removing cron jobs for $SERVICE_USER..."
        crontab -u "$SERVICE_USER" -r 2>/dev/null || true
    fi
    
    # Remove any system cron jobs related to patching
    find /etc/cron.d/ -name "*patching*" -delete 2>/dev/null || true
    find /etc/cron.hourly/ -name "*patching*" -delete 2>/dev/null || true
    find /etc/cron.daily/ -name "*patching*" -delete 2>/dev/null || true
    
    log_info "Cron jobs cleanup completed"
}

# Main cleanup function
main_cleanup() {
    log_section "Starting Cleanup Process"
    
    cleanup_services
    cleanup_cron
    cleanup_files
    cleanup_user
    cleanup_database
    cleanup_firewall
    cleanup_python
    
    log_section "Cleanup Completed Successfully"
    log_info "All Linux Patching Automation components have been removed"
    log_info "You can now run the deployment script again if needed"
}

# Selective cleanup menu
selective_cleanup() {
    log_section "Selective Cleanup"
    echo "Choose what to remove:"
    echo "1) Services only"
    echo "2) Files and directories only"  
    echo "3) User and group only"
    echo "4) Database only"
    echo "5) Everything (full cleanup)"
    echo "6) Cancel"
    
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1)
            cleanup_services
            ;;
        2)
            cleanup_files
            ;;
        3)
            cleanup_user
            ;;
        4)
            cleanup_database
            ;;
        5)
            main_cleanup
            ;;
        6)
            log_info "Cleanup cancelled"
            exit 0
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Check if system was installed
check_installation() {
    local found_components=()
    
    # Check for installation directory
    [[ -d "$INSTALL_DIR" ]] && found_components+=("Installation directory")
    
    # Check for services
    [[ -f "/etc/systemd/system/patching-portal.service" ]] && found_components+=("Services")
    
    # Check for user
    id -u "$SERVICE_USER" &>/dev/null && found_components+=("System user")
    
    # Check for database
    if command -v psql &>/dev/null && sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME" 2>/dev/null; then
        found_components+=("Database")
    fi
    
    if [[ ${#found_components[@]} -eq 0 ]]; then
        log_warn "No Linux Patching Automation components found on this system"
        exit 0
    else
        log_info "Found components: ${found_components[*]}"
    fi
}

# Main script
main() {
    check_root
    
    log_section "Linux Patching Automation Cleanup Script"
    echo "This script will help you remove Linux Patching Automation from your system"
    echo
    
    # Check what's installed
    check_installation
    
    # Ask cleanup type
    if prompt_yes_no "Do you want to see what will be removed first?" "y"; then
        show_cleanup_summary
        echo
    fi
    
    if prompt_yes_no "Do you want to perform selective cleanup?" "n"; then
        selective_cleanup
    else
        if prompt_yes_no "Are you sure you want to perform COMPLETE cleanup?" "n"; then
            main_cleanup
        else
            log_info "Cleanup cancelled by user"
            exit 0
        fi
    fi
}

# Run main function
main "$@"