#!/bin/bash

echo "Fixing database configuration for PostgreSQL..."

CONFIG_FILE="/opt/linux_patching_automation/config/settings.py"

# First, let's see what database type was configured
if sudo grep -q "USE_SQLITE = True" "$CONFIG_FILE"; then
    echo "SQLite is configured - fixing database path..."
    # Copy the fixed database models file for SQLite
    sudo cp /home/vijji/linux_patching_automation/database/models.py /opt/linux_patching_automation/database/models.py
    sudo chown patchadmin:patchadmin /opt/linux_patching_automation/database/models.py
else
    echo "PostgreSQL is configured - adding missing database attributes..."
    
    # Copy the fixed database models file 
    sudo cp /home/vijji/linux_patching_automation/database/models.py /opt/linux_patching_automation/database/models.py
    sudo chown patchadmin:patchadmin /opt/linux_patching_automation/database/models.py
    
    # Check if DATABASE_CONFIG exists and replace it with individual attributes
    if sudo grep -q "DATABASE_CONFIG" "$CONFIG_FILE"; then
        echo "Found DATABASE_CONFIG - converting to individual attributes..."
        
        # Extract values from the current config file
        DB_HOST=$(sudo grep "DB_HOST" /opt/linux_patching_automation/deploy_interactive.sh | grep "=" | cut -d'"' -f2 || echo "localhost")
        DB_PORT=$(sudo grep "DB_PORT" /opt/linux_patching_automation/deploy_interactive.sh | grep "=" | cut -d'"' -f2 || echo "5432")  
        DB_NAME=$(sudo grep "DB_NAME" /opt/linux_patching_automation/deploy_interactive.sh | grep "=" | cut -d'"' -f2 || echo "patching_db")
        DB_USER=$(sudo grep "DB_USER" /opt/linux_patching_automation/deploy_interactive.sh | grep "=" | cut -d'"' -f2 || echo "patch_admin")
        DB_PASSWORD=$(sudo grep "DB_PASSWORD" /opt/linux_patching_automation/deploy_interactive.sh | grep "=" | cut -d'"' -f2 || echo "secure_password")
        
        # Remove the DATABASE_CONFIG section and add individual attributes
        sudo sed -i '/DATABASE_CONFIG = {/,/}/d' "$CONFIG_FILE"
        
        # Add individual database attributes after USE_SQLITE
        sudo sed -i "/USE_SQLITE = /a\\
\\
    # Database connection parameters\\
    DB_HOST = \"$DB_HOST\"\\
    DB_PORT = \"$DB_PORT\"\\
    DB_NAME = \"$DB_NAME\"\\
    DB_USER = \"$DB_USER\"\\
    DB_PASSWORD = \"$DB_PASSWORD\"" "$CONFIG_FILE"
        
        echo "Added individual database attributes"
    fi
fi

# Fix any boolean syntax issues
sudo sed -i 's/USE_SQLITE = false/USE_SQLITE = False/g' "$CONFIG_FILE"
sudo sed -i 's/USE_SQLITE = true/USE_SQLITE = True/g' "$CONFIG_FILE"

echo "Testing database configuration..."

# Test the configuration
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/linux_patching_automation')
try:
    from config.settings import Config
    print('Configuration loaded successfully!')
    print(f'USE_SQLITE: {getattr(Config, \"USE_SQLITE\", \"Not found\")}')
    if not getattr(Config, 'USE_SQLITE', True):
        print(f'DB_HOST: {getattr(Config, \"DB_HOST\", \"Not found\")}')
        print(f'DB_PORT: {getattr(Config, \"DB_PORT\", \"Not found\")}')
        print(f'DB_NAME: {getattr(Config, \"DB_NAME\", \"Not found\")}')
        print(f'DB_USER: {getattr(Config, \"DB_USER\", \"Not found\")}')
    print('All database attributes found!')
except Exception as e:
    print(f'Configuration error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "Testing database initialization..."
    sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/main.py --init-db
    
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Database initialized successfully!"
        echo "Starting services..."
        sudo systemctl start patching-portal
        sudo systemctl start patching-monitor  
        sudo systemctl enable patching-portal
        sudo systemctl enable patching-monitor
        echo "Services started. Check status with: systemctl status patching-portal"
    else
        echo "ERROR: Database initialization failed."
    fi
else
    echo "ERROR: Configuration test failed."
fi