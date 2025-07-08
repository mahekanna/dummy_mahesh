#!/bin/bash

# Complete Linux Patching Automation Deployment Script
# Handles Python version requirements, permissions, and full end-to-end deployment
# Supports RHEL/CentOS systems with Python 3.11+ requirements

set -e

# Error handler for cleanup on failure
cleanup_on_error() {
    local exit_code=$?
    echo
    log_error "Deployment failed with exit code: $exit_code"
    echo
    log_warn "If you want to clean up and start over, run:"
    log_warn "  sudo ./quick_cleanup.sh      (for quick cleanup)"
    log_warn "  sudo ./cleanup_installation.sh  (for complete cleanup)"
    exit $exit_code
}

# Set up error trap
trap cleanup_on_error ERR

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_PYTHON_VERSION="3.11"
INSTALL_DIR="/opt/linux_patching_automation"
SERVICE_USER="patchadmin"
SERVICE_GROUP="patchadmin"
PASSWORD_INPUT_MODE="hidden"  # Will be set during configuration
LOG_DIR="/var/log/patching"
BACKUP_DIR="/backup/patching"
CONFIG_DIR="/etc/patching"
PYTHON_INSTALL_DIR="/opt/python311"
PYTHON_DOWNLOAD_URL="https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz"
PYTHON_VERSION="3.11.8"

# Interactive configuration variables
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

# Check Python version
check_python_version() {
    log_info "Checking Python version..."
    
    # Check if python3 exists and get version
    if command -v python3 &> /dev/null; then
        CURRENT_PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_info "Found Python $CURRENT_PYTHON_VERSION"
        
        # Compare versions
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            log_info "Python version $CURRENT_PYTHON_VERSION meets requirements (>= $REQUIRED_PYTHON_VERSION)"
            PYTHON_CMD="python3"
            PIP_CMD="pip3"
            return 0
        else
            log_warn "Python version $CURRENT_PYTHON_VERSION is below required $REQUIRED_PYTHON_VERSION"
            return 1
        fi
    else
        log_warn "Python3 not found"
        return 1
    fi
}

# Install Python from source
install_python_from_source() {
    log_section "Installing Python $PYTHON_VERSION from source"
    
    # Install build dependencies
    log_info "Installing build dependencies..."
    if [ -f /etc/redhat-release ]; then
        yum groupinstall -y "Development Tools"
        yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel \
                       sqlite-devel readline-devel tk-devel gdbm-devel \
                       db4-devel libpcap-devel xz-devel expat-devel
    elif [ -f /etc/debian_version ]; then
        apt-get update
        apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
                           libnss3-dev libssl-dev libsqlite3-dev libreadline-dev \
                           libffi-dev curl libbz2-dev
    fi
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download Python source
    log_info "Downloading Python $PYTHON_VERSION..."
    curl -O "$PYTHON_DOWNLOAD_URL"
    
    # Extract
    log_info "Extracting Python source..."
    tar -xzf "Python-$PYTHON_VERSION.tgz"
    cd "Python-$PYTHON_VERSION"
    
    # Configure and compile
    log_info "Configuring Python build..."
    ./configure --prefix="$PYTHON_INSTALL_DIR" --enable-optimizations --with-ensurepip=install
    
    log_info "Compiling Python (this may take several minutes)..."
    make -j$(nproc)
    
    # Install
    log_info "Installing Python..."
    make altinstall
    
    # Create symlinks
    ln -sf "$PYTHON_INSTALL_DIR/bin/python3.11" /usr/local/bin/python3.11
    ln -sf "$PYTHON_INSTALL_DIR/bin/pip3.11" /usr/local/bin/pip3.11
    
    # Set commands for later use
    PYTHON_CMD="$PYTHON_INSTALL_DIR/bin/python3.11"
    PIP_CMD="$PYTHON_INSTALL_DIR/bin/pip3.11"
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
    
    log_info "Python $PYTHON_VERSION installed successfully"
}

# Detect OS and set package manager
detect_os() {
    if [ -f /etc/redhat-release ]; then
        OS="rhel"
        if command -v dnf &> /dev/null; then
            PKG_MGR="dnf"
        else
            PKG_MGR="yum"
        fi
    elif [ -f /etc/debian_version ]; then
        OS="debian"
        PKG_MGR="apt"
    else
        log_error "Unsupported OS. This script supports RHEL/CentOS and Debian/Ubuntu."
        exit 1
    fi
    
    log_info "Detected OS: $OS, Package Manager: $PKG_MGR"
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
    
    # Use -p flag to show prompt on same line as input
    read -s -p "$(echo -e "${BLUE}[INPUT]${NC} $prompt: ")" password
    echo >&2  # Add newline after hidden input (to stderr)
    
    # Show asterisks to indicate password was entered (to stderr)
    if [[ -n "$password" ]]; then
        local masked=$(printf '*%.0s' $(seq 1 ${#password}))
        echo -e "${GREEN}[✓]${NC} Password entered: $masked" >&2
    else
        echo -e "${RED}[✗]${NC} No password entered" >&2
    fi
    
    # Only echo the actual password to stdout
    echo "$password"
}

# Prompt for password (visible input) - for troubleshooting
prompt_password_visible() {
    local prompt="$1"
    local password
    
    echo -e "${YELLOW}[WARNING]${NC} Password will be visible on screen!" >&2
    read -p "$(echo -e "${BLUE}[INPUT]${NC} $prompt: ")" password
    
    if [[ -n "$password" ]]; then
        echo -e "${GREEN}[✓]${NC} Password entered (${#password} characters)" >&2
    else
        echo -e "${RED}[✗]${NC} No password entered" >&2
    fi
    
    # Only echo the actual password to stdout
    echo "$password"
}

# Wrapper function to use appropriate password input method
get_password() {
    local prompt="$1"
    
    if [[ "$PASSWORD_INPUT_MODE" == "visible" ]]; then
        prompt_password_visible "$prompt"
    else
        prompt_password "$prompt"
    fi
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
    log_section "Linux Patching Automation - Complete Setup"
    
    echo
    echo "This script will install and configure the Linux Patching Automation system."
    echo "It will handle Python version requirements, permissions, and complete deployment."
    echo
    
    # Check if password input might be problematic
    echo -e "${YELLOW}[INFO]${NC} Testing password input capability..."
    echo -n "Press any key to test hidden input: "
    if read -s -n 1 test_char 2>/dev/null; then
        echo
        echo -e "${GREEN}[✓]${NC} Hidden password input is supported"
        PASSWORD_INPUT_MODE="hidden"
    else
        echo
        echo -e "${YELLOW}[WARNING]${NC} Hidden password input may not work properly in this environment"
        echo "Would you like to use visible password input instead? (passwords will be shown on screen)"
        if prompt_yes_no "Use visible password input?" "n"; then
            PASSWORD_INPUT_MODE="visible"
            echo -e "${YELLOW}[WARNING]${NC} Passwords will be visible during input!"
        else
            PASSWORD_INPUT_MODE="hidden"
            echo -e "${BLUE}[INFO]${NC} Using hidden password input (you won't see characters as you type)"
        fi
    fi
    
    echo
    echo "Press Enter to continue or Ctrl+C to exit..."
    read
    
    # Basic Configuration
    log_section "Basic Configuration"
    
    COMPANY_NAME=$(prompt_input "Enter your company name" "My Company")
    INSTALL_DIR=$(prompt_input "Installation directory" "$INSTALL_DIR")
    SERVICE_USER=$(prompt_input "Service user account" "$SERVICE_USER")
    SERVICE_GROUP=$(prompt_input "Service group" "$SERVICE_GROUP")
    
    # Set password for service user (system account only - NOT for web UI login)
    log_info "Setting password for $SERVICE_USER system user"
    log_info "NOTE: This is for system/SSH access only. Web UI uses LDAP/netgroup authentication."
    
    while true; do
        SERVICE_USER_PASSWORD=$(get_password "System password for $SERVICE_USER user")
        
        # Debug: Check if password was captured
        if [[ -z "$SERVICE_USER_PASSWORD" ]]; then
            log_error "Failed to capture password. Please try again."
            continue
        fi
        
        if [[ ${#SERVICE_USER_PASSWORD} -lt 8 ]]; then
            log_error "Password must be at least 8 characters long (got ${#SERVICE_USER_PASSWORD} characters)"
            continue
        fi
        
        SERVICE_USER_PASSWORD_CONFIRM=$(get_password "Confirm system password for $SERVICE_USER user")
        
        if [[ -z "$SERVICE_USER_PASSWORD_CONFIRM" ]]; then
            log_error "Failed to capture confirmation password. Please try again."
            continue
        fi
        
        if [[ "$SERVICE_USER_PASSWORD" == "$SERVICE_USER_PASSWORD_CONFIRM" ]]; then
            log_info "Passwords match. Proceeding with user creation."
            break
        else
            log_error "Passwords do not match. Please try again."
        fi
    done
    
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
        SMTP_PASSWORD=$(get_password "SMTP password")
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
                
                # Set database password with confirmation
                while true; do
                    DB_PASSWORD=$(get_password "Database password")
                    if [[ ${#DB_PASSWORD} -lt 8 ]]; then
                        log_error "Database password must be at least 8 characters long"
                        continue
                    fi
                    DB_PASSWORD_CONFIRM=$(get_password "Confirm database password")
                    if [[ "$DB_PASSWORD" == "$DB_PASSWORD_CONFIRM" ]]; then
                        break
                    else
                        log_error "Passwords do not match. Please try again."
                    fi
                done
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
        LDAP_BIND_PASSWORD=$(get_password "LDAP bind password")
    else
        LDAP_ENABLED="false"
    fi
    
    # Patching Script Configuration
    log_section "Remote Patching Script Configuration"
    
    echo "Configure the patching script path that will be used on remote servers:"
    echo "This script will be executed on target servers for patching operations."
    echo
    
    PATCHING_SCRIPT_PATH=$(prompt_input "Patching script path on remote servers" "/opt/scripts/patch_server.sh")
    
    while true; do
        if [[ "$PATCHING_SCRIPT_PATH" =~ ^/.+\.sh$ ]]; then
            break
        else
            log_error "Please provide a valid absolute path ending with .sh"
            PATCHING_SCRIPT_PATH=$(prompt_input "Patching script path on remote servers" "/opt/scripts/patch_server.sh")
        fi
    done
    
    if prompt_yes_no "Enable patching script validation on remote servers?" "y"; then
        VALIDATE_PATCHING_SCRIPT="true"
        echo "Note: System will check if the script exists on remote servers before patching"
    else
        VALIDATE_PATCHING_SCRIPT="false"
    fi
    
    # Configuration Summary
    log_section "Configuration Summary"
    
    echo "Please review your configuration:"
    echo
    echo "Basic Settings:"
    echo "  Company Name:        $COMPANY_NAME"
    echo "  Installation Dir:    $INSTALL_DIR"
    echo "  Service User:        $SERVICE_USER"
    echo "  Service Password:    *** (configured)"
    echo "  Web Portal Port:     $WEB_PORT"
    echo
    echo "Python Configuration:"
    echo "  Required Version:    $REQUIRED_PYTHON_VERSION+"
    echo "  Install Path:        $PYTHON_INSTALL_DIR (if needed)"
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
        echo "  Password:            *** (configured)"
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
    echo "Patching Script Settings:"
    echo "  Script Path:         $PATCHING_SCRIPT_PATH"
    echo "  Validation:          $VALIDATE_PATCHING_SCRIPT"
    echo
    
    if ! prompt_yes_no "Continue with installation?" "y"; then
        log_warn "Installation cancelled by user"
        exit 0
    fi
}

# Create service user
create_user() {
    log_info "Creating service user..."
    
    if ! id -u "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        log_info "Created user: $SERVICE_USER"
        
        # Set password for the service user
        if [[ -n "$SERVICE_USER_PASSWORD" ]]; then
            echo "$SERVICE_USER:$SERVICE_USER_PASSWORD" | chpasswd
            if [[ $? -eq 0 ]]; then
                log_info "Password set for user: $SERVICE_USER"
            else
                log_error "Failed to set password for user: $SERVICE_USER"
                exit 1
            fi
        else
            log_error "No password provided for user: $SERVICE_USER"
            exit 1
        fi
    else
        log_warn "User $SERVICE_USER already exists"
        # Still set/update password for existing user
        if [[ -n "$SERVICE_USER_PASSWORD" ]]; then
            echo "$SERVICE_USER:$SERVICE_USER_PASSWORD" | chpasswd
            if [[ $? -eq 0 ]]; then
                log_info "Password updated for existing user: $SERVICE_USER"
            else
                log_error "Failed to update password for user: $SERVICE_USER"
                exit 1
            fi
        else
            log_error "No password provided for user: $SERVICE_USER"
            exit 1
        fi
    fi
    
    if ! getent group "$SERVICE_GROUP" &>/dev/null; then
        groupadd "$SERVICE_GROUP"
        log_info "Created group: $SERVICE_GROUP"
    fi
    
    # Add service user to sudo group for system operations
    usermod -a -G wheel "$SERVICE_USER" 2>/dev/null || usermod -a -G sudo "$SERVICE_USER" 2>/dev/null || true
}

# Create directories with proper permissions
create_directories() {
    log_info "Creating directories with proper permissions..."
    
    # Create all required directories
    mkdir -p "$INSTALL_DIR" "$LOG_DIR" "$BACKUP_DIR" "$CONFIG_DIR"
    mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/config"
    mkdir -p "$INSTALL_DIR/web_portal/static" "$INSTALL_DIR/web_portal/templates"
    
    # Set ownership recursively
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$BACKUP_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$CONFIG_DIR"
    
    # Set directory permissions
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$BACKUP_DIR"
    chmod 755 "$CONFIG_DIR"
    
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
    
    log_info "Directories created with proper permissions"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    if [[ "$OS" == "rhel" ]]; then
        # RHEL/CentOS
        $PKG_MGR update -y
        $PKG_MGR install -y net-snmp net-snmp-utils sqlite sudo cronie \
                          gcc gcc-c++ make openssl-devel bzip2-devel libffi-devel \
                          zlib-devel readline-devel tk-devel gdbm-devel \
                          db4-devel libpcap-devel xz-devel expat-devel \
                          rsync curl wget tar gzip \
                          openldap-devel python3-ldap || true
        
        # Install sendmail if using local email
        if [[ "$USE_SENDMAIL" == "true" ]]; then
            $PKG_MGR install -y sendmail sendmail-cf
            systemctl enable sendmail
            systemctl start sendmail
        fi
        
        # Install PostgreSQL if needed
        if [[ "$DB_TYPE" == "postgresql" ]]; then
            $PKG_MGR install -y postgresql postgresql-server postgresql-devel postgresql-contrib
            if [[ "$DB_HOST" == "localhost" ]]; then
                # Initialize database if not already done
                if [ ! -f /var/lib/pgsql/data/postgresql.conf ]; then
                    postgresql-setup initdb
                fi
                systemctl enable postgresql
                systemctl start postgresql
                
                # Wait for PostgreSQL to be ready
                sleep 10
                
                # Ensure PostgreSQL is running
                if ! systemctl is-active --quiet postgresql; then
                    log_error "Failed to start PostgreSQL"
                    exit 1
                fi
            fi
        fi
        
    elif [[ "$OS" == "debian" ]]; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y snmp snmp-mibs-downloader sqlite3 sudo cron \
                           build-essential gcc make libssl-dev libbz2-dev \
                           libffi-dev zlib1g-dev libreadline-dev libsqlite3-dev \
                           libncurses5-dev libgdbm-dev libnss3-dev libssl-dev \
                           tk-dev libgdbm-dev libc6-dev \
                           rsync curl wget tar gzip \
                           libldap2-dev libsasl2-dev python3-ldap || true
        
        # Install sendmail if using local email
        if [[ "$USE_SENDMAIL" == "true" ]]; then
            apt-get install -y sendmail sendmail-cf
            systemctl enable sendmail
            systemctl start sendmail
        fi
        
        # Install PostgreSQL if needed
        if [[ "$DB_TYPE" == "postgresql" ]]; then
            apt-get install -y postgresql postgresql-contrib libpq-dev postgresql-client
            if [[ "$DB_HOST" == "localhost" ]]; then
                systemctl enable postgresql
                systemctl start postgresql
                
                # Wait for PostgreSQL to be ready
                sleep 10
                
                # Ensure PostgreSQL is running
                if ! systemctl is-active --quiet postgresql; then
                    log_error "Failed to start PostgreSQL"
                    exit 1
                fi
                
                # Set proper PostgreSQL version detection for Debian/Ubuntu
                PG_VERSION=$(sudo -u postgres psql --version | awk '{print $3}' | sed 's/\..*//')
                if [ -z "$PG_VERSION" ]; then
                    PG_VERSION=$(ls /etc/postgresql/ | head -1)
                fi
            fi
        fi
    fi
    
    log_info "System dependencies installed"
}

# Install application files
install_application() {
    log_info "Installing application files..."
    
    SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # Copy application files
    rsync -av --exclude '.git' --exclude '*.pyc' --exclude '__pycache__' "$SOURCE_DIR/" "$INSTALL_DIR/"
    
    # Set proper ownership
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/"
    
    # Set executable permissions
    chmod +x "$INSTALL_DIR/bash_scripts/"*.sh
    chmod +x "$INSTALL_DIR/main.py"
    chmod +x "$INSTALL_DIR/monitor.py"
    chmod +x "$INSTALL_DIR/web_portal/app.py"
    
    # Set file permissions
    find "$INSTALL_DIR" -type f -name "*.py" -exec chmod 644 {} \;
    find "$INSTALL_DIR" -type f -name "*.html" -exec chmod 644 {} \;
    find "$INSTALL_DIR" -type f -name "*.css" -exec chmod 644 {} \;
    find "$INSTALL_DIR" -type f -name "*.js" -exec chmod 644 {} \;
    
    log_info "Application files installed"
}

# Setup Python environment
setup_python_environment() {
    log_info "Setting up Python environment..."
    
    # Create Python virtual environment
    mkdir -p "$INSTALL_DIR/venv"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/venv"
    
    # Create virtual environment as the service user
    sudo -u "$SERVICE_USER" "$PYTHON_CMD" -m venv "$INSTALL_DIR/venv"
    
    # Upgrade pip
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    
    # Install Python dependencies
    if [[ "$DB_TYPE" == "sqlite" ]]; then
        # Create SQLite-only requirements
        grep -v "psycopg2" "$INSTALL_DIR/requirements.txt" > "$INSTALL_DIR/requirements_sqlite.txt"
        chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/requirements_sqlite.txt"
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements_sqlite.txt"
    else
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    fi
    
    log_info "Python environment setup complete"
}

# Create configuration files
create_configuration_files() {
    log_info "Creating configuration files..."
    
    # Create settings.py
    cat > "$INSTALL_DIR/config/settings.py" << EOF
# config/settings.py
# Auto-generated by complete deployment script
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
    
    # Database connection parameters
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
    
    # Admin Control via Linux Netgroups
    ADMIN_NETGROUP = os.getenv('ADMIN_NETGROUP', 'patching_admins')
    
    # Authentication Settings
    ENABLE_FALLBACK_AUTH = os.getenv('ENABLE_FALLBACK_AUTH', 'True').lower() == 'true'
    
    # Remote Patching Script Configuration
    PATCHING_SCRIPT_PATH = "$PATCHING_SCRIPT_PATH"
    VALIDATE_PATCHING_SCRIPT = $([ "$VALIDATE_PATCHING_SCRIPT" == "true" ] && echo "True" || echo "False")
    
    # SSH Configuration for Remote Operations
    SSH_CONNECTION_TIMEOUT = 30  # seconds
    SSH_COMMAND_TIMEOUT = 300    # seconds (5 minutes)
    MAX_RETRY_ATTEMPTS = 3
    
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

    # Create admin configuration
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
    },
    "ldap_configuration": {
        "enabled": $LDAP_ENABLED,
        "server": "$LDAP_SERVER",
        "base_dn": "$LDAP_BASE_DN",
        "bind_dn": "$LDAP_BIND_DN"
    }
}
EOF

    # Set proper permissions on config files
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/config/"
    chmod 640 "$INSTALL_DIR/config/settings.py"
    chmod 640 "$INSTALL_DIR/config/admin_config.json"
    
    log_info "Configuration files created"
}

# Create systemd services
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
Environment=PYTHONPATH=$INSTALL_DIR
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
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python monitor.py
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    log_info "Systemd services created"
}

# Initialize database
initialize_database() {
    log_info "Initializing database..."
    
    if [[ "$DB_TYPE" == "postgresql" && "$DB_HOST" == "localhost" ]]; then
        # Create PostgreSQL database if it doesn't exist
        log_info "Creating PostgreSQL database and user..."
        
        # Check if user exists and create if not
        sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
        sudo -u postgres psql << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER USER $DB_USER CREATEDB;
EOF
        
        # Check if database exists and create if not
        sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME || \
        sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
GRANT CREATE ON SCHEMA public TO $DB_USER;
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
EOF
        
        # Configure PostgreSQL for production
        PG_VERSION=$(sudo -u postgres psql --version | awk '{print $3}' | sed 's/\..*//')
        
        # Determine config directory based on OS
        if [[ "$OS" == "rhel" ]]; then
            PG_CONFIG_DIR="/var/lib/pgsql/data"
        else
            # Debian/Ubuntu
            PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"
            if [ ! -d "$PG_CONFIG_DIR" ]; then
                # Fallback to first available version
                PG_VERSION=$(ls /etc/postgresql/ | head -1)
                PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"
            fi
        fi
        
        if [ -d "$PG_CONFIG_DIR" ]; then
            # Backup original config
            cp "$PG_CONFIG_DIR/postgresql.conf" "$PG_CONFIG_DIR/postgresql.conf.backup" 2>/dev/null || true
            cp "$PG_CONFIG_DIR/pg_hba.conf" "$PG_CONFIG_DIR/pg_hba.conf.backup" 2>/dev/null || true
            
            # Update postgresql.conf for better performance
            cat >> "$PG_CONFIG_DIR/postgresql.conf" << EOF

# Patching automation optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 4.0
effective_io_concurrency = 2
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Connection settings
max_connections = 200

# Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
EOF
            
            # Update pg_hba.conf for local connections
            if ! grep -q "# Patching automation" "$PG_CONFIG_DIR/pg_hba.conf"; then
                cat >> "$PG_CONFIG_DIR/pg_hba.conf" << EOF

# Patching automation access
local   $DB_NAME    $DB_USER                    md5
host    $DB_NAME    $DB_USER    127.0.0.1/32    md5
host    $DB_NAME    $DB_USER    ::1/128         md5
EOF
            fi
            
            # Restart PostgreSQL to apply changes
            systemctl restart postgresql
            sleep 5
        fi
        
        # Test database connection
        log_info "Testing database connection..."
        if sudo -u "$SERVICE_USER" PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
            log_info "Database connection test successful"
        else
            log_error "Database connection test failed"
            exit 1
        fi
        
    elif [[ "$DB_TYPE" == "postgresql" && "$DB_HOST" != "localhost" ]]; then
        # For remote PostgreSQL, just test the connection
        log_info "Testing remote PostgreSQL connection..."
        if sudo -u "$SERVICE_USER" PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
            log_info "Remote database connection test successful"
        else
            log_error "Remote database connection test failed. Please ensure:"
            log_error "1. PostgreSQL server is running on $DB_HOST:$DB_PORT"
            log_error "2. Database '$DB_NAME' exists"
            log_error "3. User '$DB_USER' has access to the database"
            log_error "4. Network connectivity is available"
            exit 1
        fi
    fi
    
    # Create sample CSV if it doesn't exist
    if [ ! -f "$INSTALL_DIR/data/servers.csv" ]; then
        cat > "$INSTALL_DIR/data/servers.csv" << EOF
Server Name,IP Address,Operating System,Primary Owner,Secondary Owner,Location,Environment,Server Timezone,host_group,Q1 Patch Date,Q1 Patch Time,Q1 Approval Status,Q2 Patch Date,Q2 Patch Time,Q2 Approval Status,Q3 Patch Date,Q3 Patch Time,Q3 Approval Status,Q4 Patch Date,Q4 Patch Time,Q4 Approval Status,Current Quarter Patching Status,Last Patch Date,Patch Duration,Notes
sample-server-01,192.168.1.10,RHEL 8,admin@company.com,backup@company.com,Data Center,Production,America/New_York,web_servers,,,Pending,,,Pending,,,Pending,,,Pending,Pending,,,Sample server entry
EOF
        chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/data/servers.csv"
    fi
    
    # Run database initialization
    sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/main.py" --init-db 2>/dev/null || true
    
    log_info "Database initialized"
}

# Setup SSH keys
setup_ssh_keys() {
    log_info "Setting up SSH keys for $SERVICE_USER..."
    
    SSH_DIR="$INSTALL_DIR/.ssh"
    
    # Create SSH directory with proper ownership
    mkdir -p "$SSH_DIR"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    
    if [ ! -f "$SSH_DIR/id_rsa" ]; then
        # Generate SSH key as the service user
        sudo -u "$SERVICE_USER" ssh-keygen -t rsa -b 4096 -f "$SSH_DIR/id_rsa" -N "" -C "patchadmin@$COMPANY_NAME"
        
        # Set proper permissions
        chown "$SERVICE_USER:$SERVICE_GROUP" "$SSH_DIR/id_rsa" "$SSH_DIR/id_rsa.pub"
        chmod 600 "$SSH_DIR/id_rsa"
        chmod 644 "$SSH_DIR/id_rsa.pub"
        
        log_info "SSH key generated"
    else
        log_warn "SSH key already exists"
        # Ensure proper ownership
        chown -R "$SERVICE_USER:$SERVICE_GROUP" "$SSH_DIR"
        chmod 700 "$SSH_DIR"
        chmod 600 "$SSH_DIR/id_rsa" 2>/dev/null || true
        chmod 644 "$SSH_DIR/id_rsa.pub" 2>/dev/null || true
    fi
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    # Configure firewall for web portal
    if command -v firewall-cmd > /dev/null; then
        firewall-cmd --permanent --add-port=$WEB_PORT/tcp
        firewall-cmd --reload
        log_info "Firewall configured (firewalld)"
    elif command -v ufw > /dev/null; then
        ufw allow $WEB_PORT/tcp
        log_info "Firewall configured (ufw)"
    else
        log_warn "No firewall management tool found. Please manually open port $WEB_PORT"
    fi
}

# Setup sudoers for service user
setup_sudoers() {
    log_info "Setting up sudoers for $SERVICE_USER..."
    
    # Create sudoers file for patching operations
    cat > /etc/sudoers.d/patching << EOF
# Patching automation sudoers file
$SERVICE_USER ALL=(ALL) NOPASSWD: /usr/bin/yum, /usr/bin/dnf, /usr/bin/apt, /usr/bin/apt-get, /usr/bin/systemctl, /usr/bin/reboot, /usr/bin/shutdown
$SERVICE_USER ALL=(ALL) NOPASSWD: /bin/mount, /bin/umount, /usr/bin/df, /usr/bin/du
$SERVICE_USER ALL=(ALL) NOPASSWD: /usr/bin/snmpwalk, /usr/bin/snmpget
EOF
    
    # Set proper permissions
    chmod 440 /etc/sudoers.d/patching
    
    log_info "Sudoers configured"
}

# Start services
start_services() {
    log_info "Starting and enabling services..."
    
    # Enable and start services
    systemctl enable patching-portal.service
    systemctl enable patching-monitor.service
    
    systemctl start patching-portal.service
    systemctl start patching-monitor.service
    
    # Check service status
    sleep 5
    if systemctl is-active --quiet patching-portal; then
        log_info "Patching portal service started successfully"
    else
        log_warn "Patching portal service failed to start"
    fi
    
    if systemctl is-active --quiet patching-monitor; then
        log_info "Patching monitor service started successfully"
    else
        log_warn "Patching monitor service failed to start"
    fi
}

# Show post-installation instructions
show_post_install_instructions() {
    log_section "Installation Complete!"
    
    echo "The Linux Patching Automation system has been installed successfully!"
    echo
    echo "System Information:"
    echo "==================="
    echo "Installation Path:     $INSTALL_DIR"
    echo "Service User:          $SERVICE_USER"
    echo "Python Version:        $($PYTHON_CMD --version)"
    echo "Python Path:           $PYTHON_CMD"
    echo "Virtual Environment:   $INSTALL_DIR/venv"
    echo "Database Type:         $DB_TYPE"
    if [[ "$DB_TYPE" == "postgresql" ]]; then
        echo "Database Host:         $DB_HOST:$DB_PORT"
        echo "Database Name:         $DB_NAME"
        echo "Database User:         $DB_USER"
    else
        echo "Database File:         $INSTALL_DIR/patching.db"
    fi
    echo
    echo "Access Information:"
    echo "==================="
    echo "Web Portal URL:        http://$(hostname -f):$WEB_PORT"
    echo
    if [[ "$LDAP_ENABLED" == "true" ]]; then
        echo "Authentication:        LDAP/nslcd (netgroup: $ADMIN_NETGROUP)"
        echo "Admin Access:          Users in '$ADMIN_NETGROUP' netgroup"
        echo "User Access:           Based on server ownership in CSV"
        echo
        echo "${GREEN}NOTE: Web UI login uses your LDAP/Linux credentials${NC}"
    else
        echo "Authentication:        Local (Demo Mode)"
        echo "Admin Login:           patchadmin / admin123"
        echo "Alternative Login:     admin / admin"
        echo
        echo "${YELLOW}WARNING: LDAP is not configured!${NC}"
        echo "${YELLOW}These demo logins are for initial setup only.${NC}"
        echo "${YELLOW}Enable LDAP authentication for production use.${NC}"
    fi
    echo
    echo "System User Info:"
    echo "================="
    echo "Service Account:       $SERVICE_USER (for SSH/system operations)"
    echo "SSH Access:           Use the $SERVICE_USER account for system tasks"
    echo
    echo "SSH Public Key (copy this to target servers):"
    echo "============================================="
    if [ -f "$INSTALL_DIR/.ssh/id_rsa.pub" ]; then
        cat "$INSTALL_DIR/.ssh/id_rsa.pub"
    else
        echo "SSH key not found. Generate manually if needed."
    fi
    echo "============================================="
    echo
    echo "Next Steps:"
    echo "==========="
    if [[ "$LDAP_ENABLED" == "true" ]]; then
        echo "1. Add admin users to '$ADMIN_NETGROUP' netgroup"
        echo "2. Import your server inventory CSV file"
        echo "3. Ensure CSV has correct Linux usernames for owners"
        echo "4. Test LDAP authentication via web portal"
        echo "5. Set up SSH access from $SERVICE_USER to target servers"
        echo "6. Configure automated patching schedules"
    else
        echo "1. Configure LDAP authentication for production use"
        echo "2. Import your server inventory CSV file"
        echo "3. Test with demo admin login (admin/admin)"
        echo "4. Set up SSH access from $SERVICE_USER to target servers"
        echo "5. Enable LDAP before production deployment"
    fi
    if [[ "$DB_TYPE" == "postgresql" ]]; then
        echo "7. Monitor PostgreSQL performance and tune as needed"
        echo "8. Set up PostgreSQL backups (pg_dump)"
    fi
    echo
    echo "Service Management:"
    echo "==================="
    echo "Start services:    systemctl start patching-portal patching-monitor"
    echo "Stop services:     systemctl stop patching-portal patching-monitor"
    echo "Service status:    systemctl status patching-portal"
    echo "View logs:         journalctl -u patching-portal -f"
    echo
    echo "File Locations:"
    echo "==============="
    echo "Application:       $INSTALL_DIR"
    echo "Configuration:     $INSTALL_DIR/config/"
    echo "Logs:             $LOG_DIR"
    echo "Backups:          $BACKUP_DIR"
    echo "Data:             $INSTALL_DIR/data/"
    echo
    echo "For more information, refer to the documentation in $INSTALL_DIR/docs/"
    echo
    echo "${GREEN}Installation completed successfully!${NC}"
}

# Main installation function
main() {
    log_section "Linux Patching Automation - Complete Deployment"
    
    # Set error handling
    set -e
    trap 'log_error "Installation failed at line $LINENO. Check the error above for details."; exit 1' ERR
    
    # Check if running as root
    check_root
    
    # Detect OS
    detect_os
    
    # Check Python version and install if needed
    if ! check_python_version; then
        log_warn "Python $REQUIRED_PYTHON_VERSION+ not found. Will install from source."
        install_python_from_source
    fi
    
    # Collect configuration
    collect_configuration
    
    # Installation steps
    create_user
    create_directories
    install_dependencies
    install_application
    setup_python_environment
    create_configuration_files
    create_systemd_services
    setup_ssh_keys
    setup_sudoers
    initialize_database
    configure_firewall
    start_services
    
    # Show completion message
    show_post_install_instructions
}

# Run the installation
main "$@"