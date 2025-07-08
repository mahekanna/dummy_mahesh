#!/bin/bash

echo "=== FIXING DASHBOARD TEMPLATE ERROR ==="
echo

# Copy the fixed web app to production
echo "1. Copying fixed dashboard to production..."
sudo cp /home/vijji/linux_patching_automation/web_portal/app.py /opt/linux_patching_automation/web_portal/app.py
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/web_portal/app.py

echo "2. Restarting web portal..."
sudo systemctl restart patching-portal

echo "3. Waiting for service to start..."
sleep 3

echo "4. Checking service status..."
sudo systemctl status patching-portal --no-pager -l | head -15

echo
echo "✓ Dashboard template fix applied!"
echo
echo "The dashboard should now load without 'quarters' undefined error."
echo
echo "=== Fix completed ==="