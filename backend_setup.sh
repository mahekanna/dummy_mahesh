#!/bin/bash

# Linux Patching Automation - Backend Only Setup Script
# This script sets up the CLI-based backend system without web components

set -e

echo "======================================"
echo "Linux Patching Backend Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   print_error "Please do not run this script as root"
   exit 1
fi

# Create project structure
print_status "Creating backend project structure..."

# Create main directories
mkdir -p linux_patching_backend/{cli,core,utils,config,data,logs,scripts,tests,docs}
mkdir -p linux_patching_backend/data/reports

# Create __init__.py files
touch linux_patching_backend/cli/__init__.py
touch linux_patching_backend/core/__init__.py
touch linux_patching_backend/utils/__init__.py
touch linux_patching_backend/config/__init__.py

# Create requirements.txt
cat > linux_patching_backend/requirements.txt << 'EOF'
# Core dependencies
paramiko>=2.7.2
pytz>=2021.3
python-crontab>=2.5.1
tabulate>=0.8.9
click>=8.0.0
colorama>=0.4.4

# CSV and data handling
pandas>=1.3.0

# Email
secure-smtplib>=0.1.1

# SNMP
pysnmp>=4.4.12

# Scheduling
schedule>=1.1.0
APScheduler>=3.8.0

# Configuration
python-dotenv>=0.19.0
PyYAML>=5.4.1

# Testing
pytest>=6.2.5
pytest-mock>=3.6.1
pytest-cov>=2.12.1
EOF

# Create setup.py
cat > linux_patching_backend/setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="linux-patching-backend",
    version="1.0.0",
    description="Linux Patching Automation Backend CLI",
    packages=find_packages(),
    install_requires=[
        "paramiko>=2.7.2",
        "pytz>=2021.3",
        "click>=8.0.0",
        "tabulate>=0.8.9",
        "PyYAML>=5.4.1",
    ],
    entry_points={
        'console_scripts': [
            'patch-manager=cli.patch_manager:main',
        ],
    },
)
EOF

# Create main CLI entry point
cat > linux_patching_backend/cli/patch_manager.py << 'EOF'
#!/usr/bin/env python3
"""
Linux Patching Automation - CLI Interface
Main entry point for all patching operations
"""

import click
import sys
import os
from tabulate import tabulate
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.server_manager import server_group
from cli.approval_manager import approval_group
from cli.report_generator import report_group
from core.patching_engine import PatchingEngine
from utils.logger import setup_logger

logger = setup_logger('patch_manager')

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Linux Patching Automation CLI - Backend Management Tool"""
    pass

@cli.command()
@click.option('--server', '-s', required=True, help='Server name to patch')
@click.option('--dry-run', is_flag=True, help='Perform dry run without actual patching')
@click.option('--force', is_flag=True, help='Force patching even if pre-checks fail')
def patch(server, dry_run, force):
    """Execute patching for a specific server"""
    logger.info(f"Starting patch operation for {server}")
    
    engine = PatchingEngine()
    
    if dry_run:
        click.echo(f"Performing dry run for {server}...")
        result = engine.dry_run(server)
    else:
        if not force and not click.confirm(f"Are you sure you want to patch {server}?"):
            click.echo("Patching cancelled.")
            return
            
        click.echo(f"Starting patching for {server}...")
        result = engine.patch_server(server, force=force)
    
    if result['success']:
        click.secho(f"✓ Patching completed successfully for {server}", fg='green')
    else:
        click.secho(f"✗ Patching failed for {server}: {result['error']}", fg='red')

@cli.command()
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to process')
@click.option('--group', '-g', help='Host group to process')
@click.option('--dry-run', is_flag=True, help='Show what would be patched')
def batch_patch(quarter, group, dry_run):
    """Execute batch patching for multiple servers"""
    engine = PatchingEngine()
    
    click.echo(f"Starting batch patching...")
    if quarter:
        click.echo(f"Quarter: {quarter}")
    if group:
        click.echo(f"Host Group: {group}")
    
    servers = engine.get_servers_for_patching(quarter=quarter, group=group)
    
    if dry_run:
        click.echo("\nServers that would be patched:")
        for server in servers:
            click.echo(f"  - {server['name']} ({server['status']})")
    else:
        if not click.confirm(f"Patch {len(servers)} servers?"):
            return
            
        results = engine.batch_patch(servers)
        
        # Display results
        click.echo("\nPatching Results:")
        for result in results:
            if result['success']:
                click.secho(f"  ✓ {result['server']}", fg='green')
            else:
                click.secho(f"  ✗ {result['server']}: {result['error']}", fg='red')

@cli.command()
def status():
    """Show current patching status"""
    engine = PatchingEngine()
    status_data = engine.get_patching_status()
    
    # Format as table
    headers = ['Metric', 'Value']
    table_data = [
        ['Total Servers', status_data['total_servers']],
        ['Pending Approval', status_data['pending_approval']],
        ['Scheduled', status_data['scheduled']],
        ['In Progress', status_data['in_progress']],
        ['Completed', status_data['completed']],
        ['Failed', status_data['failed']],
        ['Current Quarter', status_data['current_quarter']],
    ]
    
    click.echo("\nPatching Status Summary")
    click.echo("=" * 40)
    click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))

# Add subcommand groups
cli.add_command(server_group)
cli.add_command(approval_group)
cli.add_command(report_group)

def main():
    """Main entry point"""
    try:
        cli()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        click.secho(f"Error: {str(e)}", fg='red')
        sys.exit(1)

if __name__ == '__main__':
    main()
EOF

# Create sample configuration
cat > linux_patching_backend/config/settings.py << 'EOF'
"""
Backend Configuration Settings
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
LOG_DIR = BASE_DIR / 'logs'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
(DATA_DIR / 'reports').mkdir(exist_ok=True)

# CSV Files
SERVERS_CSV = DATA_DIR / 'servers.csv'
PATCH_HISTORY_CSV = DATA_DIR / 'patch_history.csv'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', '25'))
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'False').lower() == 'true'
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'patching@company.com')

# Patching Configuration
PRECHECK_HOURS_BEFORE = int(os.getenv('PRECHECK_HOURS_BEFORE', '24'))
PATCHING_WINDOW_HOURS = int(os.getenv('PATCHING_WINDOW_HOURS', '4'))
MAX_PARALLEL_PATCHES = int(os.getenv('MAX_PARALLEL_PATCHES', '5'))
PATCH_TIMEOUT_MINUTES = int(os.getenv('PATCH_TIMEOUT_MINUTES', '120'))

# SSH Configuration
SSH_TIMEOUT = int(os.getenv('SSH_TIMEOUT', '30'))
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH', os.path.expanduser('~/.ssh/id_rsa'))

# SNMP Configuration
SNMP_COMMUNITY = os.getenv('SNMP_COMMUNITY', 'public')
SNMP_TIMEOUT = int(os.getenv('SNMP_TIMEOUT', '10'))

# User Roles
USER_ROLES = {
    'admin': ['all'],
    'operator': ['patch', 'view', 'report'],
    'viewer': ['view', 'report']
}
EOF

# Create README
cat > linux_patching_backend/README.md << 'EOF'
# Linux Patching Automation - Backend CLI

A command-line interface for automating Linux server patching operations.

## Features

- **Server Management**: Add, remove, and manage server inventory
- **Automated Patching**: Schedule and execute patches with pre/post checks
- **Reporting**: Generate detailed reports on patching status
- **Email Notifications**: Get notified about patching events
- **Rollback Support**: Automated rollback on failure

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd linux_patching_backend
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run setup:
```bash
python setup.py install
```

### Basic Usage

```bash
# View help
patch-manager --help

# Check status
patch-manager status

# Add a server
patch-manager server add --name server01.company.com --group web --os ubuntu

# List servers
patch-manager server list

# Patch a single server
patch-manager patch --server server01.company.com

# Batch patch by quarter
patch-manager batch-patch --quarter Q1

# Generate report
patch-manager report generate --type summary --quarter Q1
```

## Configuration

Edit `config/settings.py` or use environment variables:

```bash
export SMTP_SERVER=mail.company.com
export SMTP_PORT=587
export EMAIL_FROM=patching@company.com
```

## Server Inventory

Servers are stored in `data/servers.csv` with the following fields:
- Server Name
- Host Group
- Operating System
- Patch Schedule (Q1-Q4 dates)
- Owner information
- Timezone

## Cron Setup

Add to crontab for automated patching:

```bash
# Run pre-checks daily at 2 AM
0 2 * * * /path/to/venv/bin/patch-manager precheck --auto

# Process scheduled patches every hour
0 * * * * /path/to/venv/bin/patch-manager process-scheduled
```

## Support

For issues or questions, contact the system administration team.
EOF

# Create sample server manager
cat > linux_patching_backend/cli/server_manager.py << 'EOF'
"""Server management CLI commands"""

import click
from tabulate import tabulate
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_handler import CSVHandler
from utils.logger import setup_logger

logger = setup_logger('server_manager')

@click.group(name='server')
def server_group():
    """Manage server inventory"""
    pass

@server_group.command(name='list')
@click.option('--group', '-g', help='Filter by host group')
@click.option('--os', '-o', help='Filter by operating system')
def list_servers(group, os):
    """List all servers in inventory"""
    csv_handler = CSVHandler()
    servers = csv_handler.read_servers()
    
    # Apply filters
    if group:
        servers = [s for s in servers if s.get('host_group', '').lower() == group.lower()]
    if os:
        servers = [s for s in servers if s.get('operating_system', '').lower() == os.lower()]
    
    if not servers:
        click.echo("No servers found matching criteria.")
        return
    
    # Prepare table data
    headers = ['Server Name', 'Host Group', 'OS', 'Timezone', 'Status']
    table_data = []
    
    for server in servers:
        table_data.append([
            server.get('server_name', ''),
            server.get('host_group', ''),
            server.get('operating_system', ''),
            server.get('server_timezone', 'UTC'),
            server.get('current_quarter_status', 'Active')
        ])
    
    click.echo(f"\nTotal Servers: {len(servers)}")
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

@server_group.command(name='add')
@click.option('--name', '-n', required=True, help='Server hostname')
@click.option('--group', '-g', required=True, help='Host group')
@click.option('--os', '-o', required=True, help='Operating system')
@click.option('--timezone', '-t', default='UTC', help='Server timezone')
@click.option('--owner', help='Primary owner email')
def add_server(name, group, os, timezone, owner):
    """Add a new server to inventory"""
    csv_handler = CSVHandler()
    
    # Check if server already exists
    servers = csv_handler.read_servers()
    if any(s.get('server_name') == name for s in servers):
        click.secho(f"Server {name} already exists!", fg='red')
        return
    
    # Add new server
    new_server = {
        'server_name': name,
        'host_group': group,
        'operating_system': os,
        'server_timezone': timezone,
        'primary_owner': owner or '',
        'current_quarter_status': 'Active'
    }
    
    servers.append(new_server)
    
    if csv_handler.write_servers(servers):
        click.secho(f"✓ Server {name} added successfully!", fg='green')
        logger.info(f"Added server: {name}")
    else:
        click.secho(f"✗ Failed to add server {name}", fg='red')

@server_group.command(name='remove')
@click.option('--name', '-n', required=True, help='Server hostname')
@click.option('--force', is_flag=True, help='Skip confirmation')
def remove_server(name, force):
    """Remove a server from inventory"""
    if not force and not click.confirm(f"Remove server {name}?"):
        return
    
    csv_handler = CSVHandler()
    servers = csv_handler.read_servers()
    
    # Filter out the server
    original_count = len(servers)
    servers = [s for s in servers if s.get('server_name') != name]
    
    if len(servers) == original_count:
        click.secho(f"Server {name} not found!", fg='red')
        return
    
    if csv_handler.write_servers(servers):
        click.secho(f"✓ Server {name} removed successfully!", fg='green')
        logger.info(f"Removed server: {name}")
    else:
        click.secho(f"✗ Failed to remove server {name}", fg='red')
EOF

# Make scripts executable
chmod +x linux_patching_backend/cli/patch_manager.py

print_status "Backend project structure created successfully!"

# Create installation instructions
cat > linux_patching_backend/INSTALL.md << 'EOF'
# Installation Instructions

## Prerequisites

- Python 3.6 or higher
- pip package manager
- SSH access to target servers
- sudo privileges for patching operations

## Step 1: Create patchadmin user

```bash
sudo useradd -m -s /bin/bash patchadmin
sudo passwd patchadmin
```

## Step 2: Setup SSH keys

```bash
sudo -u patchadmin ssh-keygen -t rsa -b 4096
# Copy public key to all target servers
```

## Step 3: Install Python dependencies

```bash
cd linux_patching_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 4: Configure settings

Edit `config/settings.py` or create `.env` file:

```
SMTP_SERVER=mail.company.com
SMTP_PORT=587
EMAIL_FROM=patching@company.com
```

## Step 5: Initialize data

Create initial `data/servers.csv` with your server inventory.

## Step 6: Test installation

```bash
patch-manager --version
patch-manager status
```

## Step 7: Setup cron (optional)

```bash
crontab -e
# Add automated scheduling entries
```
EOF

echo ""
print_status "Backend setup complete!"
echo ""
echo "Next steps:"
echo "1. cd linux_patching_backend"
echo "2. python3 -m venv venv"
echo "3. source venv/bin/activate"
echo "4. pip install -r requirements.txt"
echo "5. Configure settings in config/settings.py"
echo "6. Add servers to data/servers.csv"
echo "7. Run: python cli/patch_manager.py --help"
echo ""
echo "See INSTALL.md for detailed instructions."
EOF

# Make the script executable
chmod +x backend_setup.sh