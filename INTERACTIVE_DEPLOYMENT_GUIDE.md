# 🚀 Interactive Deployment Guide

## Overview

The new `deploy_interactive.sh` script provides a user-friendly, interactive installation process that prompts administrators for all configuration settings during deployment. No manual file editing required!

## Prerequisites

Before running the deployment script, ensure you have:

1. **Root access** on the target server
2. **Python 3.8+** installed
3. **Internet connectivity** for package downloads
4. **SMTP credentials** for email notifications
5. **PostgreSQL** installed (optional, for production use)

## Quick Start

```bash
# Download and run the interactive installer
sudo ./deploy_interactive.sh
```

## Configuration Prompts

The script will guide you through the following configuration sections:

### 1️⃣ Basic Configuration

- **Company Name**: Your organization name (used in emails and reports)
- **Installation Directory**: Where to install the application (default: `/opt/linux_patching_automation`)
- **Service User**: System user to run the services (default: `patchadmin`)
- **Log Directory**: Where to store log files (default: `/var/log/patching`)
- **Backup Directory**: Where to store backups (default: `/backup/patching`)

### 2️⃣ Web Portal Configuration

- **Web Portal Port**: Port for the web interface (default: `5001`)
  - The script validates port numbers (1-65535)
  - Automatically configures firewall rules

### 3️⃣ Administrator Configuration

- **Primary Admin Email**: Main administrator email (required)
  - Receives all critical alerts and reports
  - Used as default SMTP username
- **Backup Admin Email**: Secondary admin email (optional)
  - Receives copies of critical alerts

### 4️⃣ Email (SMTP) Configuration

- **SMTP Server**: Mail server hostname (e.g., `smtp.gmail.com`)
- **SMTP Port**: Mail server port (default: `587`)
- **Use TLS**: Enable TLS/STARTTLS encryption (recommended)
- **SMTP Username**: Authentication username (often your email)
- **SMTP Password**: Authentication password (hidden input)

#### Common SMTP Settings:

**Gmail:**
- Server: `smtp.gmail.com`
- Port: `587`
- Use TLS: Yes
- Note: Enable "Less secure app access" or use App Passwords

**Office 365:**
- Server: `smtp.office365.com`
- Port: `587`
- Use TLS: Yes

**SendGrid:**
- Server: `smtp.sendgrid.net`
- Port: `587`
- Use TLS: Yes

### 5️⃣ Database Configuration

Choose between:

1. **SQLite** (Default)
   - Simple file-based database
   - No additional setup required
   - Good for < 1000 servers

2. **PostgreSQL** (Recommended for production)
   - Scalable and robust
   - Better performance for large deployments
   - Additional prompts:
     - Database host and port
     - Database name
     - Database user and password

### 6️⃣ LDAP Configuration (Optional)

If you want to integrate with Active Directory/LDAP:

- **LDAP Server URL**: Full LDAP URL (e.g., `ldap://ldap.company.com`)
- **Base DN**: LDAP base DN (e.g., `dc=company,dc=com`)
- **Bind DN**: Admin bind DN for queries
- **Bind Password**: LDAP admin password

### 7️⃣ Configuration Review

Before installation begins, you'll see a summary of all settings and can confirm or cancel.

## Post-Installation Steps

After successful installation:

### 1. Change Default Admin Password

```bash
# Access the web portal
http://your-server:5001

# Login with:
Username: admin
Password: admin

# Change password immediately!
```

### 2. Configure SSH Access

The installer generates SSH keys for the service user:

```bash
# Copy the displayed public key to all target servers
ssh-copy-id -i /opt/linux_patching_automation/.ssh/id_rsa.pub root@target-server

# Or manually add to target servers:
cat >> ~/.ssh/authorized_keys
[paste the public key]
```

### 3. Import Server Inventory

**Option 1: Web Interface**
- Navigate to Admin Panel → Import CSV
- Upload your servers.csv file

**Option 2: Command Line**
```bash
sudo -u patchadmin /opt/linux_patching_automation/venv/bin/python \
  /opt/linux_patching_automation/main.py --import-csv /path/to/servers.csv
```

### 4. Test Email Configuration

From the Admin Panel:
1. Go to Settings → Email Configuration
2. Click "Send Test Email"
3. Verify receipt at admin email address

### 5. Verify Services

```bash
# Check service status
systemctl status patching-portal patching-monitor

# View logs
journalctl -u patching-portal -f
journalctl -u patching-monitor -f
```

## Configuration Files

All configuration is stored in:

- **Main Settings**: `/opt/linux_patching_automation/config/settings.py`
- **Admin Config**: `/opt/linux_patching_automation/config/admin_config.json`
- **User Database**: `/opt/linux_patching_automation/config/users.json`

## Service Management

```bash
# Start services
systemctl start patching-portal patching-monitor

# Stop services
systemctl stop patching-portal patching-monitor

# Restart services
systemctl restart patching-portal patching-monitor

# Enable auto-start
systemctl enable patching-portal patching-monitor
```

## Troubleshooting

### Email Issues

1. **Gmail**: Enable "Less secure app access" or use App Passwords with 2FA
2. **Corporate SMTP**: May need to whitelist the server IP
3. **Test manually**:
   ```python
   python3
   import smtplib
   server = smtplib.SMTP('smtp.server.com', 587)
   server.starttls()
   server.login('username', 'password')
   ```

### Database Issues

**PostgreSQL Connection Failed:**
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql -h localhost -U patchadmin -d patching_db

# Check PostgreSQL logs
tail -f /var/log/postgresql/*.log
```

### Web Portal Not Accessible

1. **Check firewall**:
   ```bash
   # For firewalld
   firewall-cmd --list-ports
   
   # For ufw
   ufw status
   ```

2. **Check port binding**:
   ```bash
   netstat -tlnp | grep 5001
   ```

3. **Check service logs**:
   ```bash
   journalctl -u patching-portal -n 50
   ```

## Security Recommendations

1. **Change default passwords immediately**
2. **Use HTTPS with SSL certificates**
3. **Restrict database access to localhost**
4. **Enable LDAP for centralized authentication**
5. **Regular backup of configuration and database**
6. **Monitor logs for suspicious activity**

## Backup and Recovery

### Backup Commands
```bash
# Backup configuration
tar -czf patching_config_$(date +%Y%m%d).tar.gz /opt/linux_patching_automation/config/

# Backup database (SQLite)
cp /opt/linux_patching_automation/patching.db /backup/patching/patching_$(date +%Y%m%d).db

# Backup database (PostgreSQL)
pg_dump -U patchadmin patching_db > /backup/patching/patching_$(date +%Y%m%d).sql
```

### Restore Commands
```bash
# Restore configuration
tar -xzf patching_config_20250707.tar.gz -C /

# Restore database (PostgreSQL)
psql -U patchadmin patching_db < /backup/patching/patching_20250707.sql
```

## Support

For issues or questions:
1. Check logs in `/var/log/patching/`
2. Review this guide and troubleshooting section
3. Contact your system administrator

---

**Note**: This interactive installer significantly simplifies the deployment process by eliminating the need to manually edit configuration files. All settings are collected upfront and validated before installation begins.