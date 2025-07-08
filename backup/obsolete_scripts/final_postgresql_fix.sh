#!/bin/bash

echo "=== FINAL POSTGRESQL COMPATIBILITY FIX ==="
echo

# Step 1: Copy the fixed database models file
echo "1. Updating database models for PostgreSQL compatibility..."
sudo cp /home/vijji/linux_patching_automation/database/models.py /opt/linux_patching_automation/database/models.py
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/database/models.py

# Step 2: Fix the configuration file to have individual DB attributes
echo "2. Fixing configuration file for PostgreSQL..."
CONFIG_FILE="/opt/linux_patching_automation/config/settings.py"

# Remove any DATABASE_CONFIG dictionary if it exists
sudo sed -i '/DATABASE_CONFIG = {/,/}/d' "$CONFIG_FILE"

# Add individual database attributes if they don't exist
if ! sudo grep -q "DB_HOST" "$CONFIG_FILE"; then
    echo "Adding missing database configuration attributes..."
    
    # Add the missing DB attributes after USE_SQLITE line
    sudo sed -i '/USE_SQLITE = /a\
\
    # Database connection parameters\
    DB_HOST = "localhost"\
    DB_PORT = "5432"\
    DB_NAME = "patching_db"\
    DB_USER = "patch_admin"\
    DB_PASSWORD = "secure_password"' "$CONFIG_FILE"
fi

# Step 3: Fix boolean syntax
echo "3. Fixing boolean syntax..."
sudo sed -i 's/USE_SQLITE = false/USE_SQLITE = False/g' "$CONFIG_FILE"
sudo sed -i 's/USE_SQLITE = true/USE_SQLITE = True/g' "$CONFIG_FILE"

# Step 4: Test configuration
echo "4. Testing configuration..."
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/linux_patching_automation')
try:
    from config.settings import Config
    print('✓ Configuration loaded successfully')
    print(f'  USE_SQLITE: {getattr(Config, \"USE_SQLITE\", \"Not found\")}')
    if not getattr(Config, 'USE_SQLITE', True):
        print(f'  DB_HOST: {getattr(Config, \"DB_HOST\", \"Not found\")}')
        print(f'  DB_PORT: {getattr(Config, \"DB_PORT\", \"Not found\")}')
        print(f'  DB_NAME: {getattr(Config, \"DB_NAME\", \"Not found\")}')
        print(f'  DB_USER: {getattr(Config, \"DB_USER\", \"Not found\")}')
    print('✓ All database attributes are available')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo
    echo "5. Initializing PostgreSQL database..."
    
    # Make sure PostgreSQL service is running
    sudo systemctl start postgresql
    
    # Initialize database
    sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/main.py --init-db
    
    if [ $? -eq 0 ]; then
        echo
        echo "🎉 SUCCESS! PostgreSQL database initialized successfully!"
        echo
        echo "Starting services..."
        sudo systemctl start patching-portal patching-monitor
        sudo systemctl enable patching-portal patching-monitor
        
        echo
        echo "✅ All services started successfully!"
        echo
        echo "You can now access the web portal at: http://$(hostname -f):5001"
        echo "Default login: admin / admin"
        echo
        echo "Check service status with:"
        echo "  systemctl status patching-portal"
        echo "  systemctl status patching-monitor"
        
    else
        echo "❌ Database initialization failed"
        echo "Check PostgreSQL service and database credentials"
        echo
        echo "You might want to:"
        echo "1. Check if PostgreSQL is running: systemctl status postgresql"
        echo "2. Verify database exists: sudo -u postgres psql -l"
        echo "3. Check database user permissions"
    fi
else
    echo "❌ Configuration test failed"
fi

echo
echo "=== Fix completed ==="