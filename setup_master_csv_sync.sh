#!/bin/bash

echo "=== SETTING UP MASTER CSV SYNC ==="
echo

# Configuration (UPDATE THESE VALUES)
MASTER_SERVER="master-db-server.example.com"
MASTER_CSV_PATH="/exports/database/reports/server_inventory.csv"
MASTER_USER="sync_user"
LOCAL_CSV_PATH="/opt/linux_patching_automation/data/servers.csv"
BACKUP_DIR="/opt/linux_patching_automation/data/backups"
LOG_FILE="/opt/linux_patching_automation/logs/csv_sync.log"

echo "Master CSV Sync Configuration:"
echo "  Remote Server: $MASTER_USER@$MASTER_SERVER"
echo "  Remote CSV Path: $MASTER_CSV_PATH"
echo "  Local CSV Path: $LOCAL_CSV_PATH"
echo "  Backup Directory: $BACKUP_DIR"
echo

# Create necessary directories
echo "1. Creating directories..."
sudo mkdir -p "$BACKUP_DIR"
sudo mkdir -p "$(dirname $LOG_FILE)"
sudo chown -R patchadmin:patchadmin "$BACKUP_DIR"
sudo chown -R patchadmin:patchadmin "$(dirname $LOG_FILE)"

# Create the sync script
echo "2. Creating CSV sync script..."
sudo tee /opt/linux_patching_automation/scripts/sync_master_csv.sh << 'EOF'
#!/bin/bash

# Configuration
MASTER_SERVER="master-db-server.example.com"
MASTER_CSV_PATH="/exports/database/reports/server_inventory.csv"
MASTER_USER="sync_user"
LOCAL_CSV_PATH="/opt/linux_patching_automation/data/servers.csv"
BACKUP_DIR="/opt/linux_patching_automation/data/backups"
LOG_FILE="/opt/linux_patching_automation/logs/csv_sync.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "=== Starting Master CSV Sync ==="

# Create backup of current CSV if it exists
if [ -f "$LOCAL_CSV_PATH" ]; then
    BACKUP_FILE="$BACKUP_DIR/servers_backup_$(date +%Y%m%d_%H%M%S).csv"
    log_message "Creating backup: $BACKUP_FILE"
    cp "$LOCAL_CSV_PATH" "$BACKUP_FILE"
    
    # Keep only last 7 days of backups
    find "$BACKUP_DIR" -name "servers_backup_*.csv" -mtime +7 -delete 2>/dev/null
fi

# Sync CSV from master server
log_message "Syncing CSV from $MASTER_USER@$MASTER_SERVER:$MASTER_CSV_PATH"

# Use rsync to fetch the master CSV
rsync -avz --timeout=30 "$MASTER_USER@$MASTER_SERVER:$MASTER_CSV_PATH" "$LOCAL_CSV_PATH.tmp" 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    # Verify the downloaded file
    if [ -s "$LOCAL_CSV_PATH.tmp" ]; then
        # Check if it has the expected header
        HEADER=$(head -1 "$LOCAL_CSV_PATH.tmp")
        if [[ "$HEADER" == *"Server Name"* ]]; then
            log_message "CSV sync successful - replacing local file"
            mv "$LOCAL_CSV_PATH.tmp" "$LOCAL_CSV_PATH"
            chown patchadmin:patchadmin "$LOCAL_CSV_PATH"
            
            # Trigger database sync
            log_message "Triggering database sync..."
            sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/linux_patching_automation')
from scripts.admin_manager import AdminManager
admin = AdminManager()
result = admin.sync_csv_to_database()
print('Database sync completed:', result)
" 2>&1 | tee -a "$LOG_FILE"
            
            log_message "=== Master CSV Sync Completed Successfully ==="
        else
            log_message "ERROR: Downloaded file doesn't contain expected header"
            rm -f "$LOCAL_CSV_PATH.tmp"
            exit 1
        fi
    else
        log_message "ERROR: Downloaded file is empty"
        rm -f "$LOCAL_CSV_PATH.tmp"
        exit 1
    fi
else
    log_message "ERROR: rsync failed"
    rm -f "$LOCAL_CSV_PATH.tmp"
    exit 1
fi
EOF

sudo chmod +x /opt/linux_patching_automation/scripts/sync_master_csv.sh
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/scripts/sync_master_csv.sh

# Create SSH key for passwordless sync (if not exists)
echo "3. Setting up SSH key for passwordless sync..."
if [ ! -f /home/patchadmin/.ssh/id_rsa ]; then
    sudo -u patchadmin ssh-keygen -t rsa -b 2048 -f /home/patchadmin/.ssh/id_rsa -N ""
    echo
    echo "IMPORTANT: Copy this public key to $MASTER_USER@$MASTER_SERVER:"
    echo "----------------------------------------"
    sudo cat /home/patchadmin/.ssh/id_rsa.pub
    echo "----------------------------------------"
    echo
    echo "Add it to: $MASTER_USER@$MASTER_SERVER:~/.ssh/authorized_keys"
    echo
fi

# Add cron job for hourly sync
echo "4. Setting up cron job for hourly CSV sync..."
CRON_JOB="0 * * * * /opt/linux_patching_automation/scripts/sync_master_csv.sh >/dev/null 2>&1"

# Check if cron job already exists
if ! sudo crontab -u patchadmin -l 2>/dev/null | grep -q "sync_master_csv.sh"; then
    # Add the cron job
    (sudo crontab -u patchadmin -l 2>/dev/null; echo "$CRON_JOB") | sudo crontab -u patchadmin -
    echo "Cron job added: Hourly CSV sync at minute 0"
else
    echo "Cron job already exists"
fi

# Test the sync script
echo "5. Testing CSV sync (dry run)..."
echo "Manual test command:"
echo "  sudo -u patchadmin /opt/linux_patching_automation/scripts/sync_master_csv.sh"
echo

echo "=== CSV Sync Setup Completed ==="
echo
echo "NEXT STEPS:"
echo "1. Update the configuration in /opt/linux_patching_automation/scripts/sync_master_csv.sh:"
echo "   - MASTER_SERVER: Your actual server hostname/IP"
echo "   - MASTER_CSV_PATH: Your actual CSV file path"
echo "   - MASTER_USER: Your actual username"
echo
echo "2. Set up SSH key authentication:"
echo "   - Copy the public key shown above to the master server"
echo "   - Test: ssh $MASTER_USER@$MASTER_SERVER"
echo
echo "3. Test the sync manually:"
echo "   sudo -u patchadmin /opt/linux_patching_automation/scripts/sync_master_csv.sh"
echo
echo "4. Monitor logs:"
echo "   tail -f /opt/linux_patching_automation/logs/csv_sync.log"