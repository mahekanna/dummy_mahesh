#!/bin/bash

echo "=== Linux Patching System Diagnostic Tool ==="
echo "============================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check status
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        echo "  Error details: $3"
    fi
}

# 1. Check Python version
echo "1. Checking Python version..."
python3 --version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc) -eq 1 ]]; then
    check_status 0 "Python version $PYTHON_VERSION is compatible"
else
    check_status 1 "Python version $PYTHON_VERSION is too old (need 3.8+)"
fi
echo

# 2. Check if virtual environment exists
echo "2. Checking virtual environment..."
if [ -d "/opt/linux_patching_automation/venv" ]; then
    check_status 0 "Virtual environment exists"
else
    check_status 1 "Virtual environment missing" "Run: cd /opt/linux_patching_automation && python3 -m venv venv"
fi
echo

# 3. Check required Python packages
echo "3. Checking Python packages..."
if [ -d "/opt/linux_patching_automation/venv" ]; then
    MISSING_PACKAGES=""
    for package in flask flask-login psycopg2-binary paramiko; do
        if ! /opt/linux_patching_automation/venv/bin/pip show $package >/dev/null 2>&1; then
            MISSING_PACKAGES="$MISSING_PACKAGES $package"
        fi
    done
    
    if [ -z "$MISSING_PACKAGES" ]; then
        check_status 0 "All required packages installed"
    else
        check_status 1 "Missing packages:$MISSING_PACKAGES" "Run: sudo -u patchadmin /opt/linux_patching_automation/venv/bin/pip install -r requirements.txt"
    fi
else
    echo -e "${YELLOW}⚠${NC} Cannot check packages - venv missing"
fi
echo

# 4. Check database configuration
echo "4. Checking database configuration..."
if [ -f "/opt/linux_patching_automation/config/settings.py" ]; then
    if grep -q "CHANGE_ME_IN_PRODUCTION" /opt/linux_patching_automation/config/settings.py; then
        check_status 1 "Database credentials not configured" "Edit /opt/linux_patching_automation/config/settings.py"
    else
        check_status 0 "Database credentials configured"
    fi
else
    check_status 1 "settings.py missing"
fi
echo

# 5. Check services
echo "5. Checking services..."
for service in patching-portal patching-monitor; do
    if systemctl is-active --quiet $service; then
        check_status 0 "$service is running"
    else
        check_status 1 "$service is not running" "Run: sudo systemctl start $service"
        # Show recent logs
        echo "  Recent logs:"
        sudo journalctl -u $service -n 5 --no-pager | sed 's/^/    /'
    fi
done
echo

# 6. Check web portal accessibility
echo "6. Checking web portal..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 | grep -q "200\|302"; then
    check_status 0 "Web portal is responding"
    echo "  Access URL: http://$(hostname -I | awk '{print $1}'):5001"
else
    check_status 1 "Web portal not responding" "Check logs: sudo journalctl -u patching-portal -f"
fi
echo

# 7. Check file permissions
echo "7. Checking file permissions..."
PERM_ISSUES=""
for dir in config data logs web_portal; do
    if [ -d "/opt/linux_patching_automation/$dir" ]; then
        OWNER=$(stat -c %U:%G "/opt/linux_patching_automation/$dir")
        if [ "$OWNER" != "patchadmin:patchadmin" ]; then
            PERM_ISSUES="$PERM_ISSUES $dir($OWNER)"
        fi
    fi
done

if [ -z "$PERM_ISSUES" ]; then
    check_status 0 "File permissions correct"
else
    check_status 1 "Permission issues:$PERM_ISSUES" "Run: sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation"
fi
echo

# 8. Check for common template issues
echo "8. Checking templates..."
TEMPLATE_DIR="/opt/linux_patching_automation/web_portal/templates"
if [ -d "$TEMPLATE_DIR" ]; then
    TEMPLATE_COUNT=$(find $TEMPLATE_DIR -name "*.html" | wc -l)
    if [ $TEMPLATE_COUNT -gt 0 ]; then
        check_status 0 "Found $TEMPLATE_COUNT templates"
    else
        check_status 1 "No templates found"
    fi
else
    check_status 1 "Templates directory missing"
fi
echo

# 9. Database connectivity test
echo "9. Testing database connection..."
if [ -f "/opt/linux_patching_automation/main.py" ]; then
    sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "
import sys
sys.path.insert(0, '/opt/linux_patching_automation')
try:
    from database.models import DatabaseManager
    db = DatabaseManager()
    conn = db.connect()
    db.close()
    print('Database connection successful')
    exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>&1
    check_status $? "Database connection test"
else
    check_status 1 "main.py not found"
fi
echo

# Summary
echo "=== DIAGNOSTIC SUMMARY ==="
echo "If you see any ✗ marks above, fix those issues first."
echo
echo "Quick fix commands:"
echo "1. Install dependencies: cd /opt/linux_patching_automation && sudo -u patchadmin ./venv/bin/pip install -r requirements.txt"
echo "2. Fix permissions: sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation"
echo "3. Initialize database: sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/main.py --init-db"
echo "4. Restart services: sudo systemctl restart patching-portal patching-monitor"
echo
echo "For detailed logs: sudo journalctl -u patching-portal -f"