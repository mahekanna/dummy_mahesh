# Linux Patching Automation - Installation Guide

## Quick Installation

### Automated Installation (Recommended)

```bash
# Download and run the deployment script
curl -sSL https://raw.githubusercontent.com/company/linux-patching-automation/main/deploy.sh | sudo bash

# Or clone and run locally
git clone https://github.com/company/linux-patching-automation.git
cd linux-patching-automation/linux_patching_cli
sudo ./deploy.sh
```

### Manual Installation

#### 1. Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-dev \
    build-essential libffi-dev libssl-dev openssh-client snmp \
    snmp-mibs-downloader curl wget git
```

**CentOS/RHEL/Fedora:**
```bash
sudo dnf install -y python3 python3-pip python3-devel gcc gcc-c++ \
    make libffi-devel openssl-devel openssh-clients net-snmp \
    net-snmp-utils curl wget git

# Or for older versions:
sudo yum install -y python3 python3-pip python3-devel gcc gcc-c++ \
    make libffi-devel openssl-devel openssh-clients net-snmp \
    net-snmp-utils curl wget git
```

#### 2. Create System User

```bash
# Create patchadmin user
sudo useradd -m -s /bin/bash patchadmin

# Set password
sudo passwd patchadmin

# Add to sudo group
sudo usermod -aG sudo patchadmin  # Ubuntu/Debian
sudo usermod -aG wheel patchadmin  # CentOS/RHEL/Fedora

# Create SSH key
sudo -u patchadmin ssh-keygen -t rsa -b 4096 -f /home/patchadmin/.ssh/id_rsa -N ""
```

#### 3. Create Directory Structure

```bash
# Create directories
sudo mkdir -p /opt/linux_patching_automation
sudo mkdir -p /etc/linux_patching_automation
sudo mkdir -p /var/log/linux_patching_automation
sudo mkdir -p /var/lib/linux_patching_automation
sudo mkdir -p /var/backups/linux_patching_automation

# Set ownership
sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation
sudo chown -R patchadmin:patchadmin /var/log/linux_patching_automation
sudo chown -R patchadmin:patchadmin /var/lib/linux_patching_automation
sudo chown -R patchadmin:patchadmin /var/backups/linux_patching_automation
```

#### 4. Install Application

```bash
# Clone repository
cd /opt/linux_patching_automation
sudo -u patchadmin git clone https://github.com/company/linux-patching-automation.git .

# Create virtual environment
sudo -u patchadmin python3 -m venv venv

# Activate and install
sudo -u patchadmin bash -c "
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    pip install -e .
"
```

#### 5. Configure System

```bash
# Create configuration file
sudo cp config/settings.py.example /etc/linux_patching_automation/settings.py

# Edit configuration
sudo nano /etc/linux_patching_automation/settings.py

# Create environment file
sudo tee /etc/linux_patching_automation/environment << EOF
PATCHING_HOME=/opt/linux_patching_automation
PATCHING_USER=patchadmin
PATCHING_DATA=/var/lib/linux_patching_automation
PATCHING_LOGS=/var/log/linux_patching_automation
PATCHING_CONFIG=/etc/linux_patching_automation
PYTHONPATH=/opt/linux_patching_automation
PATH=/opt/linux_patching_automation/venv/bin:\$PATH
EOF
```

#### 6. Create System Service

```bash
# Create systemd service
sudo tee /etc/systemd/system/linux-patching.service << EOF
[Unit]
Description=Linux Patching Automation Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=patchadmin
Group=patchadmin
WorkingDirectory=/opt/linux_patching_automation
Environment=PYTHONPATH=/opt/linux_patching_automation
Environment=PATH=/opt/linux_patching_automation/venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/etc/linux_patching_automation/environment
ExecStart=/opt/linux_patching_automation/venv/bin/python -m cli.patch_manager system health --interval 300
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=linux-patching

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable linux-patching
```

#### 7. Create CLI Wrapper

```bash
# Create CLI wrapper
sudo tee /usr/local/bin/patch-manager << 'EOF'
#!/bin/bash
# Linux Patching Automation CLI Wrapper

# Source environment
if [ -f /etc/linux_patching_automation/environment ]; then
    source /etc/linux_patching_automation/environment
fi

# Activate virtual environment
source /opt/linux_patching_automation/venv/bin/activate

# Run the CLI
exec python /opt/linux_patching_automation/cli/patch_manager.py "$@"
EOF

# Make executable
sudo chmod +x /usr/local/bin/patch-manager

# Create aliases
sudo ln -sf /usr/local/bin/patch-manager /usr/local/bin/patching-cli
sudo ln -sf /usr/local/bin/patch-manager /usr/local/bin/linux-patcher
```

#### 8. Setup Logging

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/linux-patching << EOF
/var/log/linux_patching_automation/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 patchadmin patchadmin
    postrotate
        /bin/systemctl reload linux-patching 2>/dev/null || true
    endscript
}
EOF
```

#### 9. Create Sample Data

```bash
# Create sample server inventory
sudo -u patchadmin tee /var/lib/linux_patching_automation/servers.csv << EOF
Server Name,Host Group,Operating System,Environment,Server Timezone,Location,Primary Owner,Q1 Patch Date,Q1 Patch Time,Q1 Approval Status,Q2 Patch Date,Q2 Patch Time,Q2 Approval Status,Q3 Patch Date,Q3 Patch Time,Q3 Approval Status,Q4 Patch Date,Q4 Patch Time,Q4 Approval Status,Current Quarter Patching Status,Active Status
web01.company.com,web,ubuntu,production,America/New_York,US-East,admin@company.com,2024-01-15,02:00,Pending,2024-04-15,02:00,Pending,2024-07-15,02:00,Pending,2024-10-15,02:00,Pending,Active,Active
db01.company.com,database,centos,production,America/Chicago,US-Central,dba@company.com,2024-01-16,03:00,Pending,2024-04-16,03:00,Pending,2024-07-16,03:00,Pending,2024-10-16,03:00,Pending,Active,Active
app01.company.com,application,ubuntu,production,America/Los_Angeles,US-West,dev@company.com,2024-01-17,04:00,Pending,2024-04-17,04:00,Pending,2024-07-17,04:00,Pending,2024-10-17,04:00,Pending,Active,Active
EOF
```

#### 10. Setup Cron Jobs

```bash
# Create cron jobs for patchadmin user
sudo -u patchadmin tee /tmp/patching-cron << EOF
# Daily pre-check at 2 AM
0 2 * * * /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/cli/patch_manager.py precheck run --auto >> /var/log/linux_patching_automation/cron.log 2>&1

# Weekly report on Monday at 8 AM
0 8 * * 1 /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/cli/patch_manager.py report generate --type weekly >> /var/log/linux_patching_automation/cron.log 2>&1

# Monthly cleanup on first day at 3 AM
0 3 1 * * /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/cli/patch_manager.py system cleanup --days 30 --confirm >> /var/log/linux_patching_automation/cron.log 2>&1
EOF

# Install cron jobs
sudo -u patchadmin crontab /tmp/patching-cron
sudo rm /tmp/patching-cron
```

## Configuration

### Email Settings

Edit `/etc/linux_patching_automation/settings.py`:

```python
# Email Configuration
SMTP_SERVER = 'smtp.company.com'
SMTP_PORT = 587
SMTP_USE_TLS = True
SMTP_USERNAME = 'patching@company.com'
SMTP_PASSWORD = 'your-password'
EMAIL_FROM = 'patching@company.com'
ADMIN_EMAILS = ['admin@company.com']
```

### SSH Configuration

```python
# SSH Configuration
SSH_KEY_PATH = '/home/patchadmin/.ssh/id_rsa'
SSH_DEFAULT_USER = 'patchadmin'
SSH_TIMEOUT = 30
```

### Patching Configuration

```python
# Patching Configuration
MAX_PARALLEL_PATCHES = 5
PATCH_TIMEOUT_MINUTES = 120
PRECHECK_HOURS_BEFORE = 24
ENABLE_AUTO_REBOOT = True
REQUIRE_APPROVAL = True
```

## Testing Installation

### Basic Tests

```bash
# Test CLI
patch-manager --version
patch-manager --help

# Test system health
patch-manager system health

# Test server list
patch-manager server list

# Test email configuration
patch-manager system test-email --to admin@company.com
```

### Connectivity Tests

```bash
# Test SSH connectivity
patch-manager server test --servers web01.company.com

# Test all servers
patch-manager server test --parallel
```

### Service Tests

```bash
# Start service
sudo systemctl start linux-patching

# Check status
sudo systemctl status linux-patching

# View logs
sudo journalctl -u linux-patching -f
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied Errors

```bash
# Fix ownership
sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation
sudo chown -R patchadmin:patchadmin /var/lib/linux_patching_automation
sudo chown -R patchadmin:patchadmin /var/log/linux_patching_automation

# Fix SSH key permissions
sudo -u patchadmin chmod 600 /home/patchadmin/.ssh/id_rsa
sudo -u patchadmin chmod 644 /home/patchadmin/.ssh/id_rsa.pub
```

#### 2. Python Import Errors

```bash
# Reinstall dependencies
sudo -u patchadmin bash -c "
    cd /opt/linux_patching_automation
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt --force-reinstall
"
```

#### 3. Service Won't Start

```bash
# Check service logs
sudo journalctl -u linux-patching -n 50

# Check configuration
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "
    import sys
    sys.path.append('/opt/linux_patching_automation')
    from config.settings import Config
    config = Config()
    print('Configuration loaded successfully')
"
```

#### 4. SSH Connection Issues

```bash
# Test SSH manually
sudo -u patchadmin ssh -i /home/patchadmin/.ssh/id_rsa target-server

# Copy SSH key to target servers
sudo -u patchadmin ssh-copy-id -i /home/patchadmin/.ssh/id_rsa target-server
```

#### 5. Email Issues

```bash
# Test SMTP connection
telnet smtp.company.com 587

# Check email configuration
patch-manager system test-email --to test@company.com
```

### Log Files

- **Main Log**: `/var/log/linux_patching_automation/patching.log`
- **Error Log**: `/var/log/linux_patching_automation/patching_errors.log`
- **Audit Log**: `/var/log/linux_patching_automation/patching_audit.log`
- **Cron Log**: `/var/log/linux_patching_automation/cron.log`
- **Service Log**: `sudo journalctl -u linux-patching`

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
patch-manager --debug system health
```

## Uninstallation

```bash
# Stop service
sudo systemctl stop linux-patching
sudo systemctl disable linux-patching

# Remove service file
sudo rm /etc/systemd/system/linux-patching.service
sudo systemctl daemon-reload

# Remove cron jobs
sudo -u patchadmin crontab -r

# Remove CLI wrapper
sudo rm /usr/local/bin/patch-manager
sudo rm /usr/local/bin/patching-cli
sudo rm /usr/local/bin/linux-patcher

# Remove directories
sudo rm -rf /opt/linux_patching_automation
sudo rm -rf /etc/linux_patching_automation
sudo rm -rf /var/lib/linux_patching_automation
sudo rm -rf /var/log/linux_patching_automation
sudo rm -rf /var/backups/linux_patching_automation

# Remove logrotate config
sudo rm /etc/logrotate.d/linux-patching

# Remove user (optional)
sudo userdel -r patchadmin
```

## Upgrade

```bash
# Backup current installation
sudo tar -czf /var/backups/patching_backup_$(date +%Y%m%d).tar.gz \
    /opt/linux_patching_automation \
    /etc/linux_patching_automation \
    /var/lib/linux_patching_automation

# Stop service
sudo systemctl stop linux-patching

# Pull latest code
cd /opt/linux_patching_automation
sudo -u patchadmin git pull origin main

# Update dependencies
sudo -u patchadmin bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt --upgrade
    pip install -e . --upgrade
"

# Start service
sudo systemctl start linux-patching
```

## Support

For installation issues:
1. Check the troubleshooting section above
2. Review log files for error messages
3. Test individual components (SSH, email, etc.)
4. Contact support at patching@company.com

## Next Steps

After successful installation:
1. Configure email settings
2. Import your server inventory
3. Set up SSH keys for all target servers
4. Test connectivity to all servers
5. Configure approval workflows
6. Schedule your first patching cycle

See the main [README.md](README.md) for usage instructions.