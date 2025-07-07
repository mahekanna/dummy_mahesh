#!/bin/bash

SERVER_NAME="$1"
LOG_FILE="/var/log/patching/disk_check.log"

# Configuration
ROOT_THRESHOLD=80
BOOT_THRESHOLD=70
VAR_THRESHOLD=85

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $SERVER_NAME - $1" >> "$LOG_FILE"
}

# Function to check disk usage
check_disk_usage() {
    local mount_point="$1"
    local threshold="$2"
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_NAME" "df -h $mount_point" >/dev/null 2>&1; then
        usage=$(ssh "$SERVER_NAME" "df -h $mount_point | tail -1 | awk '{print \$5}' | sed 's/%//'")
        
        if [ "$usage" -gt "$threshold" ]; then
            log_message "ALERT: $mount_point usage is ${usage}% (threshold: ${threshold}%)"
            echo "FAIL: $mount_point usage ${usage}% exceeds threshold ${threshold}%"
            return 1
        else
            log_message "OK: $mount_point usage is ${usage}% (threshold: ${threshold}%)"
            echo "PASS: $mount_point usage ${usage}%"
        fi
    else
        log_message "ERROR: Cannot check $mount_point on $SERVER_NAME"
        echo "ERROR: Cannot access $mount_point"
        return 1
    fi
    
    return 0
}

# Main execution
log_message "Starting disk space check"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Check if server is reachable
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_NAME" "echo 'connectivity_test'" >/dev/null 2>&1; then
    log_message "ERROR: Cannot connect to $SERVER_NAME"
    echo "ERROR: Cannot connect to server"
    exit 1
fi

# Initialize return code
OVERALL_STATUS=0

# Check root filesystem
echo "Checking root filesystem..."
if ! check_disk_usage "/" "$ROOT_THRESHOLD"; then
    OVERALL_STATUS=1
fi

# Check boot filesystem
echo "Checking boot filesystem..."
if ! check_disk_usage "/boot" "$BOOT_THRESHOLD"; then
    OVERALL_STATUS=1
fi

# Check var filesystem
echo "Checking var filesystem..."
if ! check_disk_usage "/var" "$VAR_THRESHOLD"; then
    OVERALL_STATUS=1
fi

# Additional filesystem checks
echo "Checking other mounted filesystems..."
ssh "$SERVER_NAME" "df -h | grep -E '^/dev/' | awk '{print \$6}'" | while read mount_point; do
    if [[ "$mount_point" != "/" && "$mount_point" != "/boot" && "$mount_point" != "/var" ]]; then
        usage=$(ssh "$SERVER_NAME" "df -h $mount_point | tail -1 | awk '{print \$5}' | sed 's/%//'")
        if [ "$usage" -gt 90 ]; then
            log_message "WARNING: $mount_point usage is ${usage}%"
            echo "WARNING: $mount_point usage ${usage}%"
        fi
    fi
done

if [ $OVERALL_STATUS -eq 0 ]; then
    log_message "Disk space check completed successfully"
    echo "All disk space checks passed"
else
    log_message "Disk space check failed - some filesystems exceed thresholds"
    echo "Disk space check failed"
fi

exit $OVERALL_STATUS
