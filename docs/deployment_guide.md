# Linux OS Patching Automation - Deployment and Operations Guide

## Table of Contents
1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Quarter System](#quarter-system)
7. [Timezone Handling](#timezone-handling)
8. [Web Portal](#web-portal)
9. [Email Notifications](#email-notifications)
10. [Database Management](#database-management)
11. [Monitoring and Logging](#monitoring-and-logging)
12. [Backup and Recovery](#backup-and-recovery)
13. [Troubleshooting](#troubleshooting)
14. [Security Considerations](#security-considerations)
15. [Maintenance Procedures](#maintenance-procedures)

## Overview

The Linux OS Patching Automation system is a comprehensive solution for managing and automating the patching process for Linux servers. It provides a structured approach to scheduling, executing, and validating patches across multiple quarters, with support for various timezones and server configurations.

### Key Features

- Automated patching workflow
- Custom quarter definitions
- Timezone detection and conversion
- Email notifications for patch scheduling and status
- Pre-patch and post-patch validation
- Web portal for schedule management
- Comprehensive logging and reporting

## System Requirements

### Server Requirements

- Linux OS (RHEL/CentOS 7+ or Ubuntu 18.04+)
- Python 3.8 or higher
- Minimum 2GB RAM
- 10GB free disk space
- Network connectivity to managed servers
- SMTP server for email notifications

### Client Requirements

- SSH access to target servers
- SNMP access for timezone detection
- sudo privileges for patching operations

## Architecture

The system uses a modular architecture with the following components:

1. **Web Portal**: Flask-based web interface for schedule management
2. **Database**: SQLite or PostgreSQL for storing server and patch information
3. **Scripts**: Python scripts for each stage of the patching process
4. **Bash Scripts**: Shell scripts for executing system commands on target servers
5. **Email System**: Notification system for sending alerts and updates
6. **Monitoring**: Continuous monitoring of the patching process

### Process Flow

1. **Monthly Notice**: Send quarterly patch scheduling notice
2. **Reminders**: Send weekly and daily reminders
3. **Pre-checks**: Validate server readiness before patching
4. **Scheduling**: Schedule patching jobs
5. **Patch Execution**: Apply patches to target servers
6. **Validation**: Verify successful patch application
7. **Post-Patch**: Validate system stability after patching
8. **Completion Notice**: Send notification of completion

## Installation

### Automated Installation

The simplest way to install the system is using the provided deployment script:

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

This script will:
1. Create necessary users and directories
2. Install dependencies
3. Set up the application
4. Configure systemd services
5. Set up cron jobs
6. Initialize the database
7. Start the services

### Manual Installation

For manual installation, follow these steps:

1. Create the installation directory:
   ```bash
   sudo mkdir -p /opt/linux_patching_automation
   ```

2. Create the service user:
   ```bash
   sudo useradd -r -s /bin/bash -d /opt/linux_patching_automation -m patchadmin
   ```

3. Copy application files:
   ```bash
   sudo cp -r * /opt/linux_patching_automation/
   ```

4. Set permissions:
   ```bash
   sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation
   ```

5. Create virtual environment:
   ```bash
   sudo -u patchadmin python3 -m venv /opt/linux_patching_automation/venv
   ```

6. Install dependencies:
   ```bash
   sudo -u patchadmin /opt/linux_patching_automation/venv/bin/pip install -r /opt/linux_patching_automation/requirements.txt
   ```

7. Initialize database:
   ```bash
   sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python /opt/linux_patching_automation/main.py --init-db
   ```

8. Create systemd services (see deploy.sh for examples)

9. Start services:
   ```bash
   sudo systemctl start patching-portal.service
   sudo systemctl start patching-monitor.service
   ```

## Configuration

### Main Configuration

The main configuration file is located at `/etc/patching/patching.conf`. This file contains environment-specific settings such as:

- Installation directories
- Service user
- SMTP server details
- Default email addresses

### Application Configuration

Application settings are defined in `config/settings.py`:

- Database configuration
- Email settings
- Patching parameters
- Quarter definitions
- Timing configurations
- File paths

### Server Inventory

Server information is stored in `data/servers.csv` with the following fields:

- Server Name
- Server Timezone
- Patch dates and times for each quarter
- Current patching status
- Owner information
- Host group and location

## Quarter System

This system uses a custom quarter definition:

- **Q1**: November to January
- **Q2**: February to April
- **Q3**: May to July
- **Q4**: August to October

This quarter system is defined in `config/settings.py`:

```python
QUARTERS = {
    '1': {'name': 'Q1', 'months': [11, 12, 1]},   # Nov to Jan
    '2': {'name': 'Q2', 'months': [2, 3, 4]},     # Feb to April
    '3': {'name': 'Q3', 'months': [5, 6, 7]},     # May to July
    '4': {'name': 'Q4', 'months': [8, 9, 10]}     # August to October
}
```

### Quarter Determination

The current quarter is determined by the month:

```python
def get_current_quarter():
    current_month = datetime.now().month
    for quarter, details in Config.QUARTERS.items():
        if current_month in details['months']:
            return quarter
    return '1'  # Default to Q1
```

## Timezone Handling

The system uses advanced timezone handling to:

1. Detect server timezones using SNMP
2. Convert between timezones for scheduling
3. Display times in appropriate local format

### Timezone Detection

Server timezones are detected using the following methods:

1. SNMP query for system time (primary method)
2. SSH to server and query using `timedatectl`
3. Reading `/etc/timezone` file
4. Analyzing output from `date` command

### Timezone Conversion

Times are converted between timezones using the `pytz` library:

```python
def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
    # Normalize timezone names
    from_tz = self.get_canonical_timezone(from_tz)
    to_tz = self.get_canonical_timezone(to_tz)
    
    # Get timezone objects
    from_timezone = pytz.timezone(from_tz)
    to_timezone = pytz.timezone(to_tz)
    
    # Localize if naive datetime
    if dt.tzinfo is None:
        dt = from_timezone.localize(dt)
    
    # Convert timezone
    converted_dt = dt.astimezone(to_timezone)
    return converted_dt
```

## Web Portal

The web portal provides a user interface for managing patching schedules.

### Access

The web portal is available at `http://server:5000/` by default.

### Authentication

The portal uses Flask-Login for authentication. In a production environment, this should be integrated with your company's authentication system (LDAP, SSO, etc.).

### Features

- View server inventory
- Update patching schedules
- Monitor patching status
- Visualize quarterly schedules
- Timezone information display

## Email Notifications

The system sends several types of email notifications:

1. **Monthly Notice**: Sent at the beginning of each quarter
2. **Weekly Reminder**: Sent on Mondays for servers scheduled that week
3. **24-Hour Reminder**: Sent the day before patching
4. **Pre-check Alert**: Sent if pre-checks fail
5. **Completion Notice**: Sent after patching completes
6. **Failure Notice**: Sent if patching fails

### Email Templates

Email templates are stored in the `templates/` directory as HTML files:

- `monthly_notice.html`
- `weekly_reminder.html`
- `daily_reminder.html`
- `completion_notice.html`

### SMTP Configuration

SMTP settings are configured in `config/settings.py`:

```python
# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.company.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'patching@company.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'email_password')
```

## Database Management

The system can use either SQLite or PostgreSQL for data storage.

### Tables

- `servers`: Server information and schedules
- `patch_history`: Historical patching data
- `notifications`: Email notification records
- `precheck_results`: Pre-check validation results
- `configuration`: System configuration

### Backup

The database (or CSV file) is automatically backed up daily to the backup directory.

## Monitoring and Logging

### Logs

Logs are stored in `/var/log/patching/` with separate log files for each component:

- `main.log`: Main application log
- `precheck.log`: Pre-check operations
- `scheduler.log`: Scheduling operations
- `patch_validator.log`: Patch validation
- `post_patch.log`: Post-patch validation
- `email_sender.log`: Email operations
- `monitor.log`: Continuous monitoring

### Log Rotation

Logs are automatically rotated using logrotate with the following policy:

- Daily rotation
- 30 days retention
- Compression of old logs

## Backup and Recovery

### Automated Backups

The system performs the following backups:

1. Daily backup of server inventory CSV
2. Backup before any schema changes
3. Backup of configuration files during updates

### Recovery Procedure

To recover from a failure:

1. Reinstall the application if necessary
2. Restore the latest database backup
3. Restore configuration files
4. Verify services are running

## Troubleshooting

### Installation Issues

1. **Permission denied errors during installation**
   ```
   [Errno 13] Permission denied: '/opt/linux_patching_automation/venv'
   ```
   
   **Solution:**
   - Ensure the /opt directory is writable: `sudo chmod 755 /opt`
   - Fix ownership of the installation directory: 
     ```
     sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation
     ```
   - Manually create the venv directory with correct permissions:
     ```
     sudo mkdir -p /opt/linux_patching_automation/venv
     sudo chown patchadmin:patchadmin /opt/linux_patching_automation/venv
     sudo -u patchadmin python3 -m venv /opt/linux_patching_automation/venv
     ```
   - If all else fails, use the manual installation script: `sudo ./manual_install.sh`

2. **Python virtual environment errors**
   ```
   Error: Command '['/opt/linux_patching_automation/venv/bin/python3', '-m', 'ensurepip', '--upgrade', '--default-pip']' returned non-zero exit status 1
   ```
   
   **Solution:**
   - Install Python venv package: 
     ```
     # Debian/Ubuntu
     sudo apt-get install python3-venv
     
     # RHEL/CentOS
     sudo yum install python3-devel
     ```
   - Try creating venv without pip and then install pip:
     ```
     sudo -u patchadmin python3 -m venv /opt/linux_patching_automation/venv --without-pip
     sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -m ensurepip
     ```

3. **PostgreSQL dependency issues**
   ```
   Error: pg_config executable not found.
   pg_config is required to build psycopg2 from source.
   ```
   
   **Solution:**
   - Install PostgreSQL development packages:
     ```
     # Debian/Ubuntu
     sudo apt-get install libpq-dev postgresql-dev
     
     # RHEL/CentOS
     sudo yum install postgresql-devel
     ```
   - Or use SQLite instead (for small deployments):
     ```
     sudo -u patchadmin /opt/linux_patching_automation/venv/bin/pip install -r /opt/linux_patching_automation/requirements_sqlite.txt
     ```
   - Modify the database configuration in settings.py to use SQLite instead of PostgreSQL

### Runtime Issues

1. **Email notifications not being sent**
   - Check SMTP configuration
   - Verify email templates exist
   - Check email logs

2. **Pre-checks failing**
   - Verify SSH connectivity to servers
   - Check disk space on servers
   - Verify SNMP access

3. **Web portal not accessible**
   - Check if service is running
   - Verify firewall allows access to port 5000
   - Check Flask logs

4. **Patching not starting on schedule**
   - Verify cron jobs are set up correctly
   - Check scheduler logs
   - Verify at jobs are created

### Diagnostic Commands

```bash
# Check service status
systemctl status patching-portal
systemctl status patching-monitor

# View logs
tail -f /var/log/patching/main.log

# Check cron jobs
sudo -u patchadmin crontab -l

# Test database access
sqlite3 /opt/linux_patching_automation/patching.db .tables

# Test email sending
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python -c "from utils.email_sender import EmailSender; EmailSender().send_email('admin@company.com', 'Test', 'Test message')"
```

## Security Considerations

### Best Practices

1. Use a dedicated service account with limited privileges
2. Secure SMTP credentials
3. Implement proper authentication for the web portal
4. Use SSH keys instead of passwords
5. Restrict sudo access to only necessary commands
6. Secure database access

### SSH Keys

Generate and distribute SSH keys for the service user:

```bash
sudo -u patchadmin ssh-keygen -t rsa -b 4096
sudo -u patchadmin ssh-copy-id -i /opt/linux_patching_automation/.ssh/id_rsa.pub user@server
```

## Maintenance Procedures

### Updates

To update the application:

1. Stop services:
   ```bash
   sudo systemctl stop patching-portal
   sudo systemctl stop patching-monitor
   ```

2. Backup the current installation:
   ```bash
   sudo cp -r /opt/linux_patching_automation /opt/linux_patching_automation.bak
   ```

3. Update files:
   ```bash
   sudo rsync -av --exclude '.git' /path/to/new/files/ /opt/linux_patching_automation/
   ```

4. Update dependencies if needed:
   ```bash
   sudo -u patchadmin /opt/linux_patching_automation/venv/bin/pip install -r /opt/linux_patching_automation/requirements.txt
   ```

5. Restart services:
   ```bash
   sudo systemctl start patching-portal
   sudo systemctl start patching-monitor
   ```

### Quarterly Maintenance

At the end of each quarter:

1. Archive patch history
2. Reset server statuses for the new quarter
3. Verify server inventory is up to date
4. Test email templates
5. Run a system health check
