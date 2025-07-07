# 📁 Project Structure

## Overview
```
linux_patching_automation/
├── 📋 README.md                          # Project overview and quick start
├── 🚀 deploy_interactive.sh              # Interactive deployment script
├── 📖 INTERACTIVE_DEPLOYMENT_GUIDE.md    # Deployment documentation
├── 🐍 main.py                           # Main CLI entry point
├── 📊 monitor.py                        # Monitoring daemon
├── ⚙️ manage_services.py                # Service management utility
├── 🗃️ patching.db                       # SQLite database (if used)
├── 📝 requirements.txt                   # Python dependencies (PostgreSQL)
├── 📝 requirements_sqlite.txt            # Python dependencies (SQLite only)
└── 🚫 .gitignore                        # Git ignore patterns
```

## Core Directories

### 📂 bash_scripts/
Shell scripts for system operations:
- `dell_idrac_check.sh` - iDRAC hardware validation
- `disk_check.sh` - Disk space verification
- `patch_execution.sh` - Patch deployment script
- `server_validation.sh` - Post-patch validation

### 📂 config/
System configuration files:
- `__init__.py` - Python package marker
- `admin_config.json` - Admin settings and preferences
- `server_groups.json` - Host group definitions
- `settings.py` - Main application configuration
- `users.py` - User management and authentication

### 📂 data/
Data storage:
- `servers.csv` - Server inventory database

### 📂 database/
Database schema and models:
- `__init__.py` - Python package marker
- `models.py` - Database ORM models
- `schema.sql` - Database schema definition

### 📂 docs/
Comprehensive documentation:
- `ADMIN_TECHNICAL_GUIDE.md` - Complete admin guide
- `ADMIN_QUICK_REFERENCE.md` - Daily operations reference
- `CLI_COMMAND_REFERENCE.md` - CLI command reference
- `WEB_PORTAL_USER_GUIDE.md` - Web interface guide
- `deployment_guide.md` - Legacy deployment guide

### 📂 logs/
Application logs (created at runtime):
- `.gitkeep` - Preserves empty directory structure
- Various `.log` files created during operation

### 📂 scripts/
Core application modules:
- `__init__.py` - Python package marker
- `admin_manager.py` - Administrative operations
- `automated_reports.py` - Report generation system
- `generate_host_groups.py` - Host group management
- `intelligent_scheduler.py` - AI-powered scheduling
- `ldap_manager.py` - LDAP integration
- `load_predictor.py` - Load balancing and prediction
- `scheduler.py` - Basic scheduling operations
- `step0_approval_requests.py` - Approval workflow
- `step1_monthly_notice.py` - Monthly notifications
- `step1b_weekly_followup.py` - Weekly follow-ups
- `step2_reminders.py` - Reminder notifications
- `step3_prechecks.py` - Pre-patch validation
- `step4_scheduler.py` - Patch scheduling
- `step5_patch_validation.py` - Patch validation
- `step6_post_patch.py` - Post-patch operations
- `step7_email_handler.py` - Email management
- `sync_host_groups.py` - Host group synchronization

### 📂 templates/
Email templates:
- `admin_daily_report.html` - Daily admin reports
- `admin_weekly_report.html` - Weekly admin reports
- `approval_confirmation.html` - Approval confirmations
- `approval_request.html` - Approval requests
- `completion_notice.html` - Patch completion notices
- `daily_reminder.html` - Daily reminders
- `monthly_notice.html` - Monthly notifications
- `weekly_followup.html` - Weekly follow-ups
- `weekly_reminder.html` - Weekly reminders

### 📂 tests/
Unit tests:
- `test_basic.py` - Basic functionality tests
- `test_snmp.py` - SNMP integration tests

### 📂 utils/
Utility modules:
- `__init__.py` - Python package marker
- `csv_handler.py` - CSV file operations
- `email_sender.py` - Email delivery system
- `logger.py` - Logging utilities
- `timezone_handler.py` - Timezone management
- `verify_setup.py` - Installation verification

### 📂 web_portal/
Web interface application:
- `app.py` - Flask web application
- `static/` - CSS, JavaScript, images
  - `main.js` - Main JavaScript functionality
  - `style.css` - Application styles
- `templates/` - HTML templates
  - `admin_advanced.html` - Advanced admin features
  - `admin_panel.html` - Admin dashboard
  - `base.html` - Base template
  - `dashboard.html` - Main dashboard
  - `index.html` - Landing page
  - `login.html` - Authentication page
  - `reports_dashboard.html` - Reports interface
  - `server_detail.html` - Server details page

## File Types

### 🐍 Python Files
- **Entry Points**: `main.py`, `monitor.py`, `manage_services.py`
- **Core Logic**: Files in `scripts/` directory
- **Utilities**: Files in `utils/` directory
- **Web App**: Files in `web_portal/` directory
- **Configuration**: Files in `config/` directory
- **Database**: Files in `database/` directory

### 🐚 Shell Scripts
- **System Operations**: Files in `bash_scripts/` directory
- **Deployment**: `deploy_interactive.sh`

### 📝 Configuration Files
- **JSON**: `*.json` files for structured configuration
- **Python**: `settings.py`, `users.py` for complex configuration
- **CSV**: `servers.csv` for data storage
- **SQL**: `schema.sql` for database structure

### 📖 Documentation
- **Markdown**: `*.md` files for documentation
- **HTML**: Email and web templates

### 🗄️ Data Files
- **Database**: `patching.db` (SQLite)
- **CSV Data**: Server inventory and exports
- **Logs**: Runtime application logs

## Excluded Files

The following file types are excluded via `.gitignore`:
- 🚫 Virtual environments (`venv/`, `env/`)
- 🚫 Python cache (`__pycache__/`, `*.pyc`)
- 🚫 Runtime files (`*.pid`, `*.log`)
- 🚫 Development files (`test_*.py`, `debug_*.html`)
- 🚫 Temporary files (`*.tmp`, `*.bak`)
- 🚫 OS files (`.DS_Store`, `Thumbs.db`)
- 🚫 IDE files (`.vscode/`, `.idea/`)
- 🚫 Sensitive config (`.env`, `local_settings.py`)

## Dependencies

### 📦 Python Packages
Defined in:
- `requirements.txt` - Full dependencies (includes PostgreSQL)
- `requirements_sqlite.txt` - SQLite-only dependencies

### 🔧 System Dependencies
- Python 3.8+
- SSH client
- System package managers (yum, apt)
- Optional: PostgreSQL, Redis

## Runtime Structure

During operation, additional directories may be created:
- `/var/log/patching/` - System logs
- `/backup/patching/` - Backups
- `/tmp/patching/` - Temporary files
- `venv/` - Python virtual environment

## Key Features by Directory

| Directory | Primary Function | Key Features |
|-----------|------------------|--------------|
| `scripts/` | Core Logic | Workflow steps, scheduling, reporting |
| `web_portal/` | User Interface | Dashboard, admin panel, reports |
| `bash_scripts/` | System Operations | Patch execution, validation |
| `config/` | Configuration | Settings, users, host groups |
| `utils/` | Common Functions | Email, CSV, logging, timezone |
| `templates/` | Communications | Email templates, notifications |
| `docs/` | Documentation | User guides, references |

This structure provides a clean, organized codebase that's easy to navigate and maintain.