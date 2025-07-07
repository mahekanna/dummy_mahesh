#!/usr/bin/env python3
"""
Task Scheduler for automated admin operations
Handles daily, weekly, and monthly tasks
"""

import schedule
import time
import sys
import os
from datetime import datetime, timedelta
from utils.logger import Logger
from scripts.admin_manager import AdminManager
from scripts.ldap_manager import LDAPScheduler

class TaskScheduler:
    def __init__(self):
        self.logger = Logger('scheduler')
        self.admin_manager = AdminManager()
        self.ldap_scheduler = LDAPScheduler()
        
    def setup_schedules(self):
        """Setup all scheduled tasks"""
        config = self.admin_manager.load_admin_config()
        
        # Daily tasks
        daily_time = config.get('admin_settings', {}).get('report_schedule', {}).get('daily_report_time', '08:00')
        schedule.every().day.at(daily_time).do(self.run_daily_tasks)
        
        # Database sync (daily at 1 AM)
        schedule.every().day.at("01:00").do(self.run_database_sync)
        
        # Weekly tasks
        weekly_day = config.get('admin_settings', {}).get('report_schedule', {}).get('weekly_report_day', 'monday')
        weekly_time = config.get('admin_settings', {}).get('report_schedule', {}).get('weekly_report_time', '09:00')
        getattr(schedule.every(), weekly_day.lower()).at(weekly_time).do(self.run_weekly_tasks)
        
        # LDAP sync (daily at 2 AM)
        schedule.every().day.at("02:00").do(self.run_ldap_sync)
        
        # Data cleanup (weekly on Sunday at 3 AM)
        schedule.every().sunday.at("03:00").do(self.run_cleanup_tasks)
        
        # System health check (every 6 hours)
        schedule.every(6).hours.do(self.run_health_check)
        
        self.logger.info("Task scheduler initialized with all schedules")
        
    def run_daily_tasks(self):
        """Run daily administrative tasks"""
        self.logger.info("Starting daily tasks")
        
        try:
            # Send daily report
            if self.admin_manager.send_daily_report():
                self.logger.info("Daily report sent successfully")
            else:
                self.logger.error("Failed to send daily report")
                
        except Exception as e:
            self.logger.error(f"Error in daily tasks: {e}")
    
    def run_weekly_tasks(self):
        """Run weekly administrative tasks"""
        self.logger.info("Starting weekly tasks")
        
        try:
            # Send weekly report
            if self.admin_manager.send_weekly_report():
                self.logger.info("Weekly report sent successfully")
            else:
                self.logger.error("Failed to send weekly report")
                
        except Exception as e:
            self.logger.error(f"Error in weekly tasks: {e}")
    
    def run_database_sync(self):
        """Run database synchronization"""
        self.logger.info("Starting database sync")
        
        try:
            if self.admin_manager.sync_csv_to_database():
                self.logger.info("Database sync completed successfully")
            else:
                self.logger.error("Database sync failed")
                
        except Exception as e:
            self.logger.error(f"Error in database sync: {e}")
    
    def run_ldap_sync(self):
        """Run LDAP user synchronization"""
        self.logger.info("Starting LDAP sync")
        
        try:
            self.ldap_scheduler.run_scheduled_sync()
            
        except Exception as e:
            self.logger.error(f"Error in LDAP sync: {e}")
    
    def run_cleanup_tasks(self):
        """Run data cleanup tasks"""
        self.logger.info("Starting cleanup tasks")
        
        try:
            if self.admin_manager.cleanup_old_data():
                self.logger.info("Data cleanup completed successfully")
            else:
                self.logger.error("Data cleanup failed")
                
        except Exception as e:
            self.logger.error(f"Error in cleanup tasks: {e}")
    
    def run_health_check(self):
        """Run system health check"""
        self.logger.info("Running system health check")
        
        try:
            # Check disk space
            disk_usage = self._check_disk_space()
            
            # Check log file sizes
            log_sizes = self._check_log_sizes()
            
            # Check CSV file integrity
            csv_integrity = self._check_csv_integrity()
            
            # Alert if any issues
            if disk_usage > 90:
                self.logger.warning(f"High disk usage: {disk_usage}%")
                self._send_health_alert("High disk usage", f"Disk usage is at {disk_usage}%")
            
            if any(size > 100 for size in log_sizes.values()):  # 100MB
                large_logs = [f for f, size in log_sizes.items() if size > 100]
                self.logger.warning(f"Large log files detected: {large_logs}")
                self._send_health_alert("Large log files", f"Log files need attention: {large_logs}")
            
            if not csv_integrity:
                self.logger.error("CSV file integrity check failed")
                self._send_health_alert("CSV integrity failure", "CSV file may be corrupted")
                
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
    
    def _check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            usage_percent = (used / total) * 100
            return round(usage_percent, 1)
        except:
            return 0
    
    def _check_log_sizes(self):
        """Check log file sizes"""
        log_sizes = {}
        try:
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        log_sizes[filename] = round(size_mb, 2)
        except Exception as e:
            self.logger.error(f"Error checking log sizes: {e}")
        
        return log_sizes
    
    def _check_csv_integrity(self):
        """Check CSV file integrity"""
        try:
            servers = self.admin_manager.csv_handler.read_servers()
            
            # Check if we can read servers
            if not servers:
                return False
            
            # Check for required columns
            required_columns = ['Server Name', 'primary_owner']
            for server in servers[:1]:  # Check first server
                if not all(col in server for col in required_columns):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"CSV integrity check failed: {e}")
            return False
    
    def _send_health_alert(self, subject, message):
        """Send health alert to admin"""
        try:
            config = self.admin_manager.load_admin_config()
            if config['admin_settings']['notification_settings']['send_error_alerts']:
                admin_email = config['admin_settings']['admin_email']
                
                email_content = f"""
                <html>
                <body>
                <h2>System Health Alert</h2>
                <p><strong>Alert:</strong> {subject}</p>
                <p><strong>Details:</strong> {message}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Please check the system and take appropriate action if necessary.</p>
                </body>
                </html>
                """
                
                self.admin_manager.email_sender.send_email(
                    admin_email,
                    f"ALERT: {subject}",
                    email_content,
                    is_html=True
                )
                
        except Exception as e:
            self.logger.error(f"Failed to send health alert: {e}")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        self.setup_schedules()
        
        self.logger.info("Task scheduler started - running continuously")
        self.logger.info(f"Scheduled jobs: {len(schedule.jobs)}")
        
        for job in schedule.jobs:
            self.logger.info(f"  - {job}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
    
    def run_once(self, task_type):
        """Run a specific task once (for testing)"""
        self.logger.info(f"Running task once: {task_type}")
        
        if task_type == "daily":
            self.run_daily_tasks()
        elif task_type == "weekly":
            self.run_weekly_tasks()
        elif task_type == "database-sync":
            self.run_database_sync()
        elif task_type == "ldap-sync":
            self.run_ldap_sync()
        elif task_type == "cleanup":
            self.run_cleanup_tasks()
        elif task_type == "health-check":
            self.run_health_check()
        else:
            self.logger.error(f"Unknown task type: {task_type}")

if __name__ == "__main__":
    scheduler = TaskScheduler()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "run":
            scheduler.run_scheduler()
        elif sys.argv[1] == "test" and len(sys.argv) > 2:
            scheduler.run_once(sys.argv[2])
        else:
            print("Usage:")
            print("  python scheduler.py run                    # Run scheduler continuously")
            print("  python scheduler.py test daily             # Test daily tasks")
            print("  python scheduler.py test weekly            # Test weekly tasks")
            print("  python scheduler.py test database-sync     # Test database sync")
            print("  python scheduler.py test ldap-sync         # Test LDAP sync")
            print("  python scheduler.py test cleanup           # Test cleanup tasks")
            print("  python scheduler.py test health-check      # Test health check")
    else:
        print("Task Scheduler for Linux Patching Automation")
        print("Available commands:")
        print("  run      - Start the scheduler daemon")
        print("  test     - Run specific tasks once for testing")