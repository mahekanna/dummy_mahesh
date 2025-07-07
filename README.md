# Linux OS Patching Automation - Project Summary

## Overview

This project provides a comprehensive system for automating Linux server patching operations. It includes a complete workflow from scheduling and notification through execution and validation.

## Key Features

- **Custom Quarter System**: Quarters defined as Nov-Jan (Q1), Feb-Apr (Q2), May-Jul (Q3), Aug-Oct (Q4)
- **Advanced Timezone Handling**: Automated timezone detection via SNMP and conversion
- **Web Portal**: User interface for schedule management
- **Email Notifications**: Automated notifications at each stage
- **Pre-patch Validation**: Server readiness verification
- **Post-patch Validation**: Success verification
- **Comprehensive Logging**: Detailed logging of all operations

## Directory Structure

```
linux_patching_automation/
├── config/               # Configuration files
├── database/             # Database models and schema
├── scripts/              # Core Python scripts
├── bash_scripts/         # Shell scripts for execution
├── templates/            # Email templates
├── web_portal/           # Web interface
├── utils/                # Utility modules
├── data/                 # Data files (CSV)
├── logs/                 # Log files
├── tests/                # Test suite
├── docs/                 # Documentation
├── main.py               # Main execution script
├── monitor.py            # Continuous monitoring script
├── deploy.sh             # Deployment script
└── requirements.txt      # Python dependencies
```

## Installation

### Automated Installation

1. Clone the repository
2. Run the deployment script: `sudo ./deploy.sh`
3. Configure settings in `/etc/patching/patching.conf`
4. Update server inventory in `data/servers.csv`
5. Access the web portal at http://your-server:5000/

### Manual Installation

If you encounter permission issues with the automated deployment script, use the manual installation script:

```bash
sudo ./manual_install.sh
```

### Troubleshooting Permission Issues

If you encounter permission errors during installation:

1. Ensure /opt directory has proper permissions:
   ```bash
   sudo chmod 755 /opt
   ```

2. Fix ownership of the installation directory:
   ```bash
   sudo chown -R patchadmin:patchadmin /opt/linux_patching_automation
   ```

3. Check Python virtual environment permissions:
   ```bash
   sudo mkdir -p /opt/linux_patching_automation/venv
   sudo chown patchadmin:patchadmin /opt/linux_patching_automation/venv
   sudo -u patchadmin python3 -m venv /opt/linux_patching_automation/venv
   ```

## Configuration

The main settings are defined in `config/settings.py`, including:

- Quarter definitions
- Database configuration
- Email settings
- Patching parameters
- File paths

## Workflow

1. **Monthly Notice**: Send quarterly patch scheduling notice
2. **Reminders**: Send weekly and daily reminders
3. **Pre-checks**: Validate server readiness before patching
4. **Scheduling**: Schedule patching jobs
5. **Patch Execution**: Apply patches to target servers
6. **Validation**: Verify successful patch application
7. **Post-Patch**: Validate system stability after patching
8. **Completion Notice**: Send notification of completion

## Custom Quarter System

This system uses a custom quarter definition:

- **Q1**: November to January
- **Q2**: February to April
- **Q3**: May to July
- **Q4**: August to October

This differs from the standard calendar quarters to align with your specific patching cycles.

## Timezone Handling

The system detects server timezones using SNMP and converts between timezones for proper scheduling. All times are displayed in the server's local timezone to avoid confusion.

## Usage

### Command Line

```bash
# Send monthly patching notice
python main.py --step 1 --quarter 3

# Send weekly and daily reminders
python main.py --step 2 --quarter 3

# Run pre-checks for scheduled servers
python main.py --step 3 --quarter 3

# Schedule patching jobs
python main.py --step 4 --quarter 3

# Validate patching for a specific server
python main.py --step 5 --server server_name --quarter 3

# Run post-patch validation
python main.py --step 6 --server server_name --quarter 3

# Run all steps (except 5-6 which require server name)
python main.py --step all --quarter 3
```

### Web Portal

The web portal provides a user-friendly interface for:

- Viewing server inventory
- Updating patching schedules
- Monitoring patching status
- Visualizing quarterly schedules

## Documentation

For detailed information, see the following documentation:

- **Deployment Guide**: `docs/deployment_guide.md`
- **User Manual**: `docs/user_manual.md`
- **API Reference**: `docs/api_reference.md`
- **Troubleshooting Guide**: `docs/troubleshooting.md`

## Testing

Run the automated tests:

```bash
# Run basic tests
python -m tests.test_basic

# Run SNMP tests
python -m tests.test_snmp

# Verify quarter and timezone setup
python utils/verify_setup.py
```

## Verification

Use the verification tool to confirm proper setup:

```bash
python utils/verify_setup.py --all
```

This will verify:
- Quarter system configuration
- Timezone handling
- CSV data format
