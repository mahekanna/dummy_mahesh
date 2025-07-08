#!/bin/bash

echo "=== FIXING STRING CONCATENATION ERROR ==="
echo

# Copy the fixed templates to production
echo "1. Copying fixed templates to production..."
sudo cp /home/vijji/linux_patching_automation/web_portal/templates/dashboard.html /opt/linux_patching_automation/web_portal/templates/dashboard.html
sudo cp /home/vijji/linux_patching_automation/web_portal/templates/server_detail.html /opt/linux_patching_automation/web_portal/templates/server_detail.html
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/web_portal/templates/dashboard.html
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/web_portal/templates/server_detail.html

echo "2. Restarting web portal..."
sudo systemctl restart patching-portal

echo "3. Waiting for service to start..."
sleep 3

echo "4. Checking service status..."
sudo systemctl status patching-portal --no-pager -l | head -10

echo
echo "✓ String concatenation fix applied!"
echo
echo "Fixed template issues:"
echo "  - current_quarter is now converted to string with |string filter"
echo "  - Dashboard template should load without concatenation errors"
echo "  - Server detail template should work properly"
echo
echo "=== Fix completed ==="