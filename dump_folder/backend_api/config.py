"""
API Configuration
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production-use-secure-key')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///../patching.db'
    )
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # API Settings
    API_TITLE = 'Linux Patching Automation API'
    API_VERSION = 'v1'
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'csv', 'json', 'txt'}
    
    # Email Configuration (from existing settings)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 25))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'False').lower() == 'true'
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'patching@localhost')
    
    # Paths (from existing config)
    CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), '../data/servers.csv')
    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '../templates')
    LOGS_DIR = os.path.join(os.path.dirname(__file__), '../logs')
    
    # SSH Configuration
    SSH_CONNECTION_TIMEOUT = 30
    SSH_COMMAND_TIMEOUT = 300
    MAX_RETRY_ATTEMPTS = 3
    
    # Patching Configuration
    PATCHING_SCRIPT_PATH = '/usr/local/bin/patch_server.sh'
    VALIDATE_PATCHING_SCRIPT = True
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    
    # Quarters definition (from existing config)
    QUARTERS = {
        '1': {'name': 'Q1', 'months': ['November', 'December', 'January']},
        '2': {'name': 'Q2', 'months': ['February', 'March', 'April']},
        '3': {'name': 'Q3', 'months': ['May', 'June', 'July']},
        '4': {'name': 'Q4', 'months': ['August', 'September', 'October']}
    }
    
    @staticmethod
    def get_current_quarter():
        """Get current quarter based on date"""
        from datetime import datetime
        month = datetime.now().month
        if month in [11, 12, 1]:
            return '1'
        elif month in [2, 3, 4]:
            return '2'
        elif month in [5, 6, 7]:
            return '3'
        else:
            return '4'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'