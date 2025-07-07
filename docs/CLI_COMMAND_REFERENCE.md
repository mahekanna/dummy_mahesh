# 📋 CLI Command Reference Card

## Command Structure
```bash
python main.py [COMMAND] [OPTIONS] [ARGUMENTS]
```

---

## 🗄️ Database Operations

### Initialization & Maintenance
```bash
# Initialize new database
python main.py --init-db

# Backup database
python main.py --backup-db
python main.py --backup-db --output /path/to/backup.sql

# Restore database
python main.py --restore-db /path/to/backup.sql

# Database statistics
python main.py --db-stats

# Database cleanup (remove old records)
python main.py --db-cleanup --days 365

# Verify database integrity
python main.py --db-verify
```

---

## 📊 Server Management

### Import/Export Operations
```bash
# Import servers from CSV
python main.py --import-csv servers.csv
python main.py --import-csv servers.csv --update-existing

# Export servers to CSV
python main.py --export-csv output.csv
python main.py --export-csv output.csv --filter "status=pending"

# Export specific columns
python main.py --export-csv output.csv --columns "server_name,status,owner"
```

### Server Queries
```bash
# List all servers
python main.py --list-servers

# Search servers (wildcards supported)
python main.py --search-server "web*"
python main.py --search-server "*db*"
python main.py --search-server "*.prod.company.com"

# Filter servers
python main.py --list-servers --filter "status=pending"
python main.py --list-servers --filter "host_group=web_servers,status=approved"
python main.py --list-servers --filter "owner=admin@company.com"

# Complex filters
python main.py --list-servers --filter "status=pending|approved,host_group!=test*"
```

### Server Updates
```bash
# Update single server field
python main.py --update-server web01 --field primary_owner --value "newowner@company.com"
python main.py --update-server web01 --field host_group --value "production"

# Update multiple fields
python main.py --update-server web01 --updates "primary_owner=admin@company.com,host_group=web"

# Batch update from file
python main.py --batch-update updates.csv
```

---

## ✅ Approval Operations

### Individual Approvals
```bash
# Approve single server
python main.py --approve-server web01 --quarter 3
python main.py --approve-server web01 --quarter 3 --comment "Approved for maintenance"

# Approve with specific date/time
python main.py --approve-server web01 --quarter 3 --date "2025-07-15" --time "20:00"
```

### Bulk Approvals
```bash
# Approve multiple servers
python main.py --approve-servers web01,web02,db01 --quarter 3

# Approve by owner
python main.py --approve-by-owner "admin@company.com" --quarter 3
python main.py --approve-by-owner "team@company.com" --quarter 3 --dry-run

# Approve by host group
python main.py --approve-by-group "web_servers" --quarter 3
python main.py --approve-by-group "production" --quarter 3 --exclude "test*"

# Approve from file
python main.py --batch-approve servers_to_approve.txt --quarter 3

# Auto-approve based on criteria
python main.py --auto-approve --criteria "environment=dev" --quarter 3
python main.py --auto-approve --criteria "os=ubuntu" --quarter 3 --limit 50
```

### Approval Management
```bash
# List pending approvals
python main.py --list-pending --quarter 3
python main.py --list-pending --quarter 3 --owner "admin@company.com"

# Revoke approvals
python main.py --revoke-approval web01 --quarter 3
python main.py --revoke-approvals web01,web02 --quarter 3 --reason "Postponed"

# Export pending approvals
python main.py --export-pending --quarter 3 --output pending_q3.csv
```

---

## 📅 Scheduling Operations

### Manual Scheduling
```bash
# Schedule single server
python main.py --schedule-server web01 --date "2025-07-15" --time "20:00"

# Schedule multiple servers
python main.py --schedule-servers web01,web02 --date "2025-07-15" --time "20:00"

# Bulk schedule from file
python main.py --bulk-schedule schedule.csv
```

### Intelligent Scheduling
```bash
# Run intelligent scheduler for quarter
python main.py --intelligent-schedule --quarter 3

# With constraints
python main.py --intelligent-schedule --quarter 3 --max-per-hour 3
python main.py --intelligent-schedule --quarter 3 --window "20:00-23:00"

# With server list
python main.py --intelligent-schedule --quarter 3 --servers "web01,web02,db01"

# Dry run (preview only)
python main.py --intelligent-schedule --quarter 3 --dry-run
```

### Schedule Management
```bash
# View current schedule
python main.py --view-schedule --quarter 3
python main.py --view-schedule --quarter 3 --date "2025-07-15"

# Export schedule
python main.py --export-schedule --quarter 3 --format csv
python main.py --export-schedule --quarter 3 --format ical --output schedule.ics

# Clear schedule
python main.py --clear-schedule web01 --quarter 3
python main.py --clear-schedule --all --quarter 3 --confirm
```

---

## 🔄 Patching Workflow Steps

### Step Execution
```bash
# Step 0: Send approval requests
python main.py --step 0 --quarter 3

# Step 1: Send monthly notices
python main.py --step 1 --quarter 3

# Step 2: Send reminders (weekly/daily)
python main.py --step 2 --quarter 3

# Step 3: Run pre-checks
python main.py --step 3 --quarter 3

# Step 4: Execute patches
python main.py --step 4 --quarter 3

# Step 5: Validate patches
python main.py --step 5 --quarter 3

# Step 6: Post-patch validation
python main.py --step 6 --quarter 3
```

### Step Options
```bash
# Dry run mode
python main.py --step 4 --quarter 3 --dry-run

# Force execution (bypass time checks)
python main.py --step 4 --quarter 3 --force

# Specific servers only
python main.py --step 3 --quarter 3 --servers "web01,web02"

# Skip confirmations
python main.py --step 0 --quarter 3 --yes
```

---

## 📊 Reporting Commands

### Generate Reports
```bash
# Summary report
python main.py --generate-report summary --quarter 3

# Detailed report
python main.py --generate-report detailed --quarter 3

# Compliance report
python main.py --generate-report compliance --quarter 3

# Custom report with filters
python main.py --generate-report detailed --quarter 3 --filter "status=completed"
```

### Report Distribution
```bash
# Email report
python main.py --email-report summary --recipients "admin@company.com,manager@company.com"

# Email with custom subject
python main.py --email-report summary --recipients "admin@company.com" --subject "Q3 Patching Summary"

# Schedule recurring report
python main.py --schedule-report summary --frequency weekly --recipients "team@company.com"
```

### Report Export
```bash
# Export as PDF
python main.py --export-report summary --format pdf --output report.pdf

# Export as Excel
python main.py --export-report detailed --format excel --output report.xlsx

# Export as HTML
python main.py --export-report summary --format html --output report.html
```

---

## 📧 Email Operations

### Email Testing
```bash
# Send test email
python main.py --test-email admin@company.com

# Test with custom message
python main.py --test-email admin@company.com --message "Test from patching system"
```

### Notification Management
```bash
# Resend approval requests
python main.py --resend-approval-requests --quarter 3

# Resend to specific owners
python main.py --resend-approval-requests --quarter 3 --owners "admin@company.com"

# Send reminders
python main.py --send-reminders --quarter 3 --type daily
python main.py --send-reminders --quarter 3 --type weekly

# Send custom notification
python main.py --send-notification --recipients "team@company.com" --subject "Maintenance Notice" --body "Patching scheduled"
```

### Email History
```bash
# View email history
python main.py --email-history --days 7

# Export email log
python main.py --export-email-log --days 30 --output email_log.csv

# Resend failed emails
python main.py --resend-failed-emails --days 1
```

---

## 👤 User Management

### User Operations
```bash
# Create user
python main.py --create-user --username john --email john@company.com --role user

# With password
python main.py --create-user --username admin2 --email admin2@company.com --role admin --password "SecurePass123"

# Update user
python main.py --update-user john --role admin
python main.py --update-user john --email newemail@company.com

# Delete user
python main.py --delete-user john --confirm

# List users
python main.py --list-users
python main.py --list-users --role admin
```

### Password Management
```bash
# Reset password
python main.py --reset-password john

# Force password change
python main.py --force-password-change john

# Set password policy
python main.py --set-password-policy --min-length 12 --require-special
```

---

## 🔧 System Maintenance

### Health Checks
```bash
# Full system health check
python main.py --health-check

# Service status
python main.py --service-status

# Database connectivity
python main.py --check-db

# Email system test
python main.py --check-email

# SSH connectivity test
python main.py --check-ssh --servers "web01,web02"
```

### Cleanup Operations
```bash
# Clean old logs
python main.py --clean-logs --days 30

# Clean old reports
python main.py --clean-reports --days 90

# Clean patch history
python main.py --clean-history --days 365

# Full cleanup
python main.py --cleanup --all --days 90
```

### Configuration
```bash
# View current config
python main.py --show-config

# Update configuration
python main.py --config-set smtp_server "new.smtp.server"
python main.py --config-set max_servers_per_hour 10

# Export configuration
python main.py --export-config --output config_backup.json

# Import configuration
python main.py --import-config config_backup.json
```

---

## 🚀 Advanced Features

### Automation
```bash
# Create automation rule
python main.py --create-automation "auto_approve_dev" --criteria "environment=dev" --action "approve"

# List automations
python main.py --list-automations

# Run automation
python main.py --run-automation "auto_approve_dev"

# Delete automation
python main.py --delete-automation "auto_approve_dev"
```

### Batch Operations
```bash
# Batch mode with transaction
python main.py --batch-mode --begin
python main.py --approve-server web01 --quarter 3
python main.py --approve-server web02 --quarter 3
python main.py --batch-mode --commit

# Rollback batch
python main.py --batch-mode --rollback
```

### Custom Queries
```bash
# Run SQL query (read-only)
python main.py --query "SELECT COUNT(*) FROM servers WHERE status='pending'"

# Export query results
python main.py --query "SELECT * FROM servers WHERE host_group='web'" --export query_results.csv
```

---

## 🎯 Quick Examples

### Common Workflows

#### Weekly Approval Process
```bash
# 1. List pending servers
python main.py --list-pending --quarter 3 --export pending.csv

# 2. Review and approve
python main.py --approve-by-owner "admin@company.com" --quarter 3

# 3. Run intelligent scheduling
python main.py --intelligent-schedule --quarter 3

# 4. Send notifications
python main.py --send-reminders --quarter 3 --type weekly
```

#### Emergency Patch
```bash
# 1. Approve specific server
python main.py --approve-server critical-web01 --quarter 3

# 2. Schedule immediately
python main.py --schedule-server critical-web01 --date today --time "20:00"

# 3. Force execution
python main.py --step 4 --quarter 3 --servers "critical-web01" --force
```

#### Monthly Reporting
```bash
# 1. Generate all reports
python main.py --generate-report summary --quarter 3 --output summary.pdf
python main.py --generate-report detailed --quarter 3 --output detailed.xlsx
python main.py --generate-report compliance --quarter 3 --output compliance.pdf

# 2. Email to management
python main.py --email-report summary --recipients "management@company.com" --attach "summary.pdf,compliance.pdf"
```

---

## ⚡ Performance Tips

1. **Use Filters**: Always filter large datasets
   ```bash
   python main.py --list-servers --filter "status=pending" --limit 100
   ```

2. **Batch Operations**: Group similar operations
   ```bash
   python main.py --batch-approve servers.txt --quarter 3
   ```

3. **Dry Run First**: Test complex operations
   ```bash
   python main.py --intelligent-schedule --quarter 3 --dry-run
   ```

4. **Export for Analysis**: Work with exports for large datasets
   ```bash
   python main.py --export-csv all_servers.csv
   # Analyze in Excel
   python main.py --import-csv updated_servers.csv --update-existing
   ```

---

## 🆘 Getting Help

```bash
# Show help
python main.py --help

# Show version
python main.py --version

# Show command help
python main.py --approve-server --help

# Debug mode
python main.py --debug --list-servers

# Verbose output
python main.py --verbose --step 3 --quarter 3
```

---

**Pro Tip**: Create aliases for common commands:
```bash
alias pa='python /opt/linux_patching_automation/main.py'
alias pa-list='pa --list-servers'
alias pa-approve='pa --approve-server'
alias pa-schedule='pa --intelligent-schedule'
```