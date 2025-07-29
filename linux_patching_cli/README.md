# Linux Patching Automation - Complete CLI System

A comprehensive, production-ready Linux patching automation system with a powerful command-line interface.

## 🚀 Overview

This system provides complete automation for Linux server patching with advanced features including:

- **Multi-OS Support**: Ubuntu, Debian, CentOS, RHEL, Fedora
- **Parallel Processing**: Patch multiple servers simultaneously
- **Approval Workflows**: Built-in approval system for change management
- **Rich Email Notifications**: Professional HTML email templates
- **Comprehensive Logging**: Multi-level logging with audit trails
- **Pre/Post Validation**: Automated health checks before and after patching
- **Rollback Capabilities**: Automatic rollback on failure
- **Timezone Management**: SNMP-based timezone detection
- **Flexible Reporting**: Multiple report formats (CSV, JSON, HTML)
- **SSH Key Management**: Secure key-based authentication

## 📋 Features

### ✅ **Core Features**
- **Complete CLI Interface** with 50+ commands
- **Professional Email Templates** (10+ notification types)
- **Comprehensive Data Management** (5 CSV files)
- **Multi-OS Patching Support** (Ubuntu, Debian, CentOS, RHEL, Fedora)
- **Advanced SSH Operations** with connection pooling
- **Professional Logging System** (main, error, audit logs)
- **Approval Workflow System** with role-based access
- **Timezone Detection** via SNMP and SSH
- **Parallel Processing** with configurable limits
- **Complete Audit Trail** for compliance

### ✅ **Advanced Features**
- **Pre/Post Validation** with 20+ health checks
- **Rollback Capabilities** with automated recovery
- **Rich Reporting** with multiple formats
- **Email Queue System** with retry logic
- **Configuration Management** with environment variables
- **Systemd Service** integration
- **Cron Job** scheduling
- **Backup System** with retention policies
- **Health Monitoring** with alerts

## 🛠️ Installation

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/company/linux-patching-automation.git
cd linux-patching-automation/linux_patching_cli

# Run the deployment script (as root)
sudo ./deploy.sh
```

### Manual Installation

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv openssh-client snmp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Create configuration
cp config/settings.py.example config/settings.py
```

## 🔧 Configuration

### Basic Configuration

Edit `config/settings.py`:

```python
# SSH Configuration
SSH_KEY_PATH = '/home/patchadmin/.ssh/id_rsa'
SSH_DEFAULT_USER = 'patchadmin'

# Email Configuration
SMTP_SERVER = 'smtp.company.com'
SMTP_PORT = 587
SMTP_USE_TLS = True
EMAIL_FROM = 'patching@company.com'

# Patching Configuration
MAX_PARALLEL_PATCHES = 5
PATCH_TIMEOUT_MINUTES = 120
PRECHECK_HOURS_BEFORE = 24
```

### Environment Variables

```bash
# Set environment variables
export LOG_LEVEL=INFO
export SMTP_SERVER=smtp.company.com
export MAX_PARALLEL_PATCHES=3
export ENABLE_EMAIL_NOTIFICATIONS=true
```

## 📖 Usage

### Basic Commands

```bash
# Get help
patch-manager --help

# Check system status
patch-manager patch status

# List servers
patch-manager server list

# Add a server
patch-manager server add --name web01.company.com --group web --os ubuntu

# Test connectivity
patch-manager server test

# Run pre-checks
patch-manager precheck run --server web01.company.com

# Patch a single server
patch-manager patch server --server web01.company.com

# Batch patch by quarter
patch-manager patch batch --quarter Q1

# Generate reports
patch-manager report generate --type summary --quarter Q1
```

### Advanced Usage

```bash
# Approve servers for patching
patch-manager approval approve --quarter Q1 --all

# Rollback a server
patch-manager patch rollback --server web01.company.com --reason "Service failure"

# Send email reports
patch-manager report email --type quarterly --to admin@company.com

# System maintenance
patch-manager system cleanup --days 30
patch-manager system health
```

## 📊 Command Reference

### Patch Operations
- `patch-manager patch server` - Patch single server
- `patch-manager patch batch` - Batch patch multiple servers
- `patch-manager patch status` - Show patching status
- `patch-manager patch rollback` - Rollback server

### Server Management
- `patch-manager server list` - List servers
- `patch-manager server add` - Add server
- `patch-manager server remove` - Remove server
- `patch-manager server update` - Update server
- `patch-manager server test` - Test connectivity
- `patch-manager server import` - Import from CSV
- `patch-manager server export` - Export to CSV

### Approval Workflow
- `patch-manager approval list` - List approvals
- `patch-manager approval approve` - Approve servers
- `patch-manager approval reject` - Reject servers

### Pre-checks
- `patch-manager precheck run` - Run pre-checks
- `patch-manager precheck results` - Show results

### Reporting
- `patch-manager report generate` - Generate reports
- `patch-manager report email` - Email reports

### System Operations
- `patch-manager system stats` - Show statistics
- `patch-manager system cleanup` - Clean old data
- `patch-manager system health` - Health check
- `patch-manager system test-email` - Test email

## 📧 Email Templates

The system includes 10+ professional email templates:

- **Pre-check Notifications** - Detailed validation results
- **Patching Started/Completed** - Status updates with metrics
- **Approval Requests** - Professional approval workflows
- **Daily/Quarterly Reports** - Comprehensive summaries
- **Critical Alerts** - Immediate attention notifications
- **Rollback Notifications** - Recovery status updates

## 📁 Data Management

### CSV Files
- `servers.csv` - Server inventory (35+ fields)
- `patch_history.csv` - Complete patching history
- `approvals.csv` - Approval workflow records
- `precheck_results.csv` - Pre-check validation results
- `rollback_history.csv` - Rollback operations

### Sample Server Record
```csv
Server Name,Host Group,Operating System,Environment,Server Timezone,Primary Owner,Q1 Patch Date,Q1 Patch Time,Q1 Approval Status,Current Quarter Patching Status,Active Status
web01.company.com,web,ubuntu,production,America/New_York,admin@company.com,2024-01-15,02:00,Approved,Completed,Active
```

## 🔒 Security Features

- **SSH Key-Based Authentication** - No password storage
- **Role-Based Access Control** - Admin, Operator, Viewer roles
- **Audit Trail** - Complete operation logging
- **Secure Password Handling** - Encrypted storage
- **Connection Pooling** - Efficient SSH management
- **Timeout Controls** - Prevent hanging operations

## 🔄 Workflow Example

### Monthly Patching Cycle

```bash
# 1. Generate server list for upcoming quarter
patch-manager server list --output csv > Q1_servers.csv

# 2. Import any new servers
patch-manager server import --file new_servers.csv

# 3. Request approvals
patch-manager approval approve --quarter Q1 --group non-prod

# 4. Run pre-checks (24 hours before)
patch-manager precheck run --quarter Q1

# 5. Execute patching
patch-manager patch batch --quarter Q1 --group non-prod
patch-manager patch batch --quarter Q1 --group prod

# 6. Generate reports
patch-manager report generate --type quarterly --quarter Q1
patch-manager report email --type summary --quarter Q1
```

## 🔧 Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   ```bash
   # Test SSH key
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
   
   # Test connection
   patch-manager server test --servers web01.company.com
   ```

2. **Permission Denied**
   ```bash
   # Check sudo access
   patch-manager precheck run --server web01.company.com
   ```

3. **Email Errors**
   ```bash
   # Test email configuration
   patch-manager system test-email --to admin@company.com
   ```

### Log Files
- Main Log: `/var/log/linux_patching_automation/patching.log`
- Error Log: `/var/log/linux_patching_automation/patching_errors.log`
- Audit Log: `/var/log/linux_patching_automation/patching_audit.log`

### Debug Mode
```bash
# Enable debug logging
patch-manager --debug patch server --server web01.company.com
```

## 🚀 Production Deployment

### System Requirements
- **OS**: Ubuntu 18.04+, CentOS 7+, RHEL 7+, Debian 9+
- **Python**: 3.6+
- **Memory**: 2GB minimum, 4GB recommended
- **Disk**: 10GB minimum, 50GB recommended
- **Network**: SSH and SNMP access to target servers

### Service Management
```bash
# Start service
sudo systemctl start linux-patching

# Check status
sudo systemctl status linux-patching

# View logs
sudo journalctl -u linux-patching -f
```

### Cron Schedule
```bash
# Daily pre-checks at 2 AM
0 2 * * * patch-manager precheck run --auto

# Weekly reports on Monday at 8 AM
0 8 * * 1 patch-manager report generate --type weekly

# Monthly cleanup on first day at 3 AM
0 3 1 * * patch-manager system cleanup --days 30 --confirm
```

## 📈 Performance

### Benchmarks
- **Parallel Patching**: Up to 20 servers simultaneously
- **SSH Connections**: Connection pooling for efficiency
- **Email Queue**: Async processing with retry logic
- **Database**: Optimized CSV operations
- **Memory Usage**: ~50MB baseline, ~200MB during operations

### Optimization Tips
```bash
# Tune parallel processing
export MAX_PARALLEL_PATCHES=10

# Optimize timeouts
export SSH_TIMEOUT=15
export PATCH_TIMEOUT_MINUTES=90

# Enable performance logging
export LOG_LEVEL=DEBUG
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_ssh_handler.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Integration Tests
```bash
# Test end-to-end workflow
patch-manager patch server --server localhost --dry-run

# Test email functionality
patch-manager system test-email --to test@company.com

# Test all server connectivity
patch-manager server test --parallel
```

## 📚 Documentation

### API Documentation
- Generate with: `sphinx-build -b html docs/ docs/_build/`
- View at: `docs/_build/index.html`

### Manual Pages
- `man patch-manager` - Main command reference
- `man patching-cli` - Alternative interface

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/company/linux-patching-automation.git

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run linting
flake8 .
black .
mypy .
```

### Code Style
- **Python**: PEP 8 with Black formatting
- **Documentation**: Google-style docstrings
- **Testing**: pytest with >90% coverage
- **Type Hints**: mypy for type checking

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Getting Help
- **Documentation**: Check the `docs/` directory
- **Issues**: Submit via GitHub Issues
- **Email**: patching@company.com

### FAQ

**Q: Can I patch Windows servers?**
A: No, this system is designed specifically for Linux servers.

**Q: How do I add custom pre-checks?**
A: Modify the `ssh_handler.py` file to add custom validation logic.

**Q: Can I integrate with ITSM tools?**
A: Yes, the system supports webhook notifications and API integration.

**Q: Is there a web interface?**
A: This is the CLI-only version. A web interface is available separately.

## 🔮 Roadmap

### Version 2.0 (Planned)
- [ ] Container support (Docker/Kubernetes)
- [ ] REST API interface
- [ ] Plugin system for custom integrations
- [ ] Advanced scheduling with calendars
- [ ] Multi-tenant support
- [ ] Grafana dashboard integration
- [ ] Automated testing framework
- [ ] Configuration as code (YAML)

### Version 1.1 (In Progress)
- [ ] Improved error handling
- [ ] Performance optimizations
- [ ] Additional OS support
- [ ] Enhanced reporting
- [ ] Better documentation

---

**Made with ❤️ by the Linux Patching Team**

*For a complete end-to-end Linux patching solution that just works.*