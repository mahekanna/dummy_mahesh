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
    # WARNING: Set these via environment variables in production
    USE_SENDMAIL = os.getenv('USE_SENDMAIL', 'false').lower() == 'true'
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
    
    @staticmethod
    def get_current_quarter():
        """Get current quarter based on custom quarter definition"""
        current_month = datetime.now().month
        for quarter, details in Config.QUARTERS.items():
            if current_month in details['months']:
                return quarter
        return '1'  # Default to Q1 if something goes wrong
