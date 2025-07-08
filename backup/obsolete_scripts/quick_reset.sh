#!/bin/bash

echo "=== Quick Reset for Linux Patching System ==="
echo

# 1. Ensure we're in the right directory
if [ -d "/opt/linux_patching_automation" ]; then
    cd /opt/linux_patching_automation
else
    echo "ERROR: /opt/linux_patching_automation not found"
    echo "Run deployment script first: sudo ./deploy_interactive.sh"
    exit 1
fi

# 2. Fix permissions
echo "Fixing permissions..."
sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation

# 3. Reinstall dependencies
echo "Installing dependencies..."
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/pip install -r requirements.txt

# 4. Reset to default test credentials
echo "Setting test credentials..."
sudo tee /opt/linux_patching_automation/config/test_users.py << 'EOF'
# TEMPORARY TEST CONFIGURATION - REPLACE IN PRODUCTION
import os

class UserManager:
    ROLES = {
        'admin': {
            'name': 'Administrator',
            'permissions': ['view_all_servers', 'modify_all_schedules', 'approve_all_schedules', 
                          'update_incident_tickets', 'update_patcher_emails', 'manage_users', 
                          'send_notifications', 'export_data', 'system_admin']
        }
    }
    
    USERS = {
        'admin': {  # Simple test user
            'password': 'admin',
            'role': 'admin',
            'name': 'Test Admin',
            'active': True
        }
    }
    
    @classmethod
    def authenticate_user(cls, email, password):
        # For testing - accept 'admin' as both username and password
        if email == 'admin' and password == 'admin':
            return {
                'email': 'admin',
                'role': 'admin',
                'name': 'Test Admin',
                'permissions': cls.ROLES['admin']['permissions']
            }
        return None
    
    # Add compatibility for old method name
    authenticate = authenticate_user
EOF

# Backup original and use test config
sudo mv /opt/linux_patching_automation/config/users.py /opt/linux_patching_automation/config/users.py.bak
sudo mv /opt/linux_patching_automation/config/test_users.py /opt/linux_patching_automation/config/users.py
sudo chown patchadmin:patchadmin /opt/linux_patching_automation/config/users.py

# 5. Initialize database
echo "Initializing database..."
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/main.py --init-db

# 6. Restart services
echo "Restarting services..."
sudo systemctl restart patching-portal patching-monitor

# 7. Wait and check
sleep 5
echo
echo "=== Service Status ==="
sudo systemctl status patching-portal --no-pager | grep Active
sudo systemctl status patching-monitor --no-pager | grep Active

echo
echo "=== QUICK RESET COMPLETE ==="
echo
echo "Test login credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo
echo "Access URL: http://$(hostname -I | awk '{print $1}'):5001"
echo
echo "If still having issues, check logs:"
echo "  sudo journalctl -u patching-portal -f"