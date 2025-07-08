#!/bin/bash

echo "=== FOOLPROOF SETUP FOR LINUX PATCHING SYSTEM ==="
echo "This script will fix ALL issues and get the system running"
echo "========================================================"
echo

# Exit on any error
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print status
status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 1. Detect where we are
if [ -d "./web_portal" ] && [ -f "./requirements.txt" ]; then
    PROJECT_DIR=$(pwd)
    status "Found project in: $PROJECT_DIR"
else
    echo "ERROR: Run this script from the project root directory"
    echo "Example: cd /home/user/dharma_mahesh && ./foolproof_setup.sh"
    exit 1
fi

# 2. Install system dependencies
status "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y python3-pip python3-venv python3-dev postgresql postgresql-contrib libpq-dev

# 3. Create simple SQLite-based development setup
status "Creating development environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create simplified configuration
status "Creating simplified configuration..."

# Create a working config with SQLite
cat > config/dev_settings.py << 'EOF'
import os

class Config:
    # Use SQLite for simplicity
    USE_SQLITE = True
    DB_NAME = 'patching.db'
    
    # Simple email config
    USE_SENDMAIL = True
    
    # Basic paths
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    CSV_FILE_PATH = os.path.join(DATA_DIR, 'servers.csv')
    LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
    LOGS_DIR = LOG_DIR  # Alias
    TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates')
    
    # Create directories
    for dir_path in [DATA_DIR, LOG_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Quarters
    QUARTERS = {
        '1': {'name': 'Q1', 'months': [11, 12, 1]},
        '2': {'name': 'Q2', 'months': [2, 3, 4]},
        '3': {'name': 'Q3', 'months': [5, 6, 7]},
        '4': {'name': 'Q4', 'months': [8, 9, 10]}
    }
    
    # Other settings
    PRECHECK_HOURS_BEFORE = 24
    
    @staticmethod
    def get_current_quarter():
        from datetime import datetime
        month = datetime.now().month
        for q, data in Config.QUARTERS.items():
            if month in data['months']:
                return q
        return '1'
EOF

# 5. Create simple user config
cat > config/simple_users.py << 'EOF'
class UserManager:
    ROLES = {
        'admin': {
            'name': 'Administrator',
            'permissions': ['all']
        }
    }
    
    @classmethod
    def authenticate_user(cls, email, password):
        if email == 'admin' and password == 'admin':
            return {
                'email': 'admin',
                'role': 'admin',
                'name': 'Administrator',
                'permissions': ['all']
            }
        return None
    
    authenticate = authenticate_user  # Compatibility
EOF

# 6. Fix imports to use development settings
status "Configuring for development mode..."

# Backup original files
cp config/settings.py config/settings.py.original 2>/dev/null || true
cp config/users.py config/users.py.original 2>/dev/null || true

# Use development configs
cp config/dev_settings.py config/settings.py
cp config/simple_users.py config/users.py

# 7. Create sample data
status "Creating sample data..."
mkdir -p data
cat > data/servers.csv << 'EOF'
Server Name,primary_owner,secondary_owner,host_group,engr_domain,location,Server Timezone,Q1 Patch Date,Q1 Patch Time,Q2 Patch Date,Q2 Patch Time,Q3 Patch Date,Q3 Patch Time,Q4 Patch Date,Q4 Patch Time,Current Quarter Patching Status
test-server-01,admin@example.com,backup@example.com,web-servers,IT,datacenter1,EST,2025-11-14,20:00,2025-02-13,20:00,2025-05-15,20:00,2025-08-14,20:00,Pending
test-server-02,admin@example.com,backup@example.com,db-servers,Database,datacenter1,PST,2025-11-21,21:00,2025-02-20,21:00,2025-05-22,21:00,2025-08-21,21:00,Pending
EOF

# 8. Initialize database
status "Initializing database..."
python main.py --init-db || {
    warning "Database init failed, creating manually..."
    python -c "
from database.models import DatabaseManager
db = DatabaseManager(use_sqlite=True)
conn = db.connect()
db.create_tables()
db.close()
print('Database created successfully')
"
}

# 9. Create run script
status "Creating run script..."
cat > run_dev.sh << 'EOF'
#!/bin/bash
echo "Starting Linux Patching System (Development Mode)..."
echo "=================================================="
echo
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo
echo "Starting web server..."
source venv/bin/activate
cd web_portal
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
EOF
chmod +x run_dev.sh

# 10. Final status
echo
echo "========================================"
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "========================================"
echo
echo "To start the application:"
echo "  ./run_dev.sh"
echo
echo "Then access:"
echo "  http://localhost:5001"
echo
echo "Login:"
echo "  Username: admin"
echo "  Password: admin"
echo
echo "========================================"