#!/bin/bash

# Quick Cleanup Script for Common Deployment Failures
# This script handles the most common cleanup scenarios

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (sudo)"
    exit 1
fi

echo "Quick Cleanup for Linux Patching Automation"
echo "==========================================="
echo

# Stop services if they exist
log_info "Stopping services..."
systemctl stop patching-portal 2>/dev/null || true
systemctl stop patching-monitor 2>/dev/null || true
systemctl disable patching-portal 2>/dev/null || true
systemctl disable patching-monitor 2>/dev/null || true

# Remove service files
log_info "Removing service files..."
rm -f /etc/systemd/system/patching-portal.service
rm -f /etc/systemd/system/patching-monitor.service
systemctl daemon-reload

# Remove main installation (but keep backups)
if [[ -d "/opt/linux_patching_automation" ]]; then
    log_warn "Removing /opt/linux_patching_automation..."
    rm -rf "/opt/linux_patching_automation"
fi

# Clean up processes
log_info "Cleaning up processes..."
pkill -f "patching" 2>/dev/null || true
pkill -u patchadmin 2>/dev/null || true

# Remove temporary files
log_info "Removing temporary files..."
rm -f /tmp/patching_paused /tmp/schedule_frozen 2>/dev/null || true

# Remove sudoers file
rm -f /etc/sudoers.d/patching 2>/dev/null || true

log_info "Quick cleanup completed!"
echo
echo "What was cleaned:"
echo "• Stopped and disabled services"
echo "• Removed service files"
echo "• Removed installation directory"
echo "• Killed running processes"
echo "• Removed temporary files"
echo
echo "What was NOT cleaned (use full cleanup script if needed):"
echo "• patchadmin user and group"
echo "• PostgreSQL database and user"
echo "• Log and backup directories"
echo "• Firewall rules"
echo
echo "You can now run the deployment script again."
echo "For complete cleanup, use: ./cleanup_installation.sh"