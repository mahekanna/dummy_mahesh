#!/bin/bash

# Linux Patching Automation - Complete Deployment Script
# This script deploys the complete CLI-based patching system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
SYSTEM_USER="patchadmin"
INSTALL_DIR="/opt/linux_patching_automation"
VENV_DIR="$INSTALL_DIR/venv"
CONFIG_DIR="/etc/linux_patching_automation"
LOG_DIR="/var/log/linux_patching_automation"
DATA_DIR="/var/lib/linux_patching_automation"
SERVICE_NAME="linux-patching"
BACKUP_DIR="/var/backups/linux_patching_automation"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
        VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+')
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
        VERSION=$(cat /etc/debian_version)
    else
        print_error "Unable to detect Linux distribution"
        exit 1
    fi
    
    print_info "Detected OS: $DISTRO $VERSION"
}

# Function to install system dependencies
install_dependencies() {
    print_section "Installing System Dependencies"
    
    case $DISTRO in
        ubuntu|debian)
            apt-get update
            apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                build-essential \
                libffi-dev \
                libssl-dev \
                openssh-client \
                snmp \
                snmp-mibs-downloader \
                curl \
                wget \
                git \
                vim \
                htop \
                rsync \
                cron \
                logrotate \
                sudo \
                systemd
            ;;
        centos|rhel|fedora)
            if command -v dnf &> /dev/null; then
                dnf install -y \
                    python3 \
                    python3-pip \
                    python3-devel \
                    gcc \
                    gcc-c++ \
                    make \
                    libffi-devel \
                    openssl-devel \
                    openssh-clients \
                    net-snmp \
                    net-snmp-utils \
                    curl \
                    wget \
                    git \
                    vim \
                    htop \
                    rsync \
                    cronie \
                    logrotate \
                    sudo \
                    systemd
            else
                yum install -y \
                    python3 \
                    python3-pip \
                    python3-devel \
                    gcc \
                    gcc-c++ \
                    make \
                    libffi-devel \
                    openssl-devel \
                    openssh-clients \
                    net-snmp \
                    net-snmp-utils \
                    curl \
                    wget \
                    git \
                    vim \
                    htop \
                    rsync \
                    cronie \
                    logrotate \
                    sudo \
                    systemd
            fi
            ;;
        *)
            print_error "Unsupported distribution: $DISTRO"
            exit 1
            ;;
    esac
    
    print_status "System dependencies installed"
}

# Function to create system user
create_user() {
    print_section "Creating System User"
    
    if id "$SYSTEM_USER" &>/dev/null; then
        print_warning "User $SYSTEM_USER already exists"
    else
        # Create user with home directory
        useradd -m -s /bin/bash -d /home/$SYSTEM_USER $SYSTEM_USER
        
        # Set password (prompt for it)
        print_info "Setting password for $SYSTEM_USER user:"
        passwd $SYSTEM_USER
        
        # Add to sudo group
        case $DISTRO in
            ubuntu|debian)
                usermod -aG sudo $SYSTEM_USER
                ;;
            centos|rhel|fedora)
                usermod -aG wheel $SYSTEM_USER
                ;;
        esac
        
        print_status "User $SYSTEM_USER created"
    fi
    
    # Create SSH key for the user
    if [ ! -f /home/$SYSTEM_USER/.ssh/id_rsa ]; then
        print_info "Creating SSH key for $SYSTEM_USER"
        sudo -u $SYSTEM_USER ssh-keygen -t rsa -b 4096 -f /home/$SYSTEM_USER/.ssh/id_rsa -N ""
        sudo -u $SYSTEM_USER chmod 600 /home/$SYSTEM_USER/.ssh/id_rsa
        sudo -u $SYSTEM_USER chmod 644 /home/$SYSTEM_USER/.ssh/id_rsa.pub
        print_status "SSH key created"
    else
        print_warning "SSH key already exists for $SYSTEM_USER"
    fi
}

# Function to create directory structure
create_directories() {
    print_section "Creating Directory Structure"
    
    # Create directories
    mkdir -p $INSTALL_DIR
    mkdir -p $CONFIG_DIR
    mkdir -p $LOG_DIR
    mkdir -p $DATA_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p $DATA_DIR/reports
    mkdir -p $DATA_DIR/archives
    
    # Set ownership
    chown -R $SYSTEM_USER:$SYSTEM_USER $INSTALL_DIR
    chown -R $SYSTEM_USER:$SYSTEM_USER $DATA_DIR
    chown -R $SYSTEM_USER:$SYSTEM_USER $LOG_DIR
    chown -R $SYSTEM_USER:$SYSTEM_USER $BACKUP_DIR
    
    # Set permissions
    chmod 755 $INSTALL_DIR
    chmod 755 $CONFIG_DIR
    chmod 755 $LOG_DIR
    chmod 755 $DATA_DIR
    chmod 755 $BACKUP_DIR
    
    print_status "Directory structure created"
}

# Function to copy application files
copy_application() {
    print_section "Copying Application Files"
    
    # Copy application files
    cp -r . $INSTALL_DIR/
    
    # Remove unnecessary files
    rm -rf $INSTALL_DIR/.git
    rm -rf $INSTALL_DIR/__pycache__
    rm -rf $INSTALL_DIR/*/__pycache__
    find $INSTALL_DIR -name "*.pyc" -delete
    
    # Set ownership
    chown -R $SYSTEM_USER:$SYSTEM_USER $INSTALL_DIR
    
    # Make scripts executable
    chmod +x $INSTALL_DIR/cli/patch_manager.py
    chmod +x $INSTALL_DIR/scripts/*.sh
    
    print_status "Application files copied"
}

# Function to create Python virtual environment
create_venv() {
    print_section "Creating Python Virtual Environment"
    
    # Create virtual environment
    sudo -u $SYSTEM_USER python3 -m venv $VENV_DIR
    
    # Activate and install requirements
    sudo -u $SYSTEM_USER bash -c "
        source $VENV_DIR/bin/activate
        pip install --upgrade pip setuptools wheel
        pip install -r $INSTALL_DIR/requirements.txt
        pip install -e $INSTALL_DIR
    "
    
    print_status "Python virtual environment created"
}

# Function to create configuration files
create_config() {
    print_section "Creating Configuration Files"
    
    # Create main configuration file
    cat > $CONFIG_DIR/settings.py << EOF
# Linux Patching Automation Configuration
# Generated by deployment script

import os

# Paths
BASE_DIR = '$INSTALL_DIR'
DATA_DIR = '$DATA_DIR'
LOG_DIR = '$LOG_DIR'
BACKUP_DIR = '$BACKUP_DIR'

# SSH Configuration
SSH_KEY_PATH = '/home/$SYSTEM_USER/.ssh/id_rsa'
SSH_DEFAULT_USER = '$SYSTEM_USER'
SSH_TIMEOUT = 30

# Email Configuration (configure as needed)
SMTP_SERVER = 'localhost'
SMTP_PORT = 25
SMTP_USE_TLS = False
SMTP_USERNAME = ''
SMTP_PASSWORD = ''
EMAIL_FROM = 'patching@$(hostname -f)'

# Logging
LOG_LEVEL = 'INFO'
LOG_MAX_SIZE = 10485760  # 10MB
LOG_BACKUP_COUNT = 5

# Patching Configuration
MAX_PARALLEL_PATCHES = 3
PATCH_TIMEOUT_MINUTES = 120
PRECHECK_HOURS_BEFORE = 24

# Feature Flags
ENABLE_EMAIL_NOTIFICATIONS = True
ENABLE_ROLLBACK = True
ENABLE_PRECHECK = True
ENABLE_POSTCHECK = True
ENABLE_AUTO_REBOOT = True
REQUIRE_APPROVAL = True
EOF
    
    # Create environment file
    cat > $CONFIG_DIR/environment << EOF
# Environment variables for Linux Patching Automation
PATCHING_HOME=$INSTALL_DIR
PATCHING_USER=$SYSTEM_USER
PATCHING_DATA=$DATA_DIR
PATCHING_LOGS=$LOG_DIR
PATCHING_CONFIG=$CONFIG_DIR
PYTHONPATH=$INSTALL_DIR
PATH=$VENV_DIR/bin:\$PATH
EOF
    
    # Create logrotate configuration
    cat > /etc/logrotate.d/linux-patching << EOF
$LOG_DIR/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $SYSTEM_USER $SYSTEM_USER
    postrotate
        /bin/systemctl reload linux-patching 2>/dev/null || true
    endscript
}
EOF
    
    # Set permissions
    chown -R $SYSTEM_USER:$SYSTEM_USER $CONFIG_DIR
    chmod 640 $CONFIG_DIR/settings.py
    chmod 644 $CONFIG_DIR/environment
    
    print_status "Configuration files created"
}

# Function to create systemd service
create_service() {
    print_section "Creating Systemd Service"
    
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Linux Patching Automation Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SYSTEM_USER
Group=$SYSTEM_USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
Environment=PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=$CONFIG_DIR/environment
ExecStart=$VENV_DIR/bin/python -m cli.patch_manager system health --interval 300
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=linux-patching

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    
    print_status "Systemd service created"
}

# Function to create CLI wrapper
create_cli_wrapper() {
    print_section "Creating CLI Wrapper"
    
    cat > /usr/local/bin/patch-manager << EOF
#!/bin/bash
# Linux Patching Automation CLI Wrapper

# Source environment
if [ -f $CONFIG_DIR/environment ]; then
    source $CONFIG_DIR/environment
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Run the CLI
exec python $INSTALL_DIR/cli/patch_manager.py "\$@"
EOF
    
    chmod +x /usr/local/bin/patch-manager
    
    # Create additional aliases
    ln -sf /usr/local/bin/patch-manager /usr/local/bin/patching-cli
    ln -sf /usr/local/bin/patch-manager /usr/local/bin/linux-patcher
    
    print_status "CLI wrapper created"
}

# Function to create sample data
create_sample_data() {
    print_section "Creating Sample Data"
    
    # Create sample servers.csv
    cat > $DATA_DIR/servers.csv << EOF
Server Name,Host Group,Operating System,Environment,Server Timezone,Location,Primary Owner,Q1 Patch Date,Q1 Patch Time,Q1 Approval Status,Q2 Patch Date,Q2 Patch Time,Q2 Approval Status,Q3 Patch Date,Q3 Patch Time,Q3 Approval Status,Q4 Patch Date,Q4 Patch Time,Q4 Approval Status,Current Quarter Patching Status,Active Status
web01.company.com,web,ubuntu,production,America/New_York,US-East,admin@company.com,2024-01-15,02:00,Pending,2024-04-15,02:00,Pending,2024-07-15,02:00,Pending,2024-10-15,02:00,Pending,Active,Active
db01.company.com,database,centos,production,America/Chicago,US-Central,dba@company.com,2024-01-16,03:00,Pending,2024-04-16,03:00,Pending,2024-07-16,03:00,Pending,2024-10-16,03:00,Pending,Active,Active
app01.company.com,application,ubuntu,production,America/Los_Angeles,US-West,dev@company.com,2024-01-17,04:00,Pending,2024-04-17,04:00,Pending,2024-07-17,04:00,Pending,2024-10-17,04:00,Pending,Active,Active
EOF
    
    # Set ownership
    chown $SYSTEM_USER:$SYSTEM_USER $DATA_DIR/servers.csv
    
    print_status "Sample data created"
}

# Function to create cron jobs
create_cron_jobs() {
    print_section "Creating Cron Jobs"
    
    # Create cron file for the user
    cat > /tmp/patching-cron << EOF
# Linux Patching Automation Cron Jobs
# Daily pre-check at 2 AM
0 2 * * * $VENV_DIR/bin/python $INSTALL_DIR/cli/patch_manager.py precheck run --auto >> $LOG_DIR/cron.log 2>&1

# Weekly report on Monday at 8 AM
0 8 * * 1 $VENV_DIR/bin/python $INSTALL_DIR/cli/patch_manager.py report generate --type weekly >> $LOG_DIR/cron.log 2>&1

# Monthly cleanup on first day of month at 3 AM
0 3 1 * * $VENV_DIR/bin/python $INSTALL_DIR/cli/patch_manager.py system cleanup --days 30 --confirm >> $LOG_DIR/cron.log 2>&1

# Daily status check at 9 AM
0 9 * * * $VENV_DIR/bin/python $INSTALL_DIR/cli/patch_manager.py patch status >> $LOG_DIR/cron.log 2>&1
EOF
    
    # Install cron jobs for the user
    sudo -u $SYSTEM_USER crontab /tmp/patching-cron
    rm /tmp/patching-cron
    
    print_status "Cron jobs created"
}

# Function to create backup script
create_backup_script() {
    print_section "Creating Backup Script"
    
    cat > $INSTALL_DIR/scripts/backup.sh << EOF
#!/bin/bash
# Linux Patching Automation Backup Script

BACKUP_DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/patching_backup_\$BACKUP_DATE.tar.gz"

# Create backup
tar -czf \$BACKUP_FILE \\
    -C / \\
    --exclude='$LOG_DIR' \\
    --exclude='$BACKUP_DIR' \\
    $INSTALL_DIR \\
    $DATA_DIR \\
    $CONFIG_DIR

# Remove old backups (keep last 7 days)
find $BACKUP_DIR -name "patching_backup_*.tar.gz" -mtime +7 -delete

echo "Backup created: \$BACKUP_FILE"
EOF
    
    chmod +x $INSTALL_DIR/scripts/backup.sh
    chown $SYSTEM_USER:$SYSTEM_USER $INSTALL_DIR/scripts/backup.sh
    
    print_status "Backup script created"
}

# Function to create health check script
create_health_script() {
    print_section "Creating Health Check Script"
    
    cat > $INSTALL_DIR/scripts/health_check.sh << EOF
#!/bin/bash
# Linux Patching Automation Health Check Script

source $CONFIG_DIR/environment
source $VENV_DIR/bin/activate

# Run health check
python $INSTALL_DIR/cli/patch_manager.py system health

# Check service status
systemctl is-active $SERVICE_NAME >/dev/null 2>&1
if [ \$? -eq 0 ]; then
    echo "Service Status: Running"
else
    echo "Service Status: Stopped"
fi

# Check disk space
df -h $DATA_DIR | tail -1 | awk '{print "Data Directory Usage: " \$5 " (" \$3 "/" \$2 ")"}'
df -h $LOG_DIR | tail -1 | awk '{print "Log Directory Usage: " \$5 " (" \$3 "/" \$2 ")"}'

# Check last activity
if [ -f $LOG_DIR/patching.log ]; then
    echo "Last Activity: \$(tail -1 $LOG_DIR/patching.log | awk '{print \$1, \$2}')"
fi
EOF
    
    chmod +x $INSTALL_DIR/scripts/health_check.sh
    chown $SYSTEM_USER:$SYSTEM_USER $INSTALL_DIR/scripts/health_check.sh
    
    print_status "Health check script created"
}

# Function to set up firewall (if needed)
setup_firewall() {
    print_section "Setting up Firewall"
    
    # Check if firewall is active
    if systemctl is-active --quiet firewalld; then
        print_info "Configuring firewalld"
        # Allow SSH
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --reload
    elif systemctl is-active --quiet ufw; then
        print_info "Configuring ufw"
        # Allow SSH
        ufw allow ssh
    else
        print_warning "No firewall detected, skipping firewall configuration"
    fi
    
    print_status "Firewall configured"
}

# Function to run tests
run_tests() {
    print_section "Running Tests"
    
    # Test CLI
    sudo -u $SYSTEM_USER bash -c "
        source $VENV_DIR/bin/activate
        cd $INSTALL_DIR
        python -m pytest tests/ -v
    " || print_warning "Some tests failed"
    
    # Test CLI command
    sudo -u $SYSTEM_USER /usr/local/bin/patch-manager --version
    
    print_status "Tests completed"
}

# Function to display final information
display_final_info() {
    print_section "Deployment Complete"
    
    echo ""
    print_status "Linux Patching Automation has been successfully deployed!"
    echo ""
    echo "Installation Details:"
    echo "  - Install Directory: $INSTALL_DIR"
    echo "  - Data Directory: $DATA_DIR"
    echo "  - Log Directory: $LOG_DIR"
    echo "  - Config Directory: $CONFIG_DIR"
    echo "  - System User: $SYSTEM_USER"
    echo "  - Service Name: $SERVICE_NAME"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure email settings in $CONFIG_DIR/settings.py"
    echo "  2. Import your server inventory:"
    echo "     patch-manager server import --file /path/to/servers.csv"
    echo "  3. Test connectivity:"
    echo "     patch-manager server test"
    echo "  4. Start the service:"
    echo "     systemctl start $SERVICE_NAME"
    echo "  5. Check status:"
    echo "     patch-manager patch status"
    echo ""
    echo "Useful Commands:"
    echo "  - patch-manager --help"
    echo "  - patch-manager server list"
    echo "  - patch-manager patch status"
    echo "  - patch-manager system health"
    echo "  - systemctl status $SERVICE_NAME"
    echo ""
    echo "Log Files:"
    echo "  - Main Log: $LOG_DIR/patching.log"
    echo "  - Error Log: $LOG_DIR/patching_errors.log"
    echo "  - Audit Log: $LOG_DIR/patching_audit.log"
    echo ""
    echo "For support, check the documentation or contact the support team."
    echo ""
}

# Function to create uninstall script
create_uninstall_script() {
    cat > $INSTALL_DIR/scripts/uninstall.sh << EOF
#!/bin/bash
# Linux Patching Automation Uninstall Script

set -e

print_status() {
    echo -e "\033[0;32m[✓]\033[0m \$1"
}

print_warning() {
    echo -e "\033[1;33m[!]\033[0m \$1"
}

if [ "\$EUID" -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

echo "Uninstalling Linux Patching Automation..."

# Stop and disable service
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl disable $SERVICE_NAME 2>/dev/null || true
rm -f /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload

# Remove cron jobs
sudo -u $SYSTEM_USER crontab -r 2>/dev/null || true

# Remove CLI wrapper
rm -f /usr/local/bin/patch-manager
rm -f /usr/local/bin/patching-cli
rm -f /usr/local/bin/linux-patcher

# Remove directories (ask for confirmation)
read -p "Remove data directory $DATA_DIR? (y/N): " -n 1 -r
echo
if [[ \$REPLY =~ ^[Yy]$ ]]; then
    rm -rf $DATA_DIR
    print_status "Data directory removed"
fi

read -p "Remove log directory $LOG_DIR? (y/N): " -n 1 -r
echo
if [[ \$REPLY =~ ^[Yy]$ ]]; then
    rm -rf $LOG_DIR
    print_status "Log directory removed"
fi

# Remove installation directory
rm -rf $INSTALL_DIR

# Remove configuration
rm -rf $CONFIG_DIR

# Remove logrotate config
rm -f /etc/logrotate.d/linux-patching

# Remove backup directory (ask for confirmation)
read -p "Remove backup directory $BACKUP_DIR? (y/N): " -n 1 -r
echo
if [[ \$REPLY =~ ^[Yy]$ ]]; then
    rm -rf $BACKUP_DIR
    print_status "Backup directory removed"
fi

# Remove user (ask for confirmation)
read -p "Remove user $SYSTEM_USER? (y/N): " -n 1 -r
echo
if [[ \$REPLY =~ ^[Yy]$ ]]; then
    userdel -r $SYSTEM_USER 2>/dev/null || true
    print_status "User removed"
fi

print_status "Linux Patching Automation uninstalled successfully"
EOF
    
    chmod +x $INSTALL_DIR/scripts/uninstall.sh
}

# Main deployment function
main() {
    clear
    echo -e "${BLUE}Linux Patching Automation - Complete Deployment${NC}"
    echo -e "${BLUE}=================================================${NC}"
    echo ""
    
    # Check requirements
    check_root
    detect_distro
    
    # Run deployment steps
    install_dependencies
    create_user
    create_directories
    copy_application
    create_venv
    create_config
    create_service
    create_cli_wrapper
    create_sample_data
    create_cron_jobs
    create_backup_script
    create_health_script
    create_uninstall_script
    setup_firewall
    run_tests
    
    # Display final information
    display_final_info
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Linux Patching Automation Deployment Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --user USER    Specify system user (default: patchadmin)"
        echo "  --dir DIR      Specify installation directory (default: /opt/linux_patching_automation)"
        echo ""
        exit 0
        ;;
    --user)
        SYSTEM_USER="$2"
        shift 2
        ;;
    --dir)
        INSTALL_DIR="$2"
        VENV_DIR="$INSTALL_DIR/venv"
        shift 2
        ;;
esac

# Run main function
main "$@"