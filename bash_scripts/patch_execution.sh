#!/bin/bash

SERVER_NAME="$1"
LOG_FILE="/var/log/patching/patch_execution.log"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $SERVER_NAME - $1" >> "$LOG_FILE"
    echo "$1"
}

# Function to execute patching
execute_patching() {
    log_message "Starting patch execution for $SERVER_NAME"
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check if server is reachable
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_NAME" "echo 'connectivity_test'" >/dev/null 2>&1; then
        log_message "ERROR: Cannot connect to $SERVER_NAME"
        return 1
    fi
    
    # Determine OS type
    OS_TYPE=$(ssh "$SERVER_NAME" "cat /etc/os-release | grep '^ID=' | cut -d'=' -f2 | tr -d '\"'")
    log_message "Detected OS type: $OS_TYPE"
    
    case "$OS_TYPE" in
        "rhel"|"centos"|"fedora"|"rocky"|"almalinux")
            patch_rhel_based
            ;;
        "ubuntu"|"debian")
            patch_debian_based
            ;;
        "sles"|"opensuse")
            patch_suse_based
            ;;
        *)
            log_message "ERROR: Unsupported OS type: $OS_TYPE"
            return 1
            ;;
    esac
}

# Function to patch RHEL-based systems
patch_rhel_based() {
    log_message "Executing RHEL-based patching"
    
    # Update package cache
    ssh "$SERVER_NAME" "yum clean all && yum makecache" 2>&1 | while read line; do
        log_message "YUM: $line"
    done
    
    # Apply updates
    ssh "$SERVER_NAME" "yum update -y --exclude=kernel*" 2>&1 | while read line; do
        log_message "UPDATE: $line"
    done
    
    # Check for kernel updates separately
    KERNEL_UPDATES=$(ssh "$SERVER_NAME" "yum list updates | grep kernel | wc -l")
    if [ "$KERNEL_UPDATES" -gt 0 ]; then
        log_message "Kernel updates available: $KERNEL_UPDATES"
        ssh "$SERVER_NAME" "yum update -y kernel*" 2>&1 | while read line; do
            log_message "KERNEL: $line"
        done
    fi
}

# Function to patch Debian-based systems
patch_debian_based() {
    log_message "Executing Debian-based patching"
    
    # Update package cache
    ssh "$SERVER_NAME" "apt-get update" 2>&1 | while read line; do
        log_message "APT: $line"
    done
    
    # Apply updates
    ssh "$SERVER_NAME" "DEBIAN_FRONTEND=noninteractive apt-get upgrade -y" 2>&1 | while read line; do
        log_message "UPGRADE: $line"
    done
    
    # Apply dist-upgrade for kernel and major updates
    ssh "$SERVER_NAME" "DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y" 2>&1 | while read line; do
        log_message "DIST-UPGRADE: $line"
    done
    
    # Clean up
    ssh "$SERVER_NAME" "apt-get autoremove -y && apt-get autoclean" 2>&1 | while read line; do
        log_message "CLEANUP: $line"
    done
}

# Function to patch SUSE-based systems
patch_suse_based() {
    log_message "Executing SUSE-based patching"
    
    # Refresh repositories
    ssh "$SERVER_NAME" "zypper refresh" 2>&1 | while read line; do
        log_message "ZYPPER: $line"
    done
    
    # Apply patches
    ssh "$SERVER_NAME" "zypper patch -y" 2>&1 | while read line; do
        log_message "PATCH: $line"
    done
    
    # Apply updates
    ssh "$SERVER_NAME" "zypper update -y" 2>&1 | while read line; do
        log_message "UPDATE: $line"
    done
}

# Function to check if reboot is required
check_reboot_required() {
    if ssh "$SERVER_NAME" "test -f /var/run/reboot-required" 2>/dev/null; then
        return 0
    elif ssh "$SERVER_NAME" "command -v needs-restarting >/dev/null 2>&1 && needs-restarting -r" 2>/dev/null; then
        return $?
    else
        # Default to requiring reboot for safety
        return 0
    fi
}

# Main execution
log_message "Patch execution script started"

# Execute the patching
if execute_patching; then
    log_message "Patching completed successfully"
    
    # Run patch validation
    python3 "$PARENT_DIR/scripts/step5_patch_validation.py" "$SERVER_NAME"
    VALIDATION_RESULT=$?
    
    if [ $VALIDATION_RESULT -eq 0 ]; then
        log_message "Patch validation passed"
        
        # Check if reboot is required
        if check_reboot_required; then
            log_message "Reboot required - scheduling reboot"
            
            # Schedule reboot for the configured time
            # This should be called at the exact patch time
            ssh "$SERVER_NAME" "shutdown -r +1 'System reboot for patching - scheduled maintenance'" 2>&1 | while read line; do
                log_message "REBOOT: $line"
            done
            
            # Start post-patch validation in background
            nohup python3 "$PARENT_DIR/scripts/step6_post_patch.py" "$SERVER_NAME" > /dev/null 2>&1 &
            
        else
            log_message "No reboot required"
            # Run post-patch validation immediately
            python3 "$PARENT_DIR/scripts/step6_post_patch.py" "$SERVER_NAME"
        fi
    else
        log_message "Patch validation failed - aborting reboot"
        exit 1
    fi
else
    log_message "Patching failed"
    exit 1
fi

log_message "Patch execution script completed"
