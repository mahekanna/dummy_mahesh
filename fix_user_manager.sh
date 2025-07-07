#!/bin/bash

echo "=== FIXING USER MANAGER AUTHENTICATION ==="
echo

# Copy the correct users.py file to production
echo "1. Copying correct UserManager to production..."
sudo cp /home/vijji/linux_patching_automation/config/users.py /opt/linux_patching_automation/config/users.py
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/config/users.py

# Verify the method exists in production
echo "2. Verifying UserManager in production..."
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/linux_patching_automation')
from config.users import UserManager

print('Available methods:', [m for m in dir(UserManager) if not m.startswith('_')])

if hasattr(UserManager, 'authenticate_user'):
    print('✓ authenticate_user method exists')
    result = UserManager.authenticate_user('admin@company.com', 'admin123')
    if result:
        print('✓ Authentication test successful')
    else:
        print('✗ Authentication failed')
else:
    print('✗ authenticate_user method NOT found')
"

if [ $? -eq 0 ]; then
    echo
    echo "3. Restarting web portal..."
    sudo systemctl restart patching-portal
    
    echo
    echo "✓ Fix completed successfully!"
    echo
    echo "Try logging in with:"
    echo "  Email: admin@company.com"
    echo "  Password: admin123"
else
    echo "✗ UserManager verification failed"
fi

echo
echo "=== Fix completed ==="