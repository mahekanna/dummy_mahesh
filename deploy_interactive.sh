#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default Configuration
INSTALL_DIR="/opt/linux_patching_automation"
SERVICE_USER="patchadmin"
SERVICE_GROUP="patchadmin"
LOG_DIR="/var/log/patching"
BACKUP_DIR="/backup/patching"
CONFIG_DIR="/etc/patching"

# Configuration variables to be set interactively
USE_SENDMAIL=""
SMTP_SERVER=""
SMTP_PORT=""
SMTP_USERNAME=""
SMTP_PASSWORD=""
SMTP_USE_TLS=""
DEFAULT_ADMIN_EMAIL=""
BACKUP_ADMIN_EMAIL=""
WEB_PORT=""
DB_TYPE=""
DB_HOST=""
DB_PORT=""
DB_NAME=""
DB_USER=""
DB_PASSWORD=""
COMPANY_NAME=""
LDAP_ENABLED=""
LDAP_SERVER=""
LDAP_BASE_DN=""
LDAP_BIND_DN=""
LDAP_BIND_PASSWORD=""

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_prompt() {
    echo -e "${BLUE}[INPUT]${NC} $1"
}

log_section() {
    echo
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Prompt for yes/no questions
prompt_yes_no() {
    local prompt="$1"
    local default="$2"
    local response
    
    if [[ "$default" == "y" ]]; then
        read -p "$(echo -e "${BLUE}[INPUT]${NC} $prompt [Y/n]: ")" response
        response=${response:-y}
    else
        read -p "$(echo -e "${BLUE}[INPUT]${NC} $prompt [y/N]: ")" response
        response=${response:-n}
    fi
    
    [[ "$response" =~ ^[Yy]$ ]]
}

# Prompt for string input with default
prompt_input() {
    local prompt="$1"
    local default="$2"
    local response
    
    if [[ -n "$default" ]]; then
        read -p "$(echo -e "${BLUE}[INPUT]${NC} $prompt [$default]: ")" response
        echo "${response:-$default}"
    else
        read -p "$(echo -e "${BLUE}[INPUT]${NC} $prompt: ")" response
        echo "$response"
    fi
}

# Prompt for password (hidden input)
prompt_password() {
    local prompt="$1"
    local password
    
    echo -e "${BLUE}[INPUT]${NC} $prompt: "
    read -s password
    echo
    echo "$password"
}

# Validate email address
validate_email() {
    local email="$1"
    if [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Validate port number
validate_port() {
    local port="$1"
    if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1 ] && [ "$port" -le 65535 ]; then
        return 0
    else
        return 1
    fi
}

# Interactive configuration collection
collect_configuration() {
    log_section "Linux Patching Automation - Interactive Setup"
    
    echo
    echo "This script will guide you through the installation and configuration"
    echo "of the Linux Patching Automation system."
    echo
    echo "Press Enter to continue or Ctrl+C to exit..."
    read
    
    # Basic Configuration
    log_section "Basic Configuration"
    
    COMPANY_NAME=$(prompt_input "Enter your company name" "My Company")
    INSTALL_DIR=$(prompt_input "Installation directory" "$INSTALL_DIR")
    SERVICE_USER=$(prompt_input "Service user account" "$SERVICE_USER")
    SERVICE_GROUP=$(prompt_input "Service group" "$SERVICE_GROUP")
    LOG_DIR=$(prompt_input "Log directory" "$LOG_DIR")
    BACKUP_DIR=$(prompt_input "Backup directory" "$BACKUP_DIR")
    
    # Web Portal Configuration
    log_section "Web Portal Configuration"
    
    while true; do
        WEB_PORT=$(prompt_input "Web portal port" "5001")
        if validate_port "$WEB_PORT"; then
            break
        else
            log_error "Invalid port number. Please enter a number between 1 and 65535."
        fi
    done
    
    # Admin Configuration
    log_section "Administrator Configuration"
    
    while true; do
        DEFAULT_ADMIN_EMAIL=$(prompt_input "Primary administrator email" "")
        if validate_email "$DEFAULT_ADMIN_EMAIL"; then
            break
        else
            log_error "Invalid email address. Please enter a valid email."
        fi
    done
    
    while true; do
        BACKUP_ADMIN_EMAIL=$(prompt_input "Backup administrator email (optional)" "")
        if [[ -z "$BACKUP_ADMIN_EMAIL" ]] || validate_email "$BACKUP_ADMIN_EMAIL"; then
            break
        else
            log_error "Invalid email address. Please enter a valid email or leave blank."
        fi
    done
    
    # Email Configuration
    log_section "Email Configuration"
    
    echo "Choose email delivery method:"
    echo "1) Local sendmail command (recommended if sendmail is configured)"
    echo "2) SMTP server (requires SMTP server configuration)"
    echo
    
    while true; do
        EMAIL_METHOD=$(prompt_input "Email method [1/2]" "1")
        if [[ "$EMAIL_METHOD" == "1" || "$EMAIL_METHOD" == "2" ]]; then
            break
        else
            log_error "Please enter 1 or 2"
        fi
    done
    
    if [[ "$EMAIL_METHOD" == "1" ]]; then
        log_info "Using local sendmail command"
        SMTP_SERVER="localhost"
        SMTP_PORT="25"
        SMTP_USE_TLS="false"
        SMTP_USERNAME="$DEFAULT_ADMIN_EMAIL"
        SMTP_PASSWORD=""
        USE_SENDMAIL="true"
    else
        log_info "Configuring SMTP server"
        SMTP_SERVER=$(prompt_input "SMTP server hostname" "smtp.gmail.com")
        
        while true; do
            SMTP_PORT=$(prompt_input "SMTP port" "587")
            if validate_port "$SMTP_PORT"; then
                break
            else
                log_error "Invalid port number. Please enter a number between 1 and 65535."
            fi
        done
        
        SMTP_USE_TLS=$(prompt_yes_no "Use TLS/STARTTLS for SMTP?" "y" && echo "true" || echo "false")
        SMTP_USERNAME=$(prompt_input "SMTP username/email" "$DEFAULT_ADMIN_EMAIL")
        SMTP_PASSWORD=$(prompt_password "SMTP password")
        USE_SENDMAIL="false"
    fi
    
    # Database Configuration
    log_section "Database Configuration"
    
    echo "Choose database type:"
    echo "1) SQLite (Simple, file-based, no setup required)"
    echo "2) PostgreSQL (Recommended for production)"
    echo
    
    while true; do
        DB_CHOICE=$(prompt_input "Enter choice [1-2]" "1")
        case $DB_CHOICE in
            1)
                DB_TYPE="sqlite"
                log_info "Selected SQLite database"
                break
                ;;
            2)
                DB_TYPE="postgresql"
                log_info "Selected PostgreSQL database"
                
                DB_HOST=$(prompt_input "PostgreSQL host" "localhost")
                
                while true; do
                    DB_PORT=$(prompt_input "PostgreSQL port" "5432")
                    if validate_port "$DB_PORT"; then
                        break
                    else
                        log_error "Invalid port number."
                    fi
                done
                
                DB_NAME=$(prompt_input "Database name" "patching_db")
                DB_USER=$(prompt_input "Database user" "patchadmin")
                DB_PASSWORD=$(prompt_password "Database password")
                break
                ;;
            *)
                log_error "Invalid choice. Please enter 1 or 2."
                ;;
        esac
    done
    
    # LDAP Configuration (Optional)
    log_section "LDAP Configuration (Optional)"
    
    if prompt_yes_no "Enable LDAP authentication?" "n"; then
        LDAP_ENABLED="true"
        LDAP_SERVER=$(prompt_input "LDAP server URL" "ldap://ldap.company.com")
        LDAP_BASE_DN=$(prompt_input "LDAP base DN" "dc=company,dc=com")
        LDAP_BIND_DN=$(prompt_input "LDAP bind DN" "cn=admin,dc=company,dc=com")
        LDAP_BIND_PASSWORD=$(prompt_password "LDAP bind password")
    else
        LDAP_ENABLED="false"
    fi
    
    # Custom Quarter Configuration
    log_section "Patching Quarter Configuration"
    
    echo "The system uses custom quarters for patching schedules:"
    echo "Default: Q1 (Nov-Jan), Q2 (Feb-Apr), Q3 (May-Jul), Q4 (Aug-Oct)"
    echo
    
    if prompt_yes_no "Use default quarter configuration?" "y"; then
        USE_DEFAULT_QUARTERS="true"
    else
        USE_DEFAULT_QUARTERS="false"
        # TODO: Implement custom quarter configuration
        log_warn "Custom quarter configuration will be implemented in settings.py"
    fi
    
    # Configuration Summary
    log_section "Configuration Summary"
    
    echo "Please review your configuration:"
    echo
    echo "Basic Settings:"
    echo "  Company Name:        $COMPANY_NAME"
    echo "  Installation Dir:    $INSTALL_DIR"
    echo "  Service User:        $SERVICE_USER"
    echo "  Web Portal Port:     $WEB_PORT"
    echo
    echo "Email Settings:"
    if [[ "$USE_SENDMAIL" == "true" ]]; then
        echo "  Email Method:        Local sendmail"
        echo "  From Address:        $SMTP_USERNAME"
    else
        echo "  Email Method:        SMTP Server"
        echo "  SMTP Server:         $SMTP_SERVER:$SMTP_PORT"
        echo "  SMTP Username:       $SMTP_USERNAME"
        echo "  Use TLS:             $SMTP_USE_TLS"
    fi
    echo
    echo "Database Settings:"
    echo "  Type:                $DB_TYPE"
    if [[ "$DB_TYPE" == "postgresql" ]]; then
        echo "  Host:                $DB_HOST:$DB_PORT"
        echo "  Database:            $DB_NAME"
        echo "  User:                $DB_USER"
    fi
    echo
    echo "Admin Settings:"
    echo "  Primary Admin:       $DEFAULT_ADMIN_EMAIL"
    echo "  Backup Admin:        ${BACKUP_ADMIN_EMAIL:-Not configured}"
    echo
    echo "LDAP Settings:"
    echo "  Enabled:             $LDAP_ENABLED"
    if [[ "$LDAP_ENABLED" == "true" ]]; then
        echo "  Server:              $LDAP_SERVER"
        echo "  Base DN:             $LDAP_BASE_DN"
    fi
    echo
    
    if ! prompt_yes_no "Continue with installation?" "y"; then
        log_warn "Installation cancelled by user"
        exit 0
    fi
}

# Create configuration files with collected settings
create_configuration_files() {
    log_info "Creating configuration files..."
    
    # Create settings.py
    cat > "$INSTALL_DIR/config/settings.py" << EOF
# config/settings.py
# Auto-generated by interactive deployment script
# Company: $COMPANY_NAME
# Generated: $(date)

import os
from datetime import datetime, timedelta

class Config:
    # Company Information
    COMPANY_NAME = "$COMPANY_NAME"
    
    # Base Paths
    PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
    CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    CSV_FILE_PATH = os.path.join(DATA_DIR, 'servers.csv')
    LOG_DIR = "$LOG_DIR"
    TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates')
    BACKUP_DIR = "$BACKUP_DIR"
    
    # Database Configuration
    USE_SQLITE = $([ "$DB_TYPE" == "sqlite" ] && echo "True" || echo "False")
    
    # Database connection parameters (used for both SQLite and PostgreSQL)
    DB_HOST = "$DB_HOST"
    DB_PORT = "$DB_PORT"
    DB_NAME = "$DB_NAME"
    DB_USER = "$DB_USER"
    DB_PASSWORD = "$DB_PASSWORD"
    
    # Email Configuration
    USE_SENDMAIL = $([ "$USE_SENDMAIL" == "true" ] && echo "True" || echo "False")
    SMTP_SERVER = "$SMTP_SERVER"
    SMTP_PORT = $SMTP_PORT
    SMTP_USERNAME = "$SMTP_USERNAME"
    SMTP_PASSWORD = "$SMTP_PASSWORD"
    SMTP_USE_TLS = $([ "$SMTP_USE_TLS" == "true" ] && echo "True" || echo "False")
    DEFAULT_FROM_EMAIL = "$SMTP_USERNAME"
    
    # Admin Configuration
    DEFAULT_ADMIN_EMAIL = "$DEFAULT_ADMIN_EMAIL"
    BACKUP_ADMIN_EMAIL = "$BACKUP_ADMIN_EMAIL"
    
    # Web Portal Configuration
    WEB_PORT = $WEB_PORT
    SECRET_KEY = '$(openssl rand -hex 32)'
    
    # LDAP Configuration
    LDAP_ENABLED = $([ "$LDAP_ENABLED" == "true" ] && echo "True" || echo "False")
    LDAP_SERVER = "$LDAP_SERVER"
    LDAP_BASE_DN = "$LDAP_BASE_DN"
    LDAP_BIND_DN = "$LDAP_BIND_DN"
    LDAP_BIND_PASSWORD = "$LDAP_BIND_PASSWORD"
    
    # Patching Configuration
    PATCHING_WINDOW_START = 20  # 8 PM
    PATCHING_WINDOW_END = 0     # 12 AM
    MAX_SERVERS_PER_HOUR = 5
    POST_PATCH_WAIT_MINUTES = 15
    
    # Custom Quarters (Q1: Nov-Jan, Q2: Feb-Apr, Q3: May-Jul, Q4: Aug-Oct)
    QUARTERS = {
        1: {'name': 'Q1', 'months': [11, 12, 1], 'start_month': 11},
        2: {'name': 'Q2', 'months': [2, 3, 4], 'start_month': 2},
        3: {'name': 'Q3', 'months': [5, 6, 7], 'start_month': 5},
        4: {'name': 'Q4', 'months': [8, 9, 10], 'start_month': 8}
    }
    
    # Disk Space Thresholds
    DISK_WARNING_THRESHOLD = 80  # Percentage
    DISK_CRITICAL_THRESHOLD = 90 # Percentage
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def get_current_quarter():
        """Get current quarter based on custom quarters"""
        current_month = datetime.now().month
        for quarter_num, quarter_info in Config.QUARTERS.items():
            if current_month in quarter_info['months']:
                return quarter_num
        return 1  # Default to Q1
EOF

    # Create admin_config.json
    cat > "$INSTALL_DIR/config/admin_config.json" << EOF
{
    "admin_settings": {
        "admin_email": "$DEFAULT_ADMIN_EMAIL",
        "backup_admin_email": "$BACKUP_ADMIN_EMAIL",
        "notification_settings": {
            "send_daily_reports": true,
            "send_weekly_reports": true,
            "send_error_alerts": true,
            "daily_report_time": "09:00",
            "weekly_report_day": "Monday"
        }
    },
    "company_info": {
        "name": "$COMPANY_NAME",
        "timezone": "$(timedatectl show -p Timezone --value 2>/dev/null || echo 'UTC')"
    }
}
EOF

    # Create initial users.py with admin user
    cat > "$INSTALL_DIR/config/users.py" << EOF
# config/users.py
# User management and authentication

from werkzeug.security import check_password_hash, generate_password_hash
import json
import os

class User:
    def __init__(self, username, email, role='user'):
        self.username = username
        self.email = email
        self.role = role
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return self.username
    
    def is_admin(self):
        return self.role == 'admin'
    
    def can_approve_patches(self):
        return self.role in ['admin', 'approver', 'user']
    
    def can_modify_schedules(self):
        return self.role in ['admin', 'user']
    
    def can_view_reports(self):
        return self.role in ['admin', 'approver', 'user', 'readonly']

class UserManager:
    def __init__(self):
        self.users_file = os.path.join(os.path.dirname(__file__), 'users.json')
        self.users = self.load_users()
    
    def load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                return json.load(f)
        else:
            # Create default admin user
            default_users = {
                "admin": {
                    "email": "$DEFAULT_ADMIN_EMAIL",
                    "password": generate_password_hash("admin"),
                    "role": "admin"
                }
            }
            self.save_users(default_users)
            return default_users
    
    def save_users(self, users):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=4)
    
    def authenticate(self, username, password):
        """Authenticate user"""
        if username in self.users:
            user_data = self.users[username]
            if check_password_hash(user_data['password'], password):
                return User(username, user_data['email'], user_data['role'])
        return None
    
    def get_user(self, username):
        """Get user by username"""
        if username in self.users:
            user_data = self.users[username]
            return User(username, user_data['email'], user_data['role'])
        return None
    
    def create_user(self, username, email, password, role='user'):
        """Create new user"""
        if username not in self.users:
            self.users[username] = {
                'email': email,
                'password': generate_password_hash(password),
                'role': role
            }
            self.save_users(self.users)
            return True
        return False
    
    def update_user_password(self, username, new_password):
        """Update user password"""
        if username in self.users:
            self.users[username]['password'] = generate_password_hash(new_password)
            self.save_users(self.users)
            return True
        return False
EOF

    # Create systemd service file with correct port
    sed -i "s/5000/$WEB_PORT/g" /etc/systemd/system/patching-portal.service 2>/dev/null || true
    
    # Update firewall rules for the configured port
    if command -v firewall-cmd > /dev/null; then
        firewall-cmd --permanent --add-port=$WEB_PORT/tcp
        firewall-cmd --reload
    elif command -v ufw > /dev/null; then
        ufw allow $WEB_PORT/tcp
    fi
    
    # Set proper permissions
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/config/"
    chmod 640 "$INSTALL_DIR/config/settings.py"
    chmod 640 "$INSTALL_DIR/config/admin_config.json"
    chmod 640 "$INSTALL_DIR/config/users.py"
    
    log_info "Configuration files created successfully"
}

# Enhanced create_user function
create_user() {
    log_info "Creating service user..."
    
    if ! id -u "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        log_info "Created user: $SERVICE_USER"
    else
        log_warn "User $SERVICE_USER already exists"
    fi
    
    if ! getent group "$SERVICE_GROUP" &>/dev/null; then
        groupadd "$SERVICE_GROUP"
        log_info "Created group: $SERVICE_GROUP"
    fi
}

# Include all other functions from original deploy.sh
create_directories() {
    log_info "Creating directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$CONFIG_DIR"
    
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$BACKUP_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$CONFIG_DIR"
    
    # Create log rotation configuration
    cat > /etc/logrotate.d/patching << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_GROUP
    postrotate
        systemctl reload patching-portal || true
    endscript
}
EOF
    
    log_info "Directories created"
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y python3 python3-pip python3-venv snmp snmp-mibs-downloader \
                           sqlite3 sudo cron python3-dev build-essential \
                           postgresql postgresql-contrib libpq-dev openssl
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        yum update -y
        yum install -y python3 python3-pip net-snmp net-snmp-utils \
                       sqlite sudo cronie python3-devel gcc \
                       postgresql postgresql-devel postgresql-libs openssl
    else
        log_error "Unsupported OS. This script is for Debian/Ubuntu or RHEL/CentOS only."
        exit 1
    fi
    
    log_info "Dependencies installed"
}

install_application() {
    log_info "Installing application..."
    
    SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    rsync -av --exclude '.git' "$SOURCE_DIR/" "$INSTALL_DIR/"
    
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/"
    
    mkdir -p "$INSTALL_DIR/venv"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/venv"
    sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
    
    echo "Installing Python dependencies..."
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    
    # Install requirements based on database choice
    if [[ "$DB_TYPE" == "sqlite" ]]; then
        # Create SQLite-only requirements
        grep -v "psycopg2" "$INSTALL_DIR/requirements.txt" > "$INSTALL_DIR/requirements_sqlite.txt"
        chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/requirements_sqlite.txt"
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements_sqlite.txt"
    else
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    fi
    
    chmod +x "$INSTALL_DIR/bash_scripts/"*.sh
    chmod +x "$INSTALL_DIR/main.py"
    chmod +x "$INSTALL_DIR/monitor.py"
    
    log_info "Application installed"
}

create_systemd_services() {
    log_info "Creating systemd services..."
    
    # Web portal service
    cat > /etc/systemd/system/patching-portal.service << EOF
[Unit]
Description=Linux Patching Portal
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR/web_portal
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Patching monitor service
    cat > /etc/systemd/system/patching-monitor.service << EOF
[Unit]
Description=Linux Patching Monitor
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python monitor.py
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    
    log_info "Systemd services created"
}

initialize_database() {
    log_info "Initializing database..."
    
    if [[ "$DB_TYPE" == "postgresql" ]]; then
        # Create PostgreSQL database if it doesn't exist
        log_info "Creating PostgreSQL database..."
        
        sudo -u postgres psql << EOF 2>/dev/null || true
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
    fi
    
    # Run database initialization
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/main.py" --init-db
    
    log_info "Database initialized"
}

setup_ssh_keys() {
    log_info "Setting up SSH keys for $SERVICE_USER..."
    
    SSH_DIR="$INSTALL_DIR/.ssh"
    
    # Create SSH directory with proper ownership first
    mkdir -p "$SSH_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    
    if [ ! -f "$SSH_DIR/id_rsa" ]; then
        # Generate SSH key as the service user
        sudo -u "$SERVICE_USER" ssh-keygen -t rsa -b 4096 -f "$SSH_DIR/id_rsa" -N "" -C "patchadmin@$COMPANY_NAME"
        log_info "SSH key generated"
        
        # Set proper permissions
        chown "$SERVICE_USER:$SERVICE_GROUP" "$SSH_DIR/id_rsa" "$SSH_DIR/id_rsa.pub"
        chmod 600 "$SSH_DIR/id_rsa"
        chmod 644 "$SSH_DIR/id_rsa.pub"
        
        echo
        echo "SSH Public Key (copy this to target servers):"
        echo "============================================="
        cat "$SSH_DIR/id_rsa.pub"
        echo "============================================="
        echo
        echo "Add this key to the ~/.ssh/authorized_keys file on all target servers"
        echo "for the user that will execute patching commands (usually root or a sudo user)."
        echo
        read -p "Press Enter to continue..."
    else
        log_warn "SSH key already exists"
        # Ensure proper ownership even if key exists
        chown -R "$SERVICE_USER:$SERVICE_GROUP" "$SSH_DIR"
        chmod 700 "$SSH_DIR"
        chmod 600 "$SSH_DIR/id_rsa" 2>/dev/null || true
        chmod 644 "$SSH_DIR/id_rsa.pub" 2>/dev/null || true
    fi
}

show_post_install_instructions() {
    log_section "Installation Complete!"
    
    echo "The Linux Patching Automation system has been installed successfully!"
    echo
    echo "Access Information:"
    echo "==================="
    echo "Web Portal URL: http://$(hostname -f):$WEB_PORT"
    echo "Default Admin User: admin"
    echo "Default Admin Password: admin"
    echo
    echo "${RED}IMPORTANT: Change the default admin password immediately!${NC}"
    echo
    echo "Next Steps:"
    echo "==========="
    echo "1. Log into the web portal and change the admin password"
    echo "2. Add server inventory to the system:"
    echo "   - Via Web UI: Navigate to Admin Panel → Import CSV"
    echo "   - Via CLI: $INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py --import-csv servers.csv"
    echo
    echo "3. Configure SSH access:"
    echo "   - Copy the SSH public key shown earlier to all target servers"
    echo "   - Test connectivity: sudo -u $SERVICE_USER ssh target-server"
    echo
    echo "4. Set up server groups and owners in the web interface"
    echo
    echo "5. Test email notifications:"
    echo "   - Send a test email from Admin Panel → Settings"
    echo
    echo "Service Management:"
    echo "==================="
    echo "Start services:    systemctl start patching-portal patching-monitor"
    echo "Stop services:     systemctl stop patching-portal patching-monitor"
    echo "Service status:    systemctl status patching-portal patching-monitor"
    echo "View logs:         journalctl -u patching-portal -f"
    echo
    echo "Configuration Files:"
    echo "===================="
    echo "Main config:       $INSTALL_DIR/config/settings.py"
    echo "Admin config:      $INSTALL_DIR/config/admin_config.json"
    echo "User management:   $INSTALL_DIR/config/users.py"
    echo
    echo "For more information, refer to the documentation in $INSTALL_DIR/docs/"
}

start_services() {
    log_info "Starting services..."
    
    systemctl enable patching-portal.service
    systemctl enable patching-monitor.service
    
    systemctl start patching-portal.service
    systemctl start patching-monitor.service
    
    log_info "Services started"
}

# Main installation process
main() {
    log_section "Linux Patching Automation - Interactive Installation"
    
    set -e
    trap 'log_error "Installation failed! Check the error above for details."; exit 1' ERR
    
    check_root
    collect_configuration
    create_user
    create_directories
    install_dependencies
    install_application
    create_configuration_files
    create_systemd_services
    setup_ssh_keys
    initialize_database
    start_services
    show_post_install_instructions
}

# Run the installation
main