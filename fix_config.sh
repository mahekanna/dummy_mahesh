#!/bin/bash

# Quick fix script for Python boolean syntax errors in settings.py

CONFIG_FILE="/opt/linux_patching_automation/config/settings.py"

echo "Fixing Python boolean syntax and attribute names in $CONFIG_FILE..."

# Fix boolean values
sudo sed -i 's/LDAP_ENABLED = false/LDAP_ENABLED = False/g' "$CONFIG_FILE"
sudo sed -i 's/LDAP_ENABLED = true/LDAP_ENABLED = True/g' "$CONFIG_FILE"
sudo sed -i 's/USE_SENDMAIL = false/USE_SENDMAIL = False/g' "$CONFIG_FILE"
sudo sed -i 's/USE_SENDMAIL = true/USE_SENDMAIL = True/g' "$CONFIG_FILE"
sudo sed -i 's/SMTP_USE_TLS = false/SMTP_USE_TLS = False/g' "$CONFIG_FILE"
sudo sed -i 's/SMTP_USE_TLS = true/SMTP_USE_TLS = True/g' "$CONFIG_FILE"
sudo sed -i 's/USE_SQLITE = false/USE_SQLITE = False/g' "$CONFIG_FILE"
sudo sed -i 's/USE_SQLITE = true/USE_SQLITE = True/g' "$CONFIG_FILE"

# Fix attribute names to match what the code expects
sudo sed -i 's/LOGS_DIR =/LOG_DIR =/g' "$CONFIG_FILE"

# Add missing attributes that the original config has
echo "Adding missing configuration attributes..."

# Check if CSV_FILE_PATH exists, if not add it
if ! grep -q "CSV_FILE_PATH" "$CONFIG_FILE"; then
    sudo sed -i '/DATA_DIR = /a\    CSV_FILE_PATH = os.path.join(DATA_DIR, '\''servers.csv'\'')' "$CONFIG_FILE"
fi

# Check if PROJECT_ROOT and CONFIG_DIR exist, if not add them  
if ! grep -q "PROJECT_ROOT" "$CONFIG_FILE"; then
    sudo sed -i '/# Base Paths/a\    PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))' "$CONFIG_FILE"
fi

if ! grep -q "CONFIG_DIR" "$CONFIG_FILE"; then
    sudo sed -i '/PROJECT_ROOT = /a\    CONFIG_DIR = os.path.join(PROJECT_ROOT, '\''config'\'')' "$CONFIG_FILE"
fi

# Add missing QUARTERS definition and static method at the end of Config class
if ! grep -q "get_current_quarter" "$CONFIG_FILE"; then
    echo "Adding missing QUARTERS definition and static method..."
    
    # Find the line number just before the last closing of the class (before EOF)
    sudo sed -i '/^EOF$/i\
\
    # Disk Space Thresholds (in percentage)\
    DISK_THRESHOLD_ROOT = 80\
    DISK_THRESHOLD_BOOT = 70\
    DISK_THRESHOLD_VAR = 85\
\
    # Timing Configuration\
    PRECHECK_HOURS_BEFORE = 5\
    SCHEDULE_HOURS_BEFORE = 3\
    POST_PATCH_WAIT_MINUTES = 10\
\
    # Custom Quarters Definition (Q1: Nov-Jan, Q2: Feb-Apr, Q3: May-Jul, Q4: Aug-Oct)\
    QUARTERS = {\
        '\''1'\'': {'\''name'\'': '\''Q1'\'', '\''months'\'': [11, 12, 1]},   # Nov to Jan\
        '\''2'\'': {'\''name'\'': '\''Q2'\'', '\''months'\'': [2, 3, 4]},     # Feb to April\
        '\''3'\'': {'\''name'\'': '\''Q3'\'', '\''months'\'': [5, 6, 7]},     # May to July\
        '\''4'\'': {'\''name'\'': '\''Q4'\'', '\''months'\'': [8, 9, 10]}     # August to October\
    }\
\
    @staticmethod\
    def get_current_quarter():\
        """Get current quarter based on custom quarter definition"""\
        from datetime import datetime\
        current_month = datetime.now().month\
        for quarter, details in Config.QUARTERS.items():\
            if current_month in details['\''months'\'']:\
                return quarter\
        return '\''1'\''  # Default to Q1 if something goes wrong' "$CONFIG_FILE"
fi

echo "Verifying Python syntax..."
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/linux_patching_automation')
try:
    from config.settings import Config
    print('SUCCESS: Configuration file syntax is correct')
    print(f'USE_SENDMAIL: {Config.USE_SENDMAIL}')
    print(f'LDAP_ENABLED: {Config.LDAP_ENABLED}')
    print(f'USE_SQLITE: {Config.USE_SQLITE}')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "Configuration fix completed successfully!"
    echo "Now trying to initialize database..."
    sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/main.py --init-db
else
    echo "Configuration fix failed. Please check the settings manually."
fi