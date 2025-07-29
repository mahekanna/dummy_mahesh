"""
Comprehensive Logging Module for Linux Patching Automation
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import traceback

class PatchingLogger:
    """Enhanced logging class with multiple handlers and formatting options"""
    
    def __init__(self, name: str = 'patching', log_dir: str = 'logs', 
                 log_level: str = 'INFO', max_file_size: int = 10485760,
                 backup_count: int = 5):
        """
        Initialize the patching logger
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_file_size: Maximum log file size in bytes (default 10MB)
            backup_count: Number of backup files to keep
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set up formatters
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
        )
        
        self.simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.json_formatter = JsonFormatter()
        
        # Set up handlers
        self._setup_file_handlers(max_file_size, backup_count)
        self._setup_console_handler()
        
        # Log startup
        self.logger.info(f"Logging initialized for {name} with level {log_level}")
    
    def _setup_file_handlers(self, max_file_size: int, backup_count: int):
        """Set up rotating file handlers"""
        
        # Main log file - detailed logging
        main_log = self.log_dir / f"{self.name}.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log, maxBytes=max_file_size, backupCount=backup_count
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(main_handler)
        
        # Error log file - errors and critical only
        error_log = self.log_dir / f"{self.name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log, maxBytes=max_file_size, backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Audit log file - important events in JSON format
        audit_log = self.log_dir / f"{self.name}_audit.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_log, maxBytes=max_file_size, backupCount=backup_count
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(self.json_formatter)
        audit_handler.addFilter(AuditFilter())
        self.logger.addHandler(audit_handler)
    
    def _setup_console_handler(self):
        """Set up console handler with colors"""
        console_handler = ColoredConsoleHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.simple_formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
            kwargs['traceback'] = traceback.format_exc()
        
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message with optional exception"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
            kwargs['traceback'] = traceback.format_exc()
        
        self.logger.critical(message, extra=kwargs)
    
    def audit(self, event: str, server: str = None, user: str = None, 
              details: Dict[str, Any] = None, **kwargs):
        """Log audit event"""
        audit_data = {
            'event': event,
            'server': server,
            'user': user,
            'details': details or {},
            'audit': True,  # Flag for audit filter
            **kwargs
        }
        self.logger.info(f"AUDIT: {event}", extra=audit_data)
    
    def patch_started(self, server: str, quarter: str, user: str, **kwargs):
        """Log patch start event"""
        self.audit('patch_started', server=server, user=user, 
                  details={'quarter': quarter, **kwargs})
    
    def patch_completed(self, server: str, quarter: str, user: str, 
                       success: bool, duration: int, **kwargs):
        """Log patch completion event"""
        self.audit('patch_completed', server=server, user=user,
                  details={'quarter': quarter, 'success': success, 
                          'duration_minutes': duration, **kwargs})
    
    def patch_failed(self, server: str, quarter: str, user: str, 
                    error: str, **kwargs):
        """Log patch failure event"""
        self.audit('patch_failed', server=server, user=user,
                  details={'quarter': quarter, 'error': error, **kwargs})
    
    def rollback_started(self, server: str, reason: str, user: str, **kwargs):
        """Log rollback start event"""
        self.audit('rollback_started', server=server, user=user,
                  details={'reason': reason, **kwargs})
    
    def rollback_completed(self, server: str, user: str, success: bool, **kwargs):
        """Log rollback completion event"""
        self.audit('rollback_completed', server=server, user=user,
                  details={'success': success, **kwargs})
    
    def approval_requested(self, server: str, quarter: str, user: str, **kwargs):
        """Log approval request event"""
        self.audit('approval_requested', server=server, user=user,
                  details={'quarter': quarter, **kwargs})
    
    def approval_granted(self, server: str, quarter: str, approver: str, **kwargs):
        """Log approval granted event"""
        self.audit('approval_granted', server=server, user=approver,
                  details={'quarter': quarter, **kwargs})
    
    def approval_denied(self, server: str, quarter: str, approver: str, 
                       reason: str, **kwargs):
        """Log approval denied event"""
        self.audit('approval_denied', server=server, user=approver,
                  details={'quarter': quarter, 'reason': reason, **kwargs})
    
    def precheck_started(self, server: str, quarter: str, user: str, **kwargs):
        """Log precheck start event"""
        self.audit('precheck_started', server=server, user=user,
                  details={'quarter': quarter, **kwargs})
    
    def precheck_completed(self, server: str, quarter: str, user: str, 
                          passed: bool, issues: list = None, **kwargs):
        """Log precheck completion event"""
        self.audit('precheck_completed', server=server, user=user,
                  details={'quarter': quarter, 'passed': passed, 
                          'issues': issues or [], **kwargs})
    
    def server_added(self, server: str, user: str, **kwargs):
        """Log server addition event"""
        self.audit('server_added', server=server, user=user, **kwargs)
    
    def server_removed(self, server: str, user: str, **kwargs):
        """Log server removal event"""
        self.audit('server_removed', server=server, user=user, **kwargs)
    
    def server_updated(self, server: str, user: str, changes: Dict[str, Any], **kwargs):
        """Log server update event"""
        self.audit('server_updated', server=server, user=user,
                  details={'changes': changes, **kwargs})
    
    def get_log_files(self) -> Dict[str, str]:
        """Get paths to all log files"""
        return {
            'main_log': str(self.log_dir / f"{self.name}.log"),
            'error_log': str(self.log_dir / f"{self.name}_errors.log"),
            'audit_log': str(self.log_dir / f"{self.name}_audit.log")
        }
    
    def get_recent_logs(self, hours: int = 24, level: str = 'INFO') -> list:
        """Get recent log entries"""
        # This would need to be implemented to parse log files
        # For now, return empty list
        return []
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob('*.log.*'):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.info(f"Deleted old log file: {log_file}")
                except Exception as e:
                    self.error(f"Failed to delete old log file {log_file}", error=e)

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'message', 'exc_info', 'exc_text', 
                          'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

class AuditFilter(logging.Filter):
    """Filter to only pass audit events"""
    
    def filter(self, record):
        return getattr(record, 'audit', False)

class ColoredConsoleHandler(logging.StreamHandler):
    """Console handler with colored output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def emit(self, record):
        try:
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            
            # Add color to the message
            if color:
                record.levelname = f"{color}{record.levelname}{reset}"
            
            super().emit(record)
        except Exception:
            self.handleError(record)

# Global logger instance
_logger_instance = None

def get_logger(name: str = 'patching', **kwargs) -> PatchingLogger:
    """Get or create logger instance"""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = PatchingLogger(name, **kwargs)
    
    return _logger_instance

def setup_logger(name: str = 'patching', **kwargs) -> PatchingLogger:
    """Set up logger with configuration"""
    return PatchingLogger(name, **kwargs)

# Convenience functions
def debug(message: str, **kwargs):
    """Log debug message using global logger"""
    logger = get_logger()
    logger.debug(message, **kwargs)

def info(message: str, **kwargs):
    """Log info message using global logger"""
    logger = get_logger()
    logger.info(message, **kwargs)

def warning(message: str, **kwargs):
    """Log warning message using global logger"""
    logger = get_logger()
    logger.warning(message, **kwargs)

def error(message: str, error: Optional[Exception] = None, **kwargs):
    """Log error message using global logger"""
    logger = get_logger()
    logger.error(message, error=error, **kwargs)

def critical(message: str, error: Optional[Exception] = None, **kwargs):
    """Log critical message using global logger"""
    logger = get_logger()
    logger.critical(message, error=error, **kwargs)

def audit(event: str, **kwargs):
    """Log audit event using global logger"""
    logger = get_logger()
    logger.audit(event, **kwargs)

# Context manager for logging operations
class LogContext:
    """Context manager for logging operations with automatic success/failure tracking"""
    
    def __init__(self, operation: str, server: str = None, user: str = None, 
                 logger: PatchingLogger = None):
        self.operation = operation
        self.server = server
        self.user = user
        self.logger = logger or get_logger()
        self.start_time = None
        self.success = False
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.operation}", 
                        server=self.server, user=self.user)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation} successfully", 
                            server=self.server, user=self.user, 
                            duration_seconds=duration)
        else:
            self.logger.error(f"Failed {self.operation}", 
                             server=self.server, user=self.user,
                             duration_seconds=duration, error=exc_val)
        
        return False  # Don't suppress exceptions
    
    def set_success(self):
        """Mark operation as successful"""
        self.success = True

# Example usage and testing
if __name__ == "__main__":
    # Example of using the logging system
    logger = setup_logger('test_patching', log_level='DEBUG')
    
    # Test basic logging
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test audit logging
    logger.audit("system_startup", user="admin", 
                details={"version": "1.0.0", "environment": "production"})
    
    # Test patch lifecycle logging
    logger.patch_started("web01.company.com", "Q1", "admin")
    logger.patch_completed("web01.company.com", "Q1", "admin", 
                          success=True, duration=45)
    
    # Test context manager
    with LogContext("server_patching", server="web01.company.com", 
                   user="admin", logger=logger):
        # Simulate some work
        import time
        time.sleep(0.1)
        # Operation completes successfully
    
    # Test error with context manager
    try:
        with LogContext("failing_operation", server="web02.company.com", 
                       user="admin", logger=logger):
            raise Exception("Something went wrong")
    except Exception:
        pass  # Exception is logged by context manager
    
    print("Logging test completed. Check the logs/ directory for output files.")