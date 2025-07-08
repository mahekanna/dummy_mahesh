# config/settings.py
import os
from datetime import datetime

class Config:
    # Database Configuration
    # WARNING: Set these via environment variables in production
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'patching_db')
    DB_USER = os.getenv('DB_USER', 'patch_admin')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'CHANGE_ME_IN_PRODUCTION')
    
    # Email Configuration
    # Use system sendmail by default (no system config changes needed)
    USE_SENDMAIL = os.getenv('USE_SENDMAIL', 'true').lower() == 'true'
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.example.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'patching@example.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'CHANGE_ME_IN_PRODUCTION')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # Patching Configuration
    DEFAULT_PATCH_DAY = 'Thursday'
    FREEZE_PERIOD_START = 'Thursday'
    FREEZE_PERIOD_END = 'Tuesday'
    
    # Custom Quarters Definition (Updated as per requirements)
    QUARTERS = {
        '1': {'name': 'Q1', 'months': [11, 12, 1]},   # Nov to Jan
        '2': {'name': 'Q2', 'months': [2, 3, 4]},     # Feb to April
        '3': {'name': 'Q3', 'months': [5, 6, 7]},     # May to July
        '4': {'name': 'Q4', 'months': [8, 9, 10]}     # August to October
    }
    
    # Disk Space Thresholds (in percentage)
    DISK_THRESHOLD_ROOT = 80
    DISK_THRESHOLD_BOOT = 70
    DISK_THRESHOLD_VAR = 85
    
    # Timing Configuration
    PRECHECK_HOURS_BEFORE = 5
    SCHEDULE_HOURS_BEFORE = 3
    POST_PATCH_WAIT_MINUTES = 10
    
    # File Paths
    PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
    CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    CSV_FILE_PATH = os.path.join(DATA_DIR, 'servers.csv')
    LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
    TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'templates')
    
    # LDAP Configuration
    LDAP_ENABLED = os.getenv('LDAP_ENABLED', 'False').lower() == 'true'
    LDAP_SERVER = os.getenv('LDAP_SERVER', 'ldap://ldap.company.com')
    LDAP_BASE_DN = os.getenv('LDAP_BASE_DN', 'dc=company,dc=com')
    LDAP_BIND_DN = os.getenv('LDAP_BIND_DN', 'cn=admin,dc=company,dc=com')
    LDAP_BIND_PASSWORD = os.getenv('LDAP_BIND_PASSWORD', '')
    
    # Admin Control via Linux Netgroups
    ADMIN_NETGROUP = os.getenv('ADMIN_NETGROUP', 'patching_admins')
    
    # Authentication Settings
    ENABLE_FALLBACK_AUTH = os.getenv('ENABLE_FALLBACK_AUTH', 'True').lower() == 'true'
    
    # Remote Patching Script Configuration
    PATCHING_SCRIPT_PATH = os.getenv('PATCHING_SCRIPT_PATH', '/opt/scripts/patch_server.sh')
    VALIDATE_PATCHING_SCRIPT = os.getenv('VALIDATE_PATCHING_SCRIPT', 'True').lower() == 'true'
    
    # SSH Configuration for Remote Operations
    SSH_CONNECTION_TIMEOUT = int(os.getenv('SSH_CONNECTION_TIMEOUT', '30'))  # seconds
    SSH_COMMAND_TIMEOUT = int(os.getenv('SSH_COMMAND_TIMEOUT', '300'))       # seconds (5 minutes)
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def get_current_quarter():
        """Get current quarter based on custom quarter definition"""
        current_month = datetime.now().month
        for quarter, details in Config.QUARTERS.items():
            if current_month in details['months']:
                return quarter
        return '1'  # Default to Q1 if something goes wrong
