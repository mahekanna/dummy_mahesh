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

# Function to execute patching using configured remote script
execute_patching() {
    log_message "Starting patch execution for $SERVER_NAME"
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check if server is reachable
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_NAME" "echo 'connectivity_test'" >/dev/null 2>&1; then
        log_message "ERROR: Cannot connect to $SERVER_NAME"
        return 1
    fi
    
    # Get patching script path from Python configuration
    PATCHING_SCRIPT_PATH=$(python3 -c "
import sys
sys.path.insert(0, '$PARENT_DIR')
from config.settings import Config
print(Config.PATCHING_SCRIPT_PATH)
")
    
    log_message "Using remote patching script: $PATCHING_SCRIPT_PATH"
    
    # Check if script validation is enabled
    VALIDATE_SCRIPT=$(python3 -c "
import sys
sys.path.insert(0, '$PARENT_DIR')
from config.settings import Config
print('true' if Config.VALIDATE_PATCHING_SCRIPT else 'false')
")
    
    # Validate script exists and is executable if validation is enabled
    if [ "$VALIDATE_SCRIPT" = "true" ]; then
        log_message "Validating remote patching script"
        
        if ! ssh "$SERVER_NAME" "test -f '$PATCHING_SCRIPT_PATH'"; then
            log_message "ERROR: Patching script $PATCHING_SCRIPT_PATH not found on $SERVER_NAME"
            return 1
        fi
        
        if ! ssh "$SERVER_NAME" "test -x '$PATCHING_SCRIPT_PATH'"; then
            log_message "ERROR: Patching script $PATCHING_SCRIPT_PATH is not executable on $SERVER_NAME"
            return 1
        fi
        
        log_message "Remote patching script validation passed"
    fi
    
    # Execute the remote patching script
    log_message "Executing remote patching script on $SERVER_NAME"
    
    # Execute script with server name as argument and stream output
    ssh "$SERVER_NAME" "sudo $PATCHING_SCRIPT_PATH $SERVER_NAME" 2>&1 | while read line; do
        log_message "REMOTE: $line"
    done
    
    # Check exit status of the remote script
    PATCH_EXIT_CODE=${PIPESTATUS[0]}
    
    if [ $PATCH_EXIT_CODE -eq 0 ]; then
        log_message "Remote patching script completed successfully"
        return 0
    else
        log_message "ERROR: Remote patching script failed with exit code $PATCH_EXIT_CODE"
        return 1
    fi
}

# Note: OS-specific patching functions removed
# The system now uses the configurable remote patching script
# defined in PATCHING_SCRIPT_PATH configuration setting

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
