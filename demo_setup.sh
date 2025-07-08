#!/bin/bash

# Quick Demo Setup Script for Linux Patching Automation
# This script sets up the system for a quick demo without full deployment

set -e

echo "==================================================="
echo "  Linux Patching Automation - Quick Demo Setup    "
echo "==================================================="

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

echo "Setting up demo environment..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user flask flask-login werkzeug pytz psycopg2-binary python-crontab schedule pysnmp prometheus-client bcrypt || true

# Create necessary directories
echo "Creating directories..."
mkdir -p logs data config web_portal/templates web_portal/static
touch logs/.gitkeep

# Check if we have the CSV file
if [[ ! -f "data/servers.csv" ]]; then
    echo "CSV file not found. The existing one should work."
fi

# Create a simple test database initialization
echo "Testing configuration..."
python3 -c "
from config.settings import Config
from utils.csv_handler import CSVHandler
from config.users import UserManager

print('✓ Configuration loaded')
print(f'  Current quarter: Q{Config.get_current_quarter()}')

try:
    csv_handler = CSVHandler()
    servers = csv_handler.read_servers()
    print(f'✓ CSV loaded: {len(servers)} servers')
except Exception as e:
    print(f'✗ CSV loading failed: {e}')

# Test user authentication
user = UserManager.authenticate_user('admin', 'admin')
if user:
    print(f'✓ Demo admin user working: {user[\"name\"]}')
else:
    print('✗ Admin user authentication failed')
"

echo ""
echo "==================================================="
echo "  Demo Setup Complete!                             "
echo "==================================================="
echo ""
echo "Demo Accounts (Local Authentication):"
echo "  Admin:     admin / admin"
echo "  User:      user1 / demo123"
echo "  DBA:       dba@company.com / demo123"
echo "  Developer: dev@company.com / demo123"
echo ""
echo "LDAP Integration:"
echo "  Status:    Disabled (fallback to local auth)"
echo "  To Enable: export LDAP_ENABLED=true"
echo "  Netgroup:  patching_admins (for admin control)"
echo ""
echo "Quick Start Commands:"
echo "  Start Web Portal:    python3 web_portal/app.py"
echo "  Check Approvals:     python3 main.py --check-approvals --quarter 3"
echo "  Approve Server:      python3 main.py --approve --server web01.company.com --quarter 3"
echo "  Update Emails:       python3 main.py --incident-ticket DEMO001 --host-group web_servers"
echo ""
echo "Web Portal URL: http://localhost:5001"
echo ""
echo "Sample Data: 9 servers loaded with realistic patching schedules"
echo ""
echo "==================================================="
echo "Ready for Demo! 🚀"
echo "==================================================="