# 📚 Linux Patching Automation - Administrator Technical Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [CLI Administration Guide](#cli-administration-guide)
3. [Web Portal Administration Guide](#web-portal-administration-guide)
4. [Database Management](#database-management)
5. [Security Management](#security-management)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [API Reference](#api-reference)
8. [Maintenance Procedures](#maintenance-procedures)

---

## System Overview

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Portal (Flask)                        │
│                    Port: 5001 (default)                      │
├─────────────────────────────────────────────────────────────┤
│                    CLI Interface (main.py)                   │
├─────────────────────────────────────────────────────────────┤
│                    Backend Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Monitor    │  │  Scheduler   │  │ Email Engine │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   SQLite/    │  │     CSV      │  │     Logs     │     │
│  │  PostgreSQL  │  │    Files     │  │    Files     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Service Components

| Service | Purpose | Default Schedule |
|---------|---------|------------------|
| patching-portal | Web interface | Always running |
| patching-monitor | Continuous monitoring | Always running |
| patching-daily | Daily tasks | 9:00 AM daily |
| patching-monthly | Monthly notices | 1st of month |

---

## CLI Administration Guide

### Basic Command Structure

```bash
python main.py [OPTIONS] [ARGUMENTS]
```

### Core Administrative Commands

#### 1. Database Management

```bash
# Initialize database
python main.py --init-db

# Backup database
python main.py --backup-db

# Restore database
python main.py --restore-db backup_file.sql

# Database statistics
python main.py --db-stats
```

#### 2. Server Management

```bash
# Import servers from CSV
python main.py --import-csv servers.csv

# Export current server list
python main.py --export-csv output.csv

# List all servers
python main.py --list-servers

# Search servers
python main.py --search-server "web*"

# Update server details
python main.py --update-server SERVER_NAME --field primary_owner --value "admin@company.com"
```

#### 3. Patching Operations

```bash
# Run specific workflow step
python main.py --step 0  # Send approval requests
python main.py --step 1  # Send monthly notices
python main.py --step 2  # Send reminders
python main.py --step 3  # Run pre-checks
python main.py --step 4  # Execute patches
python main.py --step 5  # Validate patches
python main.py --step 6  # Post-patch validation

# Run for specific quarter
python main.py --step 1 --quarter 3

# Dry run mode (no actual changes)
python main.py --step 4 --dry-run

# Force execution (bypass time checks)
python main.py --step 4 --force
```

#### 4. Approval Management

```bash
# Approve single server
python main.py --approve-server SERVER_NAME --quarter 3

# Approve multiple servers
python main.py --approve-servers server1,server2,server3 --quarter 3

# Approve by owner
python main.py --approve-by-owner "admin@company.com" --quarter 3

# Approve by host group
python main.py --approve-by-group "web_servers" --quarter 3

# Auto-approve based on criteria
python main.py --auto-approve --criteria "environment=dev" --quarter 3

# List pending approvals
python main.py --list-pending --quarter 3
```

#### 5. Scheduling Operations

```bash
# Run intelligent scheduling
python main.py --intelligent-schedule --quarter 3

# Schedule specific server
python main.py --schedule-server SERVER_NAME --date "2025-07-15" --time "20:00"

# Bulk scheduling from file
python main.py --bulk-schedule schedule.csv

# View current schedule
python main.py --view-schedule --quarter 3

# Export schedule
python main.py --export-schedule --quarter 3 --format csv
```

#### 6. Reporting Commands

```bash
# Generate reports
python main.py --generate-report summary --quarter 3
python main.py --generate-report detailed --quarter 3
python main.py --generate-report compliance --quarter 3

# Email reports
python main.py --email-report summary --recipients "admin@company.com,manager@company.com"

# Export reports
python main.py --export-report summary --format pdf --output report.pdf
python main.py --export-report detailed --format excel --output report.xlsx
```

#### 7. Email Management

```bash
# Send test email
python main.py --test-email admin@company.com

# Resend notifications
python main.py --resend-approval-requests --quarter 3
python main.py --resend-reminders --quarter 3

# List email history
python main.py --email-history --days 7

# Configure email settings
python main.py --config-smtp --server smtp.gmail.com --port 587 --tls
```

#### 8. User Management

```bash
# Create user
python main.py --create-user --username john --email john@company.com --role admin

# Update user
python main.py --update-user john --role user

# Reset password
python main.py --reset-password john

# List users
python main.py --list-users

# Delete user
python main.py --delete-user john
```

#### 9. System Maintenance

```bash
# Clean old logs
python main.py --clean-logs --days 30

# Verify system health
python main.py --health-check

# Update system
python main.py --self-update

# Export configuration
python main.py --export-config

# Import configuration
python main.py --import-config config.json
```

### Advanced CLI Features

#### Batch Operations

```bash
# Batch approve servers from file
python main.py --batch-approve servers_to_approve.txt --quarter 3

# Batch update server attributes
python main.py --batch-update updates.csv

# Batch schedule servers
python main.py --batch-schedule schedule_list.csv
```

#### Filtering and Queries

```bash
# Filter servers by criteria
python main.py --list-servers --filter "host_group=web_servers,status=pending"

# Complex queries
python main.py --query "SELECT * FROM servers WHERE patch_date < '2025-08-01' AND approval_status = 'Pending'"

# Export filtered results
python main.py --list-servers --filter "status=failed" --export failed_servers.csv
```

#### Automation Scripts

```bash
# Create automation script
python main.py --create-automation "weekly_approval" --schedule "0 9 * * MON"

# List automation scripts
python main.py --list-automations

# Run automation manually
python main.py --run-automation "weekly_approval"
```

---

## Web Portal Administration Guide

### Accessing the Admin Panel

1. Navigate to: `http://server:5001/admin`
2. Login with admin credentials
3. Admin panel provides enhanced features

### Admin Dashboard Features

#### 1. System Overview

- **Real-time Statistics**
  - Total servers managed
  - Pending approvals
  - Scheduled patches
  - Completed patches
  - Failed patches

- **System Health**
  - Service status
  - Database connectivity
  - Email system status
  - Disk space usage
  - CPU/Memory usage

#### 2. Server Management

**Bulk Operations:**
- Import/Export CSV
- Batch approve servers
- Bulk schedule updates
- Mass email notifications

**Server Actions:**
- Edit server details
- Change ownership
- Update schedules
- View patch history
- Force patch execution

#### 3. User Management

**User Operations:**
- Create/Edit/Delete users
- Reset passwords
- Assign roles
- View activity logs

**Role Permissions:**
| Role | View | Approve | Schedule | Admin |
|------|------|---------|----------|--------|
| admin | ✓ | ✓ | ✓ | ✓ |
| user | ✓ | ✓ | ✓ | ✗ |
| approver | ✓ | ✓ | ✗ | ✗ |
| readonly | ✓ | ✗ | ✗ | ✗ |

#### 4. Configuration Management

**Email Settings:**
- SMTP configuration
- Test email functionality
- Email templates management
- Notification preferences

**System Settings:**
- Patching windows
- Max servers per hour
- Freeze periods
- Custom quarters

**LDAP Configuration:**
- Server settings
- Base DN configuration
- Bind credentials
- Group mappings

#### 5. Reports Dashboard

**Available Reports:**
- Executive Summary
- Detailed Server Report
- Compliance Report
- Patch History
- Failure Analysis
- SLA Metrics

**Report Features:**
- Real-time generation
- Multiple export formats (PDF, Excel, CSV)
- Scheduled report delivery
- Custom report builder

#### 6. Intelligent Scheduling

**Features:**
- AI-powered load balancing
- Dependency management
- Blackout period handling
- Resource optimization
- Conflict resolution

**Configuration:**
- Priority groups
- Time slot preferences
- Server dependencies
- Maintenance windows

#### 7. Monitoring Dashboard

**Real-time Monitoring:**
- Active patches
- Server status
- Queue status
- Error alerts
- Performance metrics

**Historical Data:**
- Patch success rates
- Average duration
- Peak load times
- Failure patterns

### Web Portal Advanced Features

#### 1. API Access

```javascript
// Authentication
POST /api/auth/login
{
  "username": "admin",
  "password": "password"
}

// Get server list
GET /api/servers
Authorization: Bearer <token>

// Approve server
POST /api/servers/{server_name}/approve
{
  "quarter": 3,
  "approved_by": "admin"
}

// Schedule patch
POST /api/servers/{server_name}/schedule
{
  "date": "2025-07-15",
  "time": "20:00"
}
```

#### 2. Bulk Import Templates

**CSV Format:**
```csv
Server Name,Host Group,Primary Owner,Secondary Owner,Location,OS,Environment
web01.company.com,web_servers,admin@company.com,backup@company.com,DC1,RHEL 8,Production
web02.company.com,web_servers,admin@company.com,backup@company.com,DC1,RHEL 8,Production
```

#### 3. Custom Dashboards

- Create custom views
- Add widgets
- Configure alerts
- Export configurations

---

## Database Management

### SQLite Administration

```bash
# Backup database
sqlite3 patching.db ".backup patching_backup.db"

# Vacuum database (optimize)
sqlite3 patching.db "VACUUM;"

# Check integrity
sqlite3 patching.db "PRAGMA integrity_check;"

# Export to SQL
sqlite3 patching.db .dump > backup.sql
```

### PostgreSQL Administration

```sql
-- Create backup
pg_dump -U patchadmin -h localhost patching_db > backup.sql

-- Restore backup
psql -U patchadmin -h localhost patching_db < backup.sql

-- Analyze performance
EXPLAIN ANALYZE SELECT * FROM servers WHERE status = 'pending';

-- Vacuum and analyze
VACUUM ANALYZE servers;
```

### Database Schema

```sql
-- Servers table
CREATE TABLE servers (
    id INTEGER PRIMARY KEY,
    server_name VARCHAR(255) UNIQUE NOT NULL,
    host_group VARCHAR(100),
    primary_owner VARCHAR(255),
    secondary_owner VARCHAR(255),
    os_type VARCHAR(50),
    environment VARCHAR(50),
    q1_approval_status VARCHAR(50),
    q1_patch_date DATE,
    q1_patch_time TIME,
    q2_approval_status VARCHAR(50),
    q2_patch_date DATE,
    q2_patch_time TIME,
    q3_approval_status VARCHAR(50),
    q3_patch_date DATE,
    q3_patch_time TIME,
    q4_approval_status VARCHAR(50),
    q4_patch_date DATE,
    q4_patch_time TIME,
    current_status VARCHAR(50),
    last_updated TIMESTAMP
);

-- Patch history table
CREATE TABLE patch_history (
    id INTEGER PRIMARY KEY,
    server_name VARCHAR(255),
    patch_date DATE,
    patch_time TIME,
    quarter INTEGER,
    year INTEGER,
    status VARCHAR(50),
    details TEXT,
    created_at TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    created_at TIMESTAMP,
    last_login TIMESTAMP
);
```

---

## Security Management

### Access Control

#### SSH Key Management

```bash
# Generate SSH keys for service user
sudo -u patchadmin ssh-keygen -t rsa -b 4096

# Deploy keys to target servers
sudo -u patchadmin ssh-copy-id root@target-server

# Test connectivity
sudo -u patchadmin ssh target-server "echo 'Connection successful'"
```

#### SSL/TLS Configuration

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# Configure Flask for HTTPS
# In config/settings.py:
SSL_CERT = '/path/to/cert.pem'
SSL_KEY = '/path/to/key.pem'
```

### Audit Logging

```python
# Enable audit logging in settings.py
AUDIT_LOG_ENABLED = True
AUDIT_LOG_FILE = '/var/log/patching/audit.log'
AUDIT_EVENTS = ['login', 'approval', 'schedule_change', 'patch_execution']
```

### Security Best Practices

1. **Password Policy**
   - Minimum 12 characters
   - Complexity requirements
   - Regular rotation
   - No password reuse

2. **Session Management**
   - 30-minute timeout
   - Secure session cookies
   - CSRF protection

3. **Network Security**
   - Firewall rules
   - VPN access only
   - IP whitelisting

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Email Delivery Issues

**Symptoms:** Emails not being received

**Diagnostics:**
```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.server.com', 587)
server.starttls()
server.login('user', 'pass')
print('Success')
"

# Check email logs
tail -f /var/log/patching/email_sender.log
```

**Solutions:**
- Verify SMTP credentials
- Check firewall rules for port 587/465
- Enable "Less secure apps" for Gmail
- Use app-specific passwords

#### 2. Database Connection Issues

**Symptoms:** "Database connection failed"

**Diagnostics:**
```bash
# PostgreSQL
psql -h localhost -U patchadmin -d patching_db -c "SELECT 1;"

# Check PostgreSQL logs
tail -f /var/log/postgresql/*.log

# SQLite permissions
ls -la /opt/linux_patching_automation/patching.db
```

**Solutions:**
- Verify database credentials
- Check database service status
- Ensure proper file permissions
- Review connection strings

#### 3. Web Portal Not Accessible

**Symptoms:** Cannot access web interface

**Diagnostics:**
```bash
# Check service status
systemctl status patching-portal

# Check port binding
netstat -tlnp | grep 5001

# Check logs
journalctl -u patching-portal -n 100

# Test locally
curl http://localhost:5001
```

**Solutions:**
- Restart web service
- Check firewall rules
- Verify port availability
- Review Flask error logs

#### 4. SSH Connection Failures

**Symptoms:** Cannot connect to target servers

**Diagnostics:**
```bash
# Test SSH connectivity
sudo -u patchadmin ssh -v target-server

# Check SSH keys
sudo -u patchadmin ls -la ~/.ssh/

# Verify key permissions
sudo -u patchadmin stat ~/.ssh/id_rsa
```

**Solutions:**
- Deploy SSH public keys
- Fix key permissions (600)
- Check SSH service on targets
- Verify network connectivity

#### 5. Patch Execution Failures

**Symptoms:** Patches fail to execute

**Diagnostics:**
```bash
# Check patch logs
tail -f /var/log/patching/patch_execution.log

# Verify sudo permissions on target
sudo -u patchadmin ssh target-server "sudo -n yum check-update"

# Check disk space
sudo -u patchadmin ssh target-server "df -h"
```

**Solutions:**
- Ensure sudo NOPASSWD access
- Check disk space (>20% free)
- Verify package manager locks
- Review pre-check failures

### Debug Mode

Enable debug logging:

```python
# In config/settings.py
LOG_LEVEL = 'DEBUG'
DEBUG_MODE = True

# Or via environment
export PATCHING_DEBUG=1
python main.py --step 3
```

### Performance Tuning

#### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_servers_status ON servers(current_status);
CREATE INDEX idx_servers_owner ON servers(primary_owner);
CREATE INDEX idx_patch_history_date ON patch_history(patch_date);

-- PostgreSQL specific
ALTER TABLE servers SET (autovacuum_vacuum_scale_factor = 0.1);
```

#### Application Tuning

```python
# In config/settings.py
# Increase worker threads
WORKER_THREADS = 10

# Batch processing size
BATCH_SIZE = 50

# Cache configuration
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = 'redis://localhost:6379/0'
```

---

## API Reference

### Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

Response:
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "username": "admin",
    "email": "admin@company.com",
    "role": "admin"
  }
}
```

### Server Management

#### List Servers
```http
GET /api/servers?page=1&per_page=50&filter=status:pending
Authorization: Bearer <token>

Response:
{
  "servers": [...],
  "total": 150,
  "page": 1,
  "pages": 3
}
```

#### Get Server Details
```http
GET /api/servers/{server_name}
Authorization: Bearer <token>

Response:
{
  "server_name": "web01.company.com",
  "host_group": "web_servers",
  "status": "pending",
  ...
}
```

#### Update Server
```http
PUT /api/servers/{server_name}
Authorization: Bearer <token>
Content-Type: application/json

{
  "primary_owner": "newowner@company.com",
  "q3_patch_date": "2025-07-15",
  "q3_patch_time": "20:00"
}
```

### Reporting API

#### Generate Report
```http
POST /api/reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "summary",
  "quarter": 3,
  "format": "pdf",
  "filters": {
    "host_group": "web_servers",
    "status": "completed"
  }
}

Response:
{
  "report_id": "rpt_123456",
  "status": "generating",
  "url": "/api/reports/download/rpt_123456"
}
```

### Scheduling API

#### Intelligent Schedule
```http
POST /api/schedule/intelligent
Authorization: Bearer <token>
Content-Type: application/json

{
  "quarter": 3,
  "servers": ["web01", "web02", "db01"],
  "constraints": {
    "max_per_hour": 5,
    "window_start": "20:00",
    "window_end": "00:00"
  }
}
```

---

## Maintenance Procedures

### Daily Maintenance

```bash
# Check service health
/opt/linux_patching_automation/scripts/daily_health_check.sh

# Verify backups
ls -la /backup/patching/daily/

# Review error logs
grep ERROR /var/log/patching/*.log | tail -20
```

### Weekly Maintenance

```bash
# Database maintenance
python main.py --db-maintenance

# Clean old logs
python main.py --clean-logs --days 30

# Generate weekly report
python main.py --generate-report weekly --email admin@company.com
```

### Monthly Maintenance

```bash
# Full system backup
/opt/linux_patching_automation/scripts/full_backup.sh

# Update system
cd /opt/linux_patching_automation
git pull
pip install -r requirements.txt --upgrade

# Audit user access
python main.py --audit-users

# Performance analysis
python main.py --performance-report
```

### Disaster Recovery

#### Backup Procedures

```bash
#!/bin/bash
# backup_patching_system.sh

BACKUP_DIR="/backup/patching/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup application
tar -czf $BACKUP_DIR/app_backup.tar.gz /opt/linux_patching_automation/

# Backup database
if [ -f /opt/linux_patching_automation/patching.db ]; then
    cp /opt/linux_patching_automation/patching.db $BACKUP_DIR/
else
    pg_dump -U patchadmin patching_db > $BACKUP_DIR/patching_db.sql
fi

# Backup configuration
tar -czf $BACKUP_DIR/config_backup.tar.gz /etc/patching/

# Backup logs
tar -czf $BACKUP_DIR/logs_backup.tar.gz /var/log/patching/
```

#### Restore Procedures

```bash
#!/bin/bash
# restore_patching_system.sh

RESTORE_DIR="/backup/patching/20250707"

# Stop services
systemctl stop patching-portal patching-monitor

# Restore application
tar -xzf $RESTORE_DIR/app_backup.tar.gz -C /

# Restore database
if [ -f $RESTORE_DIR/patching.db ]; then
    cp $RESTORE_DIR/patching.db /opt/linux_patching_automation/
else
    psql -U patchadmin patching_db < $RESTORE_DIR/patching_db.sql
fi

# Restore configuration
tar -xzf $RESTORE_DIR/config_backup.tar.gz -C /

# Start services
systemctl start patching-portal patching-monitor
```

---

## Appendix

### Environment Variables

```bash
# System configuration
PATCHING_ENV=production
PATCHING_DEBUG=0
PATCHING_LOG_LEVEL=INFO

# Database
PATCHING_DB_TYPE=postgresql
PATCHING_DB_HOST=localhost
PATCHING_DB_PORT=5432
PATCHING_DB_NAME=patching_db
PATCHING_DB_USER=patchadmin
PATCHING_DB_PASSWORD=secure_password

# Email
PATCHING_SMTP_SERVER=smtp.company.com
PATCHING_SMTP_PORT=587
PATCHING_SMTP_USERNAME=patching@company.com
PATCHING_SMTP_PASSWORD=email_password
```

### Log File Locations

| Log File | Purpose | Rotation |
|----------|---------|----------|
| /var/log/patching/main.log | Main application log | Daily, 30 days |
| /var/log/patching/web.log | Web portal log | Daily, 30 days |
| /var/log/patching/monitor.log | Monitor service log | Daily, 30 days |
| /var/log/patching/email.log | Email operations | Daily, 30 days |
| /var/log/patching/audit.log | Security audit log | Daily, 90 days |
| /var/log/patching/patch_execution.log | Patch execution details | Daily, 60 days |

### Service Files

- `/etc/systemd/system/patching-portal.service`
- `/etc/systemd/system/patching-monitor.service`
- `/etc/systemd/system/patching-daily.timer`
- `/etc/systemd/system/patching-monthly.timer`

### Configuration Files

- `/opt/linux_patching_automation/config/settings.py`
- `/opt/linux_patching_automation/config/admin_config.json`
- `/opt/linux_patching_automation/config/users.json`
- `/etc/patching/patching.conf`

---

**Document Version:** 1.0  
**Last Updated:** July 2025  
**Maintained By:** System Administration Team