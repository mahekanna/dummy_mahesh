# Linux Patching Automation - Backend Only Project Structure

## Overview
This is a CLI-focused backend solution for Linux patching automation without web UI components.

## Directory Structure

```
linux_patching_backend/
├── cli/                        # Command-line interface tools
│   ├── __init__.py
│   ├── patch_manager.py        # Main CLI entry point
│   ├── server_manager.py       # Server management commands
│   ├── report_generator.py     # Reporting functionality
│   └── approval_manager.py     # Approval workflow commands
│
├── core/                       # Core business logic
│   ├── __init__.py
│   ├── patching_engine.py      # Main patching orchestrator
│   ├── precheck_handler.py     # Pre-patching validation
│   ├── postcheck_handler.py    # Post-patching validation
│   ├── rollback_handler.py     # Rollback functionality
│   └── scheduler.py            # Scheduling logic
│
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── csv_handler.py          # CSV file operations
│   ├── timezone_handler.py     # Timezone management
│   ├── email_sender.py         # Email notifications
│   ├── logger.py               # Logging functionality
│   ├── ssh_handler.py          # SSH connections
│   └── snmp_handler.py         # SNMP operations
│
├── config/                     # Configuration files
│   ├── __init__.py
│   ├── settings.py             # Application settings
│   ├── users.py                # User management (CLI users)
│   └── email_templates.py      # Email templates
│
├── data/                       # Data storage
│   ├── servers.csv             # Server inventory
│   ├── patch_history.csv       # Patching history
│   └── reports/                # Generated reports
│
├── logs/                       # Application logs
│   ├── patching.log
│   ├── errors.log
│   └── audit.log
│
├── scripts/                    # Deployment and utility scripts
│   ├── setup.sh                # Initial setup script
│   ├── create_user.sh          # Create patchadmin user
│   ├── install_dependencies.sh # Install Python packages
│   └── configure_cron.sh       # Setup cron jobs
│
├── tests/                      # Unit tests
│   ├── test_patching.py
│   ├── test_csv_handler.py
│   └── test_email.py
│
├── docs/                       # Documentation
│   ├── CLI_USAGE.md            # CLI command reference
│   ├── SETUP.md                # Setup instructions
│   └── WORKFLOW.md             # Patching workflow guide
│
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
└── README.md                   # Project documentation
```

## Key Components

### 1. CLI Module (`cli/`)
- **patch_manager.py**: Main entry point for all CLI operations
- **server_manager.py**: Add/remove/update servers, view inventory
- **report_generator.py**: Generate various reports (CSV, text)
- **approval_manager.py**: Handle approval workflows

### 2. Core Module (`core/`)
- **patching_engine.py**: Orchestrates the entire patching process
- **precheck_handler.py**: Validates servers before patching
- **postcheck_handler.py**: Verifies successful patching
- **rollback_handler.py**: Handles rollback scenarios
- **scheduler.py**: Manages scheduling and timing

### 3. Utils Module (`utils/`)
- **csv_handler.py**: Manages server inventory in CSV format
- **timezone_handler.py**: Handles timezone conversions
- **email_sender.py**: Sends notifications
- **logger.py**: Centralized logging
- **ssh_handler.py**: SSH connections for remote operations
- **snmp_handler.py**: SNMP queries for server information

### 4. Data Storage (`data/`)
- Simple CSV-based storage for server inventory
- Patch history tracking
- Generated reports storage

## Simplified Features

1. **Server Management**
   - Add/remove servers via CLI
   - Import from CSV
   - View server inventory

2. **Patching Operations**
   - Manual patching trigger
   - Scheduled patching
   - Pre/post checks
   - Rollback capability

3. **Reporting**
   - Summary reports
   - Detailed patch logs
   - Email notifications

4. **User Management**
   - Simple file-based user management
   - Role-based access (Admin, Operator, Viewer)

## Removed Components
- Flask web application
- Web templates and static files
- Database (SQLite/PostgreSQL)
- Web authentication (LDAP)
- Web API endpoints

## Benefits of Backend-Only Approach
1. Simpler deployment
2. No web server dependencies
3. Easier to troubleshoot
4. Can run on minimal systems
5. Direct SSH access for operations
6. Cron-based scheduling