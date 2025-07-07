#!/bin/bash

echo "Quick PostgreSQL syntax fix for INSERT OR IGNORE..."

# Copy the fixed database models file
sudo cp /home/vijji/linux_patching_automation/database/models.py /opt/linux_patching_automation/database/models.py
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/database/models.py

echo "Testing database initialization..."
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/main.py --init-db

if [ $? -eq 0 ]; then
    echo "SUCCESS: Database initialized!"
    echo "Starting services..."
    sudo systemctl start patching-portal patching-monitor
    sudo systemctl enable patching-portal patching-monitor
    echo "Services started successfully!"
else
    echo "Database initialization failed"
fi