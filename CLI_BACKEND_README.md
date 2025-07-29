# Linux Patching Automation - CLI Backend Solution

## Overview

This is a streamlined, CLI-focused backend solution for Linux patching automation. It provides all the core patching functionality without web UI complexity, making it ideal for organizations that prefer command-line operations or want to implement patching quickly.

## Key Benefits

1. **No Web Dependencies**: No Flask, nginx, or web server configuration needed
2. **Simple Deployment**: Just Python and SSH access required
3. **Direct Control**: Execute patches directly via CLI commands
4. **Lightweight**: Minimal resource footprint
5. **Easy Integration**: Can be integrated with existing automation tools

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CLI Interface │────▶│  Patching Engine │────▶│ Target Servers  │
│  (patch-manager)│     │    (Core Logic)  │     │   (via SSH)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   CSV Storage   │     │ Email Notifier   │     │   SNMP Queries  │
│  (servers.csv)  │     │  (SMTP Server)   │     │  (Timezone etc) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Quick Start Guide

### 1. Run Setup Script

```bash
# Download and run the backend setup script
chmod +x backend_setup.sh
./backend_setup.sh
```

### 2. Activate Environment

```bash
cd linux_patching_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Settings

Create a `.env` file or edit `config/settings.py`:

```bash
# .env file
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
EMAIL_FROM=patching@company.com
SSH_KEY_PATH=/home/patchadmin/.ssh/id_rsa
```

### 4. Add Servers

```bash
# Add servers one by one
patch-manager server add --name web01.company.com --group web --os ubuntu --timezone America/New_York

# Or import from CSV
patch-manager server import --file server_list.csv
```

### 5. Execute Patching

```bash
# Patch single server
patch-manager patch --server web01.company.com

# Batch patch by quarter
patch-manager batch-patch --quarter Q1

# Dry run to see what would happen
patch-manager patch --server web01.company.com --dry-run
```

## CLI Command Reference

### Main Commands

```bash
patch-manager --help                    # Show all commands
patch-manager status                    # Show patching status summary
patch-manager patch -s SERVER           # Patch specific server
patch-manager batch-patch -q Q1         # Patch all Q1 servers
```

### Server Management

```bash
patch-manager server list               # List all servers
patch-manager server list -g web        # List servers in 'web' group
patch-manager server add -n SERVER      # Add new server
patch-manager server remove -n SERVER   # Remove server
patch-manager server update -n SERVER   # Update server details
```

### Approval Management

```bash
patch-manager approval list             # List pending approvals
patch-manager approval approve -s SERVER # Approve server for patching
patch-manager approval auto-approve -g GROUP # Auto-approve group
```

### Reporting

```bash
patch-manager report generate --type summary --quarter Q1
patch-manager report generate --type detailed --server web01
patch-manager report generate --type failed --last 7
patch-manager report email --type summary --to admin@company.com
```

## Example Workflows

### 1. Monthly Patching Cycle

```bash
# Beginning of quarter - review and approve
patch-manager approval list --quarter Q1
patch-manager approval auto-approve --group non-prod

# Night before patching - run pre-checks
patch-manager precheck --quarter Q1

# Patching night - execute patches
patch-manager batch-patch --quarter Q1 --group non-prod
patch-manager batch-patch --quarter Q1 --group prod --confirm

# After patching - generate reports
patch-manager report generate --type summary --quarter Q1
patch-manager report email --type detailed --quarter Q1
```

### 2. Emergency Patching

```bash
# Single server emergency patch
patch-manager patch --server critical01.company.com --force

# Check result
patch-manager server status --name critical01.company.com
```

### 3. Automated via Cron

```bash
# Add to crontab
# Pre-checks every day at 2 AM
0 2 * * * /path/to/venv/bin/patch-manager precheck --auto

# Process approved patches every Saturday at 11 PM
0 23 * * 6 /path/to/venv/bin/patch-manager batch-patch --approved-only

# Generate weekly reports
0 8 * * 1 /path/to/venv/bin/patch-manager report generate --type weekly
```

## Data Storage

### Server Inventory (data/servers.csv)

```csv
Server Name,Host Group,Operating System,Server Timezone,Q1 Patch Date,Q1 Patch Time
web01.company.com,web,ubuntu,America/New_York,2024-01-15,02:00
db01.company.com,database,rhel,America/Chicago,2024-01-16,03:00
```

### Patch History (data/patch_history.csv)

```csv
Timestamp,Server,Quarter,Status,Duration,Error
2024-01-15 02:00:00,web01.company.com,Q1,Success,45m,
2024-01-16 03:00:00,db01.company.com,Q1,Failed,12m,Connection timeout
```

## Configuration Options

### Environment Variables

- `LOG_LEVEL`: Set to DEBUG, INFO, WARNING, ERROR (default: INFO)
- `MAX_PARALLEL_PATCHES`: Number of concurrent patches (default: 5)
- `PATCH_TIMEOUT_MINUTES`: Timeout for each patch operation (default: 120)
- `PRECHECK_HOURS_BEFORE`: Hours before patching to run pre-checks (default: 24)

### SSH Configuration

Ensure the patchadmin user has:
- SSH key-based authentication to all servers
- Sudo privileges on target servers
- Proper entries in ~/.ssh/config for connection parameters

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   ```bash
   # Test SSH connectivity
   ssh patchadmin@server01.company.com
   # Check SSH key permissions
   chmod 600 ~/.ssh/id_rsa
   ```

2. **Permission Denied**
   ```bash
   # Verify sudo access on target server
   ssh server01 'sudo -n true'
   ```

3. **SMTP Errors**
   ```bash
   # Test email configuration
   patch-manager test email --to admin@company.com
   ```

## Migration from Full System

If migrating from the full web-based system:

1. Export server data: `patch-manager export --format csv`
2. Copy `data/servers.csv` to new backend-only installation
3. Update configuration files
4. Test with dry-run before actual patching

## Support

For issues or questions:
- Check logs in `logs/patching.log`
- Run commands with `--debug` flag for verbose output
- Review error messages in `logs/errors.log`

## Next Steps

1. **Extend Functionality**: Add custom pre/post scripts
2. **Integration**: Connect with ticketing systems
3. **Monitoring**: Send metrics to monitoring platforms
4. **Automation**: Build wrapper scripts for complex workflows