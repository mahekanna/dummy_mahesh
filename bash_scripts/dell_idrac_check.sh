#!/bin/bash

SERVER_NAME="$1"
LOG_FILE="/var/log/patching/dell_check.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $SERVER_NAME - $1" >> "$LOG_FILE"
}

# Function to check if it's Dell hardware
is_dell_hardware() {
    local vendor=$(ssh "$SERVER_NAME" "dmidecode -s system-manufacturer 2>/dev/null | tr '[:upper:]' '[:lower:]'")
    if [[ "$vendor" == *"dell"* ]]; then
        return 0
    else
        return 1
    fi
}

# Function to get iDRAC version
get_idrac_version() {
    ssh "$SERVER_NAME" "racadm getversion -f xml 2>/dev/null | grep -o 'iDRAC[0-9]*' | head -1"
}

# Function to check current boot device
check_boot_device() {
    local idrac_version="$1"
    
    case "$idrac_version" in
        "iDRAC6")
            boot_device=$(ssh "$SERVER_NAME" "racadm config -g cfgServerInfo -o cfgServerFirstBootDevice 2>/dev/null")
            ;;
        "iDRAC7"|"iDRAC8")
            boot_device=$(ssh "$SERVER_NAME" "racadm get BIOS.BiosBootSettings.BootSeq 2>/dev/null")
            ;;
        "iDRAC9")
            boot_device=$(ssh "$SERVER_NAME" "racadm get BIOS.BiosBootSettings.BootSeq 2>/dev/null")
            ;;
        *)
            # Try generic approach
            boot_device=$(ssh "$SERVER_NAME" "racadm get BIOS.BiosBootSettings.BootSeq 2>/dev/null")
            ;;
    esac
    
    echo "$boot_device"
}

# Function to set boot device to disk
set_boot_to_disk() {
    local idrac_version="$1"
    
    case "$idrac_version" in
        "iDRAC6")
            ssh "$SERVER_NAME" "racadm config -g cfgServerInfo -o cfgServerFirstBootDevice HDD"
            ;;
        "iDRAC7"|"iDRAC8")
            # Get the disk boot device identifier
            disk_device=$(ssh "$SERVER_NAME" "racadm get BIOS.BiosBootSettings.BootSeq | grep -i 'disk\\|hdd\\|sata\\|scsi' | head -1 | cut -d'=' -f1")
            if [ -n "$disk_device" ]; then
                ssh "$SERVER_NAME" "racadm set BIOS.BiosBootSettings.BootSeq $disk_device"
            fi
            ;;
        "iDRAC9")
            # For iDRAC9, use newer syntax
            disk_device=$(ssh "$SERVER_NAME" "racadm get BIOS.BiosBootSettings.BootSeq | grep -i 'disk\\|hdd\\|sata\\|nvme' | head -1 | cut -d'=' -f1")
            if [ -n "$disk_device" ]; then
                ssh "$SERVER_NAME" "racadm set BIOS.BiosBootSettings.BootSeq $disk_device"
            fi
            ;;
        *)
            log_message "Unknown iDRAC version: $idrac_version"
            return 1
            ;;
    esac
}

# Function to send alert email
send_alert_email() {
    local message="$1"
    local subject="Dell Hardware Alert: $SERVER_NAME"
    
    # Create temporary email file
    local email_file="/tmp/dell_alert_${SERVER_NAME}_$$.txt"
    
    cat > "$email_file" << EOF
Subject: $subject

Dell Hardware Alert for server: $SERVER_NAME

$message

Time: $(date)
Server: $SERVER_NAME

This is an automated alert from the patching system.
EOF
    
    # Send email (configure your mail system)
    if command -v sendmail >/dev/null 2>&1; then
        sendmail admin@company.com < "$email_file"
    elif command -v mail >/dev/null 2>&1; then
        mail -s "$subject" admin@company.com < "$email_file"
    fi
    
    rm -f "$email_file"
}

# Main execution
# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

log_message "Starting Dell hardware check"

# Check if server is reachable
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_NAME" "echo 'connectivity_test'" >/dev/null 2>&1; then
    log_message "ERROR: Cannot connect to $SERVER_NAME"
    echo "ERROR: Cannot connect to server"
    exit 1
fi

# Check if it's Dell hardware
if ! is_dell_hardware; then
    log_message "INFO: Not Dell hardware, skipping iDRAC checks"
    echo "INFO: Not Dell hardware"
    exit 0
fi

log_message "Dell hardware detected, proceeding with iDRAC checks"

# Check if racadm is available
if ! ssh "$SERVER_NAME" "command -v racadm >/dev/null 2>&1"; then
    log_message "ERROR: racadm command not found on $SERVER_NAME"
    echo "ERROR: racadm not available"
    exit 1
fi

# Get iDRAC version
IDRAC_VERSION=$(get_idrac_version)
if [ -z "$IDRAC_VERSION" ]; then
    log_message "WARNING: Could not determine iDRAC version"
    IDRAC_VERSION="unknown"
fi

log_message "iDRAC version detected: $IDRAC_VERSION"

# Check current boot device
BOOT_DEVICE=$(check_boot_device "$IDRAC_VERSION")

if [ -z "$BOOT_DEVICE" ]; then
    log_message "ERROR: Could not retrieve boot device information"
    echo "ERROR: Cannot determine boot device"
    exit 1
fi

log_message "Current boot device: $BOOT_DEVICE"

# Check if boot device is set to PXE
if echo "$BOOT_DEVICE" | grep -qi "pxe\|network"; then
    log_message "ALERT: Boot device is set to PXE/Network - attempting to change to disk"
    echo "ALERT: Boot device is PXE - changing to disk"
    
    # Send alert email
    send_alert_email "Boot device is currently set to PXE/Network. Attempting to change to disk boot."
    
    # Set boot device to disk
    if set_boot_to_disk "$IDRAC_VERSION"; then
        log_message "SUCCESS: Boot device changed to disk"
        echo "SUCCESS: Boot device changed to disk"
        
        # Create job to apply BIOS changes (iDRAC7+)
        if [[ "$IDRAC_VERSION" != "iDRAC6" ]]; then
            ssh "$SERVER_NAME" "racadm jobqueue create BIOS.Setup.1-1 -r pwrcycle -s TIME_NOW" 2>/dev/null
            log_message "BIOS configuration job created"
        fi
    else
        log_message "ERROR: Failed to change boot device to disk"
        echo "ERROR: Failed to change boot device"
        send_alert_email "FAILED to change boot device from PXE to disk. Manual intervention required."
        exit 1
    fi
else
    log_message "OK: Boot device is not set to PXE"
    echo "OK: Boot device is not PXE"
fi

log_message "Dell hardware check completed successfully"
echo "Dell hardware check passed"
exit 0
