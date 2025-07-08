#!/bin/bash

echo "Applying simple fix for database path issue..."

# Copy the corrected database models file
sudo cp /home/vijji/linux_patching_automation/database/models.py /opt/linux_patching_automation/database/models.py

# Set proper ownership
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/database/models.py

echo "Testing database initialization..."

# Try to initialize the database
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
    echo "ERROR: Database initialization failed. Check the output above."
fi