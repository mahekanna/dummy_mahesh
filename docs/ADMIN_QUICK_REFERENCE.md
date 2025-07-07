# 🚀 Administrator Quick Reference Guide

## Daily Operations Checklist

### Morning Tasks (9:00 AM)
```bash
# 1. Check system health
systemctl status patching-portal patching-monitor

# 2. Review overnight patches
python main.py --list-servers --filter "status=completed,date=today"

# 3. Check for failures
python main.py --list-servers --filter "status=failed"

# 4. Review pending approvals
python main.py --list-pending --quarter $(date +%q)
```

### Web Portal Quick Access
- **Dashboard**: `http://server:5001/`
- **Admin Panel**: `http://server:5001/admin`
- **Reports**: `http://server:5001/reports`
- **API Docs**: `http://server:5001/api/docs`

---

## Most Common CLI Commands

### 🔍 Server Queries
```bash
# List all servers
python main.py --list-servers

# Search specific servers
python main.py --search-server "web*"

# Filter by status
python main.py --list-servers --filter "status=pending"

# Export to CSV
python main.py --export-csv servers_export.csv
```

### ✅ Approval Operations
```bash
# Approve single server
python main.py --approve-server web01.company.com --quarter 3

# Approve by owner
python main.py --approve-by-owner "admin@company.com" --quarter 3

# Approve by group
python main.py --approve-by-group "web_servers" --quarter 3

# Bulk approve from file
python main.py --batch-approve servers.txt --quarter 3
```

### 📅 Scheduling
```bash
# Run intelligent scheduling
python main.py --intelligent-schedule --quarter 3

# Schedule specific server
python main.py --schedule-server web01 --date "2025-07-15" --time "20:00"

# View current schedule
python main.py --view-schedule --quarter 3
```

### 📊 Reports
```bash
# Generate summary report
python main.py --generate-report summary --quarter 3

# Email report to admins
python main.py --email-report summary --recipients "admin@company.com"

# Export detailed report
python main.py --export-report detailed --format excel --output report.xlsx
```

### 🚨 Emergency Commands
```bash
# Stop all patching immediately
systemctl stop patching-monitor

# Check failed patches
python main.py --list-servers --filter "status=failed" --export failed.csv

# Resend notifications
python main.py --resend-reminders --quarter 3

# Force patch execution (bypass time checks)
python main.py --step 4 --force --server web01
```

---

## Web Portal Quick Navigation

### Admin Dashboard Shortcuts

| Action | URL Path | Keyboard Shortcut |
|--------|----------|-------------------|
| Dashboard | `/` | `Alt+D` |
| Server List | `/servers` | `Alt+S` |
| Reports | `/reports` | `Alt+R` |
| Admin Panel | `/admin` | `Alt+A` |
| Schedule View | `/schedule` | `Alt+C` |
| User Management | `/admin/users` | `Alt+U` |

### Quick Actions

#### From Server List Page:
- **Approve Selected**: Select servers → Actions → Approve
- **Bulk Schedule**: Select servers → Actions → Schedule
- **Export Selection**: Select servers → Actions → Export CSV

#### From Reports Page:
- **Quick Generate**: Select report type → Generate
- **Email Report**: Generate → Email icon
- **Download**: Generate → Download button

---

## Service Management

### Start/Stop Services
```bash
# Start all services
systemctl start patching-portal patching-monitor

# Stop all services
systemctl stop patching-portal patching-monitor

# Restart web portal only
systemctl restart patching-portal

# Check service status
systemctl status patching-portal patching-monitor
```

### View Logs
```bash
# Real-time web portal logs
journalctl -u patching-portal -f

# Monitor service logs
journalctl -u patching-monitor -f

# Last 100 lines of all logs
journalctl -u patching-portal -u patching-monitor -n 100

# Logs from today
journalctl -u patching-portal --since today
```

---

## Database Quick Commands

### SQLite
```bash
# Quick backup
cp /opt/linux_patching_automation/patching.db /backup/patching_$(date +%Y%m%d).db

# Query servers
sqlite3 patching.db "SELECT server_name, current_status FROM servers WHERE current_status='failed';"

# Count by status
sqlite3 patching.db "SELECT current_status, COUNT(*) FROM servers GROUP BY current_status;"
```

### PostgreSQL
```bash
# Quick backup
pg_dump -U patchadmin patching_db > backup_$(date +%Y%m%d).sql

# Connect to database
psql -U patchadmin -d patching_db

# Common queries
psql -U patchadmin -d patching_db -c "SELECT COUNT(*) FROM servers WHERE current_status='pending';"
```

---

## Troubleshooting Quick Fixes

### 🔧 Email Not Working
```bash
# Test email
python main.py --test-email admin@company.com

# Check SMTP settings
grep SMTP /opt/linux_patching_automation/config/settings.py

# View email logs
tail -f /var/log/patching/email_sender.log
```

### 🔧 Web Portal Down
```bash
# Restart service
systemctl restart patching-portal

# Check port
netstat -tlnp | grep 5001

# Check for errors
journalctl -u patching-portal -n 50 --no-pager
```

### 🔧 SSH Connection Issues
```bash
# Test as service user
sudo -u patchadmin ssh -v target-server

# Check SSH key
sudo -u patchadmin cat ~/.ssh/id_rsa.pub

# Deploy key to server
sudo -u patchadmin ssh-copy-id root@target-server
```

### 🔧 Database Issues
```bash
# Check database file (SQLite)
ls -la /opt/linux_patching_automation/patching.db

# Fix permissions
chown patchadmin:patchadmin /opt/linux_patching_automation/patching.db

# Check PostgreSQL
systemctl status postgresql
psql -U patchadmin -d patching_db -c "SELECT 1;"
```

---

## Configuration Quick Edits

### Change Admin Email
```python
# Edit /opt/linux_patching_automation/config/settings.py
DEFAULT_ADMIN_EMAIL = "newadmin@company.com"

# Or via CLI
python main.py --config-set admin_email "newadmin@company.com"
```

### Change SMTP Settings
```python
# Edit /opt/linux_patching_automation/config/settings.py
SMTP_SERVER = "new.smtp.server"
SMTP_PORT = 587
SMTP_USERNAME = "new@email.com"
SMTP_PASSWORD = "newpassword"
```

### Change Web Port
```bash
# Edit service file
sudo nano /etc/systemd/system/patching-portal.service
# Change port in ExecStart line

# Reload and restart
systemctl daemon-reload
systemctl restart patching-portal
```

---

## API Quick Examples

### Get Auth Token
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### List Servers
```bash
curl -X GET http://localhost:5001/api/servers \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Approve Server
```bash
curl -X POST http://localhost:5001/api/servers/web01/approve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quarter":3}'
```

---

## Emergency Contacts & Procedures

### System Down Completely
1. Check system resources: `df -h`, `free -m`, `top`
2. Check all services: `systemctl status patching-*`
3. Review system logs: `journalctl -xe`
4. Restart services: `systemctl restart patching-portal patching-monitor`

### Mass Approval Needed
```bash
# Approve all pending for a quarter
python main.py --auto-approve --criteria "status=pending" --quarter 3

# Approve entire host group
python main.py --approve-by-group "production" --quarter 3 --force
```

### Rollback Patch
```bash
# Mark server as failed
python main.py --update-server SERVER_NAME --field current_status --value failed

# Send failure notification
python main.py --notify-failure SERVER_NAME --message "Rollback required"
```

---

## Keyboard Shortcuts (Web Portal)

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Quick search |
| `Ctrl+S` | Save changes |
| `Ctrl+A` | Select all servers |
| `Ctrl+E` | Export current view |
| `Ctrl+R` | Refresh data |
| `Ctrl+F` | Filter servers |
| `Esc` | Close dialog |

---

## Regular Expression Patterns

### Server Name Patterns
```bash
# All web servers
python main.py --search-server "web[0-9]+"

# Servers in specific datacenter
python main.py --search-server ".*\.dc1\.company\.com"

# Development servers
python main.py --search-server ".*-dev[0-9]*"
```

### Filter Expressions
```bash
# Complex filters
--filter "host_group=web*,status!=completed,owner=admin@*"

# Date-based filters
--filter "patch_date>=2025-07-01,patch_date<=2025-07-31"

# Multiple status
--filter "status=pending|approved|scheduled"
```

---

**Quick Support:**
- Logs: `/var/log/patching/`
- Config: `/opt/linux_patching_automation/config/`
- Backups: `/backup/patching/`
- Service User: `patchadmin`

**Remember:** Always test commands with `--dry-run` first!