"""
Configuration Settings for Linux Patching Automation
"""

import os
from pathlib import Path
from typing import List, Dict, Any

class Config:
    """Configuration class for patching automation"""
    
    def __init__(self):
        # Base paths
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.DATA_DIR = self.BASE_DIR / 'data'
        self.LOG_DIR = self.BASE_DIR / 'logs'
        self.ARCHIVE_DIR = self.DATA_DIR / 'archives'
        self.REPORTS_DIR = self.DATA_DIR / 'reports'
        
        # Ensure directories exist
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOG_DIR.mkdir(exist_ok=True)
        self.ARCHIVE_DIR.mkdir(exist_ok=True)
        self.REPORTS_DIR.mkdir(exist_ok=True)
        
        # CSV Files
        self.SERVERS_CSV = self.DATA_DIR / 'servers.csv'
        self.PATCH_HISTORY_CSV = self.DATA_DIR / 'patch_history.csv'
        self.APPROVAL_CSV = self.DATA_DIR / 'approvals.csv'
        self.PRECHECK_CSV = self.DATA_DIR / 'precheck_results.csv'
        self.ROLLBACK_CSV = self.DATA_DIR / 'rollback_history.csv'
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # Email Configuration
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '25'))
        self.SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'False').lower() == 'true'
        self.SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'False').lower() == 'true'
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
        self.EMAIL_FROM = os.getenv('EMAIL_FROM', 'patching@company.com')
        self.ADMIN_EMAILS = os.getenv('ADMIN_EMAILS', '').split(',') if os.getenv('ADMIN_EMAILS') else []
        
        # Patching Configuration
        self.PRECHECK_HOURS_BEFORE = int(os.getenv('PRECHECK_HOURS_BEFORE', '24'))
        self.PATCHING_WINDOW_HOURS = int(os.getenv('PATCHING_WINDOW_HOURS', '4'))
        self.MAX_PARALLEL_PATCHES = int(os.getenv('MAX_PARALLEL_PATCHES', '5'))
        self.PATCH_TIMEOUT_MINUTES = int(os.getenv('PATCH_TIMEOUT_MINUTES', '120'))
        self.REBOOT_TIMEOUT = int(os.getenv('REBOOT_TIMEOUT', '300'))
        
        # SSH Configuration
        self.SSH_TIMEOUT = int(os.getenv('SSH_TIMEOUT', '30'))
        self.SSH_KEY_PATH = os.getenv('SSH_KEY_PATH', os.path.expanduser('~/.ssh/id_rsa'))
        self.SSH_DEFAULT_USER = os.getenv('SSH_DEFAULT_USER', 'patchadmin')
        self.SSH_DEFAULT_PORT = int(os.getenv('SSH_DEFAULT_PORT', '22'))
        
        # SNMP Configuration
        self.SNMP_COMMUNITY = os.getenv('SNMP_COMMUNITY', 'public')
        self.SNMP_TIMEOUT = int(os.getenv('SNMP_TIMEOUT', '10'))
        self.SNMP_RETRIES = int(os.getenv('SNMP_RETRIES', '3'))
        
        # Timezone Configuration
        self.DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')
        
        # Security Configuration
        self.ENCRYPT_PASSWORDS = os.getenv('ENCRYPT_PASSWORDS', 'True').lower() == 'true'
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
        
        # Backup Configuration
        self.BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        self.AUTO_BACKUP = os.getenv('AUTO_BACKUP', 'True').lower() == 'true'
        
        # Notification Configuration
        self.ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'True').lower() == 'true'
        self.NOTIFICATION_DELAY_SECONDS = int(os.getenv('NOTIFICATION_DELAY_SECONDS', '5'))
        
        # Performance Configuration
        self.CONNECTION_POOL_SIZE = int(os.getenv('CONNECTION_POOL_SIZE', '10'))
        self.OPERATION_TIMEOUT = int(os.getenv('OPERATION_TIMEOUT', '3600'))
        
        # Feature Flags
        self.ENABLE_ROLLBACK = os.getenv('ENABLE_ROLLBACK', 'True').lower() == 'true'
        self.ENABLE_PRECHECK = os.getenv('ENABLE_PRECHECK', 'True').lower() == 'true'
        self.ENABLE_POSTCHECK = os.getenv('ENABLE_POSTCHECK', 'True').lower() == 'true'
        self.ENABLE_AUTO_REBOOT = os.getenv('ENABLE_AUTO_REBOOT', 'True').lower() == 'true'
        
        # Approval Configuration
        self.REQUIRE_APPROVAL = os.getenv('REQUIRE_APPROVAL', 'True').lower() == 'true'
        self.AUTO_APPROVE_GROUPS = os.getenv('AUTO_APPROVE_GROUPS', '').split(',') if os.getenv('AUTO_APPROVE_GROUPS') else []
        self.APPROVAL_TIMEOUT_HOURS = int(os.getenv('APPROVAL_TIMEOUT_HOURS', '72'))
        
        # Reporting Configuration
        self.GENERATE_DAILY_REPORTS = os.getenv('GENERATE_DAILY_REPORTS', 'True').lower() == 'true'
        self.GENERATE_WEEKLY_REPORTS = os.getenv('GENERATE_WEEKLY_REPORTS', 'True').lower() == 'true'
        self.GENERATE_MONTHLY_REPORTS = os.getenv('GENERATE_MONTHLY_REPORTS', 'True').lower() == 'true'
        self.REPORT_RECIPIENTS = os.getenv('REPORT_RECIPIENTS', '').split(',') if os.getenv('REPORT_RECIPIENTS') else []
        
        # Maintenance Configuration
        self.MAINTENANCE_WINDOW_START = os.getenv('MAINTENANCE_WINDOW_START', '02:00')
        self.MAINTENANCE_WINDOW_END = os.getenv('MAINTENANCE_WINDOW_END', '06:00')
        self.MAINTENANCE_DAYS = os.getenv('MAINTENANCE_DAYS', 'Saturday,Sunday').split(',')
        
        # Error Handling Configuration
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        self.RETRY_DELAY_SECONDS = int(os.getenv('RETRY_DELAY_SECONDS', '60'))
        self.ESCALATION_THRESHOLD = int(os.getenv('ESCALATION_THRESHOLD', '5'))
        
        # Disk Space Thresholds
        self.DISK_SPACE_WARNING_THRESHOLD = int(os.getenv('DISK_SPACE_WARNING_THRESHOLD', '80'))
        self.DISK_SPACE_CRITICAL_THRESHOLD = int(os.getenv('DISK_SPACE_CRITICAL_THRESHOLD', '90'))
        
        # Load Average Thresholds
        self.LOAD_AVERAGE_WARNING_THRESHOLD = float(os.getenv('LOAD_AVERAGE_WARNING_THRESHOLD', '5.0'))
        self.LOAD_AVERAGE_CRITICAL_THRESHOLD = float(os.getenv('LOAD_AVERAGE_CRITICAL_THRESHOLD', '10.0'))
        
        # Memory Usage Thresholds
        self.MEMORY_WARNING_THRESHOLD = int(os.getenv('MEMORY_WARNING_THRESHOLD', '85'))
        self.MEMORY_CRITICAL_THRESHOLD = int(os.getenv('MEMORY_CRITICAL_THRESHOLD', '95'))
        
        # Service Configuration
        self.CRITICAL_SERVICES = os.getenv('CRITICAL_SERVICES', 'ssh,cron,systemd').split(',')
        self.SERVICE_CHECK_TIMEOUT = int(os.getenv('SERVICE_CHECK_TIMEOUT', '30'))
        
        # Package Management
        self.PACKAGE_CACHE_TTL = int(os.getenv('PACKAGE_CACHE_TTL', '3600'))
        self.ALLOW_KERNEL_UPDATES = os.getenv('ALLOW_KERNEL_UPDATES', 'True').lower() == 'true'
        self.EXCLUDE_PACKAGES = os.getenv('EXCLUDE_PACKAGES', '').split(',') if os.getenv('EXCLUDE_PACKAGES') else []
        
        # Scheduling Configuration
        self.SCHEDULER_ENABLED = os.getenv('SCHEDULER_ENABLED', 'True').lower() == 'true'
        self.SCHEDULER_INTERVAL_MINUTES = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', '60'))
        self.SCHEDULER_MAX_JOBS = int(os.getenv('SCHEDULER_MAX_JOBS', '50'))
        
        # Compliance Configuration
        self.COMPLIANCE_CHECKS = os.getenv('COMPLIANCE_CHECKS', 'True').lower() == 'true'
        self.AUDIT_RETENTION_DAYS = int(os.getenv('AUDIT_RETENTION_DAYS', '365'))
        self.SECURITY_PATCH_PRIORITY = os.getenv('SECURITY_PATCH_PRIORITY', 'high')
        
        # Integration Configuration
        self.TICKETING_SYSTEM = os.getenv('TICKETING_SYSTEM', '')
        self.TICKETING_URL = os.getenv('TICKETING_URL', '')
        self.TICKETING_USERNAME = os.getenv('TICKETING_USERNAME', '')
        self.TICKETING_PASSWORD = os.getenv('TICKETING_PASSWORD', '')
        
        # Monitoring Configuration
        self.MONITORING_ENABLED = os.getenv('MONITORING_ENABLED', 'True').lower() == 'true'
        self.MONITORING_INTERVAL = int(os.getenv('MONITORING_INTERVAL', '300'))
        self.HEALTH_CHECK_URL = os.getenv('HEALTH_CHECK_URL', '')
        
        # Development Configuration
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        self.DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'False').lower() == 'true'
        self.TESTING_MODE = os.getenv('TESTING_MODE', 'False').lower() == 'true'
        
        # Load custom configuration file if exists
        self._load_custom_config()
    
    def _load_custom_config(self):
        """Load custom configuration from file"""
        config_file = self.BASE_DIR / 'config' / 'local_settings.py'
        if config_file.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("local_settings", config_file)
                local_settings = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(local_settings)
                
                # Override settings from local file
                for attr_name in dir(local_settings):
                    if not attr_name.startswith('_'):
                        setattr(self, attr_name, getattr(local_settings, attr_name))
                        
            except Exception as e:
                print(f"Warning: Could not load local settings: {e}")
    
    def get_os_commands(self, os_type: str) -> Dict[str, str]:
        """Get OS-specific commands"""
        commands = {
            'ubuntu': {
                'update': 'sudo apt-get update',
                'upgrade': 'sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y',
                'list_upgrades': 'sudo apt list --upgradable',
                'autoremove': 'sudo apt-get autoremove -y',
                'clean': 'sudo apt-get clean',
                'reboot_required': '[ -f /var/run/reboot-required ] && echo "yes" || echo "no"'
            },
            'debian': {
                'update': 'sudo apt-get update',
                'upgrade': 'sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y',
                'list_upgrades': 'sudo apt list --upgradable',
                'autoremove': 'sudo apt-get autoremove -y',
                'clean': 'sudo apt-get clean',
                'reboot_required': '[ -f /var/run/reboot-required ] && echo "yes" || echo "no"'
            },
            'centos': {
                'update': 'sudo yum check-update || true',
                'upgrade': 'sudo yum update -y',
                'list_upgrades': 'sudo yum check-update',
                'clean': 'sudo yum clean all',
                'reboot_required': 'needs-restarting -r > /dev/null 2>&1 && echo "no" || echo "yes"'
            },
            'rhel': {
                'update': 'sudo yum check-update || true',
                'upgrade': 'sudo yum update -y',
                'list_upgrades': 'sudo yum check-update',
                'clean': 'sudo yum clean all',
                'reboot_required': 'needs-restarting -r > /dev/null 2>&1 && echo "no" || echo "yes"'
            },
            'fedora': {
                'update': 'sudo dnf check-update || true',
                'upgrade': 'sudo dnf update -y',
                'list_upgrades': 'sudo dnf check-update',
                'clean': 'sudo dnf clean all',
                'reboot_required': 'needs-restarting -r > /dev/null 2>&1 && echo "no" || echo "yes"'
            }
        }
        
        return commands.get(os_type.lower(), commands['ubuntu'])
    
    def get_timezone_mapping(self) -> Dict[str, str]:
        """Get timezone mapping"""
        return {
            'EST': 'America/New_York',
            'CST': 'America/Chicago',
            'MST': 'America/Denver',
            'PST': 'America/Los_Angeles',
            'EDT': 'America/New_York',
            'CDT': 'America/Chicago',
            'MDT': 'America/Denver',
            'PDT': 'America/Los_Angeles',
            'UTC': 'UTC',
            'GMT': 'Europe/London',
            'IST': 'Asia/Kolkata',
            'JST': 'Asia/Tokyo',
            'AEST': 'Australia/Sydney',
            'CEST': 'Europe/Berlin',
            'CET': 'Europe/Berlin'
        }
    
    def get_user_roles(self) -> Dict[str, List[str]]:
        """Get user roles and permissions"""
        return {
            'admin': [
                'patch:execute',
                'patch:rollback',
                'patch:force',
                'server:add',
                'server:remove',
                'server:update',
                'approval:approve',
                'approval:reject',
                'report:generate',
                'report:email',
                'system:cleanup',
                'system:health'
            ],
            'operator': [
                'patch:execute',
                'patch:rollback',
                'server:update',
                'approval:request',
                'report:generate',
                'system:health'
            ],
            'viewer': [
                'server:list',
                'patch:status',
                'approval:list',
                'report:view',
                'system:health'
            ]
        }
    
    def get_notification_templates(self) -> Dict[str, str]:
        """Get notification template names"""
        return {
            'precheck_notification': 'Pre-check Results',
            'patching_started': 'Patching Started',
            'patching_completed': 'Patching Completed',
            'approval_request': 'Approval Required',
            'daily_summary': 'Daily Summary',
            'quarterly_report': 'Quarterly Report',
            'critical_alert': 'Critical Alert',
            'rollback_notification': 'Rollback Notification'
        }
    
    def get_check_thresholds(self) -> Dict[str, Any]:
        """Get check thresholds"""
        return {
            'disk_space': {
                'warning': self.DISK_SPACE_WARNING_THRESHOLD,
                'critical': self.DISK_SPACE_CRITICAL_THRESHOLD
            },
            'load_average': {
                'warning': self.LOAD_AVERAGE_WARNING_THRESHOLD,
                'critical': self.LOAD_AVERAGE_CRITICAL_THRESHOLD
            },
            'memory_usage': {
                'warning': self.MEMORY_WARNING_THRESHOLD,
                'critical': self.MEMORY_CRITICAL_THRESHOLD
            }
        }
    
    def get_patch_windows(self) -> Dict[str, Dict[str, str]]:
        """Get quarterly patch windows"""
        return {
            'Q1': {
                'start_date': '01-15',
                'end_date': '01-31',
                'maintenance_window': f"{self.MAINTENANCE_WINDOW_START}-{self.MAINTENANCE_WINDOW_END}"
            },
            'Q2': {
                'start_date': '04-15',
                'end_date': '04-30',
                'maintenance_window': f"{self.MAINTENANCE_WINDOW_START}-{self.MAINTENANCE_WINDOW_END}"
            },
            'Q3': {
                'start_date': '07-15',
                'end_date': '07-31',
                'maintenance_window': f"{self.MAINTENANCE_WINDOW_START}-{self.MAINTENANCE_WINDOW_END}"
            },
            'Q4': {
                'start_date': '10-15',
                'end_date': '10-31',
                'maintenance_window': f"{self.MAINTENANCE_WINDOW_START}-{self.MAINTENANCE_WINDOW_END}"
            }
        }
    
    def get_escalation_rules(self) -> Dict[str, Any]:
        """Get escalation rules"""
        return {
            'failure_threshold': self.ESCALATION_THRESHOLD,
            'escalation_delay': self.RETRY_DELAY_SECONDS,
            'max_retries': self.MAX_RETRIES,
            'escalation_contacts': self.ADMIN_EMAILS
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required directories
        required_dirs = [self.DATA_DIR, self.LOG_DIR]
        for dir_path in required_dirs:
            if not dir_path.exists():
                issues.append(f"Required directory missing: {dir_path}")
        
        # Check SSH key
        if not os.path.exists(self.SSH_KEY_PATH):
            issues.append(f"SSH key not found: {self.SSH_KEY_PATH}")
        
        # Check email configuration
        if self.ENABLE_EMAIL_NOTIFICATIONS and not self.SMTP_SERVER:
            issues.append("SMTP server not configured but email notifications enabled")
        
        # Check thresholds
        if self.DISK_SPACE_WARNING_THRESHOLD >= self.DISK_SPACE_CRITICAL_THRESHOLD:
            issues.append("Disk space warning threshold must be less than critical threshold")
        
        if self.MEMORY_WARNING_THRESHOLD >= self.MEMORY_CRITICAL_THRESHOLD:
            issues.append("Memory warning threshold must be less than critical threshold")
        
        # Check parallel processing limits
        if self.MAX_PARALLEL_PATCHES > 20:
            issues.append("Maximum parallel patches should not exceed 20")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = {}
        
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                value = getattr(self, attr_name)
                if isinstance(value, Path):
                    config_dict[attr_name] = str(value)
                else:
                    config_dict[attr_name] = value
        
        return config_dict
    
    def save_to_file(self, filename: str):
        """Save configuration to file"""
        config_dict = self.to_dict()
        
        with open(filename, 'w') as f:
            import json
            json.dump(config_dict, f, indent=2, default=str)
    
    def load_from_file(self, filename: str):
        """Load configuration from file"""
        try:
            with open(filename, 'r') as f:
                import json
                config_dict = json.load(f)
            
            for key, value in config_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
        except Exception as e:
            print(f"Warning: Could not load configuration from {filename}: {e}")
    
    def __str__(self):
        """String representation of configuration"""
        return f"Config(DATA_DIR={self.DATA_DIR}, LOG_LEVEL={self.LOG_LEVEL}, MAX_PARALLEL_PATCHES={self.MAX_PARALLEL_PATCHES})"
    
    def __repr__(self):
        """Detailed string representation"""
        return self.__str__()

# Create global config instance
config = Config()

# Example usage
if __name__ == "__main__":
    # Example of using the configuration
    config = Config()
    
    print("Configuration Summary:")
    print(f"Data Directory: {config.DATA_DIR}")
    print(f"Log Level: {config.LOG_LEVEL}")
    print(f"Max Parallel Patches: {config.MAX_PARALLEL_PATCHES}")
    print(f"SSH Key Path: {config.SSH_KEY_PATH}")
    print(f"Email Enabled: {config.ENABLE_EMAIL_NOTIFICATIONS}")
    
    # Validate configuration
    issues = config.validate_config()
    if issues:
        print("\nConfiguration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nConfiguration is valid!")
    
    # Show OS commands for Ubuntu
    ubuntu_commands = config.get_os_commands('ubuntu')
    print(f"\nUbuntu Commands:")
    for cmd_name, cmd in ubuntu_commands.items():
        print(f"  {cmd_name}: {cmd}")
    
    # Show patch windows
    patch_windows = config.get_patch_windows()
    print(f"\nPatch Windows:")
    for quarter, window in patch_windows.items():
        print(f"  {quarter}: {window['start_date']} - {window['end_date']}")