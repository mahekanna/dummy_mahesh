#!/bin/bash

echo "=== FIXING LOGIN COMPATIBILITY ==="
echo

# Copy the fixed web app to production
echo "1. Copying fixed web app to production..."
sudo cp /home/vijji/linux_patching_automation/web_portal/app.py /opt/linux_patching_automation/web_portal/app.py
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/web_portal/app.py

# Also copy the correct users.py just in case
echo "2. Copying correct UserManager to production..."
sudo cp /home/vijji/linux_patching_automation/config/users.py /opt/linux_patching_automation/config/users.py
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/config/users.py

echo "3. Restarting web portal..."
sudo systemctl restart patching-portal

echo "4. Checking service status..."
sleep 3
sudo systemctl status patching-portal --no-pager -l

echo
echo "✓ Login compatibility fix applied!"
echo
echo "The web app now works with both method names:"
echo "  - authenticate_user (new/correct)"
echo "  - authenticate (old/fallback)"
echo
echo "Try logging in with:"
echo "  Email: admin@company.com"
echo "  Password: admin123"
echo
echo "=== Fix completed ==="