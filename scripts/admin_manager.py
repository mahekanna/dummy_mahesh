#!/usr/bin/env python3
"""
Admin Management System
Handles all administrative tasks including configuration, reports, and system maintenance
"""

import json
import os
import sys
import shutil
import hashlib
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import Logger
from utils.csv_handler import CSVHandler
from utils.email_sender import EmailSender
from database.models import DatabaseManager
from config.settings import Config

class AdminManager:
    def __init__(self):
        self.logger = Logger('admin_manager')
        self.csv_handler = CSVHandler()
        self.email_sender = EmailSender()
        self.db = DatabaseManager()
        self.config_path = os.path.join(Config.CONFIG_DIR, 'admin_config.json')
        self.groups_config_path = os.path.join(Config.CONFIG_DIR, 'server_groups.json')
        
    def load_admin_config(self):
        """Load admin configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("Admin config not found, creating default")
            return self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading admin config: {e}")
            return self._create_default_config()
    
    def save_admin_config(self, config):
        """Save admin configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info("Admin configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save admin config: {e}")
            return False
    
    def load_server_groups_config(self):
        """Load server groups configuration"""
        try:
            with open(self.groups_config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("Server groups config not found")
            return None
        except Exception as e:
            self.logger.error(f"Error loading server groups config: {e}")
            return None
    
    def save_server_groups_config(self, config):
        """Save server groups configuration"""
        try:
            with open(self.groups_config_path, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info("Server groups configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save server groups config: {e}")
            return False
    
    def update_admin_email(self, admin_email, backup_admin_email=None):
        """Update admin email addresses"""
        config = self.load_admin_config()
        config['admin_settings']['admin_email'] = admin_email
        if backup_admin_email:
            config['admin_settings']['backup_admin_email'] = backup_admin_email
        return self.save_admin_config(config)
    
    def generate_daily_report(self):
        """Generate daily patching report for admin"""
        try:
            servers = self.csv_handler.read_servers()
            current_quarter = Config.get_current_quarter()
            
            # Count servers by status
            stats = {
                'total_servers': len(servers),
                'approved': 0,
                'pending': 0,
                'scheduled': 0,
                'completed': 0,
                'failed': 0
            }
            
            upcoming_patches = []
            overdue_approvals = []
            
            for server in servers:
                approval_status = server.get(f'Q{current_quarter} Approval Status', 'Pending')
                patch_status = server.get('Current Quarter Patching Status', 'Pending')
                patch_date = server.get(f'Q{current_quarter} Patch Date')
                
                # Count by approval status
                if approval_status in ['Approved', 'Auto-Approved']:
                    stats['approved'] += 1
                else:
                    stats['pending'] += 1
                
                # Count by patch status
                if patch_status == 'Scheduled':
                    stats['scheduled'] += 1
                elif patch_status == 'Completed':
                    stats['completed'] += 1
                elif patch_status == 'Failed':
                    stats['failed'] += 1
                
                # Check for upcoming patches (next 7 days)
                if patch_date:
                    try:
                        patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                        days_until = (patch_dt - datetime.now()).days
                        if 0 <= days_until <= 7:
                            upcoming_patches.append({
                                'server': server['Server Name'],
                                'date': patch_date,
                                'time': server.get(f'Q{current_quarter} Patch Time', 'N/A'),
                                'days_until': days_until,
                                'owner': server.get('primary_owner', 'N/A')
                            })
                    except ValueError:
                        pass
                
                # Check for overdue approvals
                if approval_status == 'Pending' and patch_date:
                    try:
                        patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                        if patch_dt <= datetime.now() + timedelta(days=3):  # Due in 3 days
                            overdue_approvals.append({
                                'server': server['Server Name'],
                                'date': patch_date,
                                'owner': server.get('primary_owner', 'N/A')
                            })
                    except ValueError:
                        pass
            
            # Calculate approval percentage
            approval_percentage = (stats['approved'] / stats['total_servers'] * 100) if stats['total_servers'] > 0 else 0
            
            # Generate HTML sections for placeholders
            upcoming_patches_section = self._generate_upcoming_patches_section(upcoming_patches)
            overdue_approvals_section = self._generate_overdue_approvals_section(overdue_approvals)
            pending_action_text = self._generate_pending_action_text(stats, overdue_approvals)
            
            # Generate report
            report_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'quarter': f'Q{current_quarter}',
                'stats': stats,
                'approval_percentage': approval_percentage,
                'upcoming_patches': sorted(upcoming_patches, key=lambda x: x['days_until']),
                'overdue_approvals': overdue_approvals,
                'upcoming_patches_section': upcoming_patches_section,
                'overdue_approvals_section': overdue_approvals_section,
                'pending_action_text': pending_action_text,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return report_data
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            return None
    
    def generate_weekly_report(self):
        """Generate weekly patching report for admin"""
        try:
            # Get daily report data
            daily_data = self.generate_daily_report()
            
            # Add weekly-specific data
            servers = self.csv_handler.read_servers()
            current_quarter = Config.get_current_quarter()
            
            # Patches completed this week
            week_start = datetime.now() - timedelta(days=7)
            completed_this_week = []
            failed_this_week = []
            
            for server in servers:
                patch_status = server.get('Current Quarter Patching Status', 'Pending')
                patch_date = server.get(f'Q{current_quarter} Patch Date')
                
                if patch_date and patch_status in ['Completed', 'Failed']:
                    try:
                        patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                        if patch_dt >= week_start:
                            patch_info = {
                                'server': server['Server Name'],
                                'date': patch_date,
                                'time': server.get(f'Q{current_quarter} Patch Time', 'N/A'),
                                'owner': server.get('primary_owner', 'N/A'),
                                'location': server.get('location', 'N/A')
                            }
                            
                            if patch_status == 'Completed':
                                completed_this_week.append(patch_info)
                            else:
                                failed_this_week.append(patch_info)
                    except ValueError:
                        pass
            
            # Generate HTML sections for weekly template
            completed_this_week_section = self._generate_completed_patches_section(completed_this_week)
            failed_this_week_section = self._generate_failed_patches_section(failed_this_week)
            completed_this_week_summary = self._generate_completed_summary(completed_this_week)
            failed_this_week_summary = self._generate_failed_summary(failed_this_week)
            weekly_activity_summary = self._generate_weekly_activity_summary(completed_this_week, failed_this_week)
            action_items_text = self._generate_action_items_text(daily_data['stats'])
            next_week_text = self._generate_next_week_text(daily_data['upcoming_patches'])
            recommendation_text = self._generate_recommendation_text(failed_this_week, daily_data['stats'], daily_data['upcoming_patches'])
            
            weekly_data = daily_data.copy()
            weekly_data.update({
                'week_start': week_start.strftime('%Y-%m-%d'),
                'current_date': datetime.now().strftime('%Y-%m-%d'),
                'next_report_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'completed_this_week': completed_this_week,
                'failed_this_week': failed_this_week,
                'completed_this_week_section': completed_this_week_section,
                'failed_this_week_section': failed_this_week_section,
                'completed_this_week_summary': completed_this_week_summary,
                'failed_this_week_summary': failed_this_week_summary,
                'weekly_activity_summary': weekly_activity_summary,
                'action_items_text': action_items_text,
                'next_week_text': next_week_text,
                'recommendation_text': recommendation_text
            })
            
            return weekly_data
            
        except Exception as e:
            self.logger.error(f"Error generating weekly report: {e}")
            return None
    
    def send_daily_report(self):
        """Send daily report to admin"""
        config = self.load_admin_config()
        if not config['admin_settings']['notification_settings']['send_daily_reports']:
            return True
        
        report_data = self.generate_daily_report()
        if not report_data:
            return False
        
        # Load email template
        template_path = os.path.join(Config.TEMPLATES_DIR, 'admin_daily_report.html')
        try:
            with open(template_path, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            template = self._get_default_daily_template()
        
        # Generate email content
        email_content = template.format(**report_data)
        
        # Send to admin emails
        admin_email = config['admin_settings']['admin_email']
        backup_email = config['admin_settings'].get('backup_admin_email')
        
        subject = f"Daily Patching Report - {report_data['date']}"
        
        try:
            self.email_sender.send_email(admin_email, subject, email_content, is_html=True)
            self.logger.info(f"Daily report sent to {admin_email}")
            
            if backup_email:
                self.email_sender.send_email(backup_email, subject, email_content, is_html=True)
                self.logger.info(f"Daily report sent to {backup_email}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to send daily report: {e}")
            return False
    
    def send_weekly_report(self):
        """Send weekly report to admin"""
        config = self.load_admin_config()
        if not config['admin_settings']['notification_settings']['send_weekly_reports']:
            return True
        
        report_data = self.generate_weekly_report()
        if not report_data:
            return False
        
        # Load email template
        template_path = os.path.join(Config.TEMPLATES_DIR, 'admin_weekly_report.html')
        try:
            with open(template_path, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            template = self._get_default_weekly_template()
        
        # Generate email content
        email_content = template.format(**report_data)
        
        # Send to admin emails
        admin_email = config['admin_settings']['admin_email']
        backup_email = config['admin_settings'].get('backup_admin_email')
        
        subject = f"Weekly Patching Report - Week of {report_data['week_start']}"
        
        try:
            self.email_sender.send_email(admin_email, subject, email_content, is_html=True)
            self.logger.info(f"Weekly report sent to {admin_email}")
            
            if backup_email:
                self.email_sender.send_email(backup_email, subject, email_content, is_html=True)
                self.logger.info(f"Weekly report sent to {backup_email}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to send weekly report: {e}")
            return False
    
    def send_monthly_report(self):
        """Send monthly report to admin"""
        config = self.load_admin_config()
        if not config['admin_settings']['notification_settings']['send_monthly_reports']:
            return True
        
        report_data = self.generate_monthly_report()
        if not report_data:
            return False
        
        # Load email template
        template_path = os.path.join(Config.TEMPLATES_DIR, 'admin_monthly_report.html')
        try:
            with open(template_path, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            template = self._get_default_monthly_template()
        
        # Generate email content
        email_content = template.format(**report_data)
        
        # Send to admin emails
        admin_email = config['admin_settings']['admin_email']
        backup_email = config['admin_settings'].get('backup_admin_email')
        
        subject = f"Monthly Patching Report - {report_data['month_name']} {report_data['year']}"
        
        try:
            self.email_sender.send_email(admin_email, subject, email_content, is_html=True)
            self.logger.info(f"Monthly report sent to {admin_email}")
            
            if backup_email:
                self.email_sender.send_email(backup_email, subject, email_content, is_html=True)
                self.logger.info(f"Monthly report sent to {backup_email}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to send monthly report: {e}")
            return False
    
    def generate_monthly_report(self):
        """Generate monthly patching report for admin"""
        try:
            # Get base data from weekly report
            weekly_data = self.generate_weekly_report()
            if not weekly_data:
                return None
            
            servers = self.csv_handler.read_servers()
            current_quarter = Config.get_current_quarter()
            
            # Calculate monthly data (last 30 days)
            month_start = datetime.now() - timedelta(days=30)
            current_date = datetime.now()
            
            completed_this_month = []
            failed_this_month = []
            
            for server in servers:
                patch_status = server.get('Current Quarter Patching Status', 'Pending')
                patch_date = server.get(f'Q{current_quarter} Patch Date')
                
                if patch_date and patch_status in ['Completed', 'Failed']:
                    try:
                        patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                        if patch_dt >= month_start:
                            patch_info = {
                                'server': server['Server Name'],
                                'date': patch_date,
                                'time': server.get(f'Q{current_quarter} Patch Time', 'N/A'),
                                'owner': server.get('primary_owner', 'N/A'),
                                'location': server.get('location', 'N/A')
                            }
                            
                            if patch_status == 'Completed':
                                completed_this_month.append(patch_info)
                            else:
                                failed_this_month.append(patch_info)
                    except ValueError:
                        pass
            
            # Calculate monthly metrics
            total_monthly_patches = len(completed_this_month) + len(failed_this_month)
            monthly_success_rate = (len(completed_this_month) / total_monthly_patches * 100) if total_monthly_patches > 0 else 0
            
            # Generate HTML sections
            monthly_activity_summary = self._generate_monthly_activity_summary(completed_this_month, failed_this_month)
            monthly_insights = self._generate_monthly_insights(weekly_data['stats'], completed_this_month, failed_this_month)
            
            monthly_data = weekly_data.copy()
            monthly_data.update({
                'month_start': month_start.strftime('%Y-%m-%d'),
                'month_name': current_date.strftime('%B'),
                'year': current_date.strftime('%Y'),
                'completed_this_month': completed_this_month,
                'failed_this_month': failed_this_month,
                'monthly_success_rate': monthly_success_rate,
                'total_monthly_patches': total_monthly_patches,
                'monthly_activity_summary': monthly_activity_summary,
                'monthly_insights': monthly_insights
            })
            
            return monthly_data
            
        except Exception as e:
            self.logger.error(f"Error generating monthly report: {e}")
            return None
    
    def sync_csv_to_database(self):
        """Sync CSV data to database daily"""
        try:
            config = self.load_admin_config()
            if not config['database_sync']['enabled']:
                return True
            
            # Backup current data if enabled
            if config['database_sync']['csv_sync_schedule']['backup_before_sync']:
                self._backup_csv_file()
            
            # Read servers from CSV
            servers = self.csv_handler.read_servers()
            
            # Connect to database
            self.db.connect()
            
            # Sync data
            synced_count = 0
            for server in servers:
                try:
                    # Insert or update server data
                    self.db.upsert_server(server)
                    synced_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to sync server {server.get('Server Name', 'Unknown')}: {e}")
            
            self.logger.info(f"Synced {synced_count} servers to database")
            return True
            
        except Exception as e:
            self.logger.error(f"Database sync failed: {e}")
            return False
    
    def cleanup_old_data(self):
        """Clean up old data based on retention settings"""
        try:
            config = self.load_admin_config()
            retention = config['database_sync']['data_retention']
            
            # Clean up historical data
            cutoff_date = datetime.now() - timedelta(days=retention['keep_historical_data_days'])
            
            # Clean up log files
            log_cutoff = datetime.now() - timedelta(days=retention['keep_log_files_days'])
            self._cleanup_log_files(log_cutoff)
            
            # Clean up backup files
            backup_cutoff = datetime.now() - timedelta(days=retention['keep_backup_files_days'])
            self._cleanup_backup_files(backup_cutoff)
            
            self.logger.info("Data cleanup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
            return False
    
    def _backup_csv_file(self):
        """Create backup of CSV file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(Config.PROJECT_ROOT, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_path = os.path.join(backup_dir, f'servers_backup_{timestamp}.csv')
            shutil.copy2(Config.CSV_FILE_PATH, backup_path)
            
            self.logger.info(f"CSV backup created: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to backup CSV file: {e}")
            return None
    
    def _cleanup_log_files(self, cutoff_date):
        """Clean up old log files"""
        try:
            log_dir = os.path.join(Config.PROJECT_ROOT, 'logs')
            if not os.path.exists(log_dir):
                return
            
            for filename in os.listdir(log_dir):
                file_path = os.path.join(log_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        self.logger.info(f"Removed old log file: {filename}")
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")
    
    def _cleanup_backup_files(self, cutoff_date):
        """Clean up old backup files"""
        try:
            backup_dir = os.path.join(Config.PROJECT_ROOT, 'backups')
            if not os.path.exists(backup_dir):
                return
            
            for filename in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        self.logger.info(f"Removed old backup file: {filename}")
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
    
    def _create_default_config(self):
        """Create default admin configuration"""
        default_config = {
            "admin_settings": {
                "admin_email": "admin@company.com",
                "backup_admin_email": "",
                "notification_settings": {
                    "send_daily_reports": True,
                    "send_weekly_reports": True,
                    "send_monthly_reports": True,
                    "send_patch_completion_reports": True,
                    "send_error_alerts": True
                }
            },
            "database_sync": {
                "enabled": True,
                "csv_sync_schedule": {
                    "frequency": "daily",
                    "time": "01:00",
                    "backup_before_sync": True
                }
            }
        }
        
        self.save_admin_config(default_config)
        return default_config
    
    def generate_report_data(self, report_type='daily'):
        """Generate report data for UI display"""
        try:
            if report_type == 'daily':
                return self.generate_daily_report()
            elif report_type == 'weekly':
                return self.generate_weekly_report()
            else:
                return self.generate_daily_report()
        except Exception as e:
            self.logger.error(f"Error generating {report_type} report data: {e}")
            return None

    def _get_default_daily_template(self):
        """Default daily report email template"""
        return """
        <html>
        <body>
        <h2>Daily Patching Report - {date}</h2>
        <h3>Quarter: {quarter}</h3>
        
        <h4>Summary Statistics</h4>
        <ul>
            <li>Total Servers: {stats[total_servers]}</li>
            <li>Approved: {stats[approved]}</li>
            <li>Pending Approval: {stats[pending]}</li>
            <li>Scheduled: {stats[scheduled]}</li>
            <li>Completed: {stats[completed]}</li>
            <li>Failed: {stats[failed]}</li>
        </ul>
        
        <h4>Upcoming Patches (Next 7 Days)</h4>
        <p>Check admin dashboard for detailed list</p>
        
        <h4>Overdue Approvals</h4>
        <p>Check admin dashboard for detailed list</p>
        </body>
        </html>
        """
    
    def _get_default_weekly_template(self):
        """Default weekly report email template"""
        return """
        <html>
        <body>
        <h2>Weekly Patching Report - Week of {week_start}</h2>
        <h3>Quarter: {quarter}</h3>
        
        <h4>This Week's Activity</h4>
        <ul>
            <li>Patches Completed: {completed_this_week}</li>
            <li>Patches Failed: {failed_this_week}</li>
        </ul>
        
        <h4>Overall Statistics</h4>
        <ul>
            <li>Total Servers: {stats[total_servers]}</li>
            <li>Approved: {stats[approved]}</li>
            <li>Pending Approval: {stats[pending]}</li>
        </ul>
        </body>
        </html>
        """
    
    def _generate_upcoming_patches_section(self, upcoming_patches):
        """Generate HTML section for upcoming patches"""
        if not upcoming_patches:
            return '''
            <div class="alert alert-info">
                <strong>No upcoming patches</strong> scheduled for the next 7 days.
            </div>
            '''
        
        html = '''
        <table class="table">
            <thead>
                <tr>
                    <th>Server Name</th>
                    <th>Patch Date</th>
                    <th>Patch Time</th>
                    <th>Days Until</th>
                    <th>Owner</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for patch in upcoming_patches:
            badge_class = 'badge-danger' if patch['days_until'] <= 1 else 'badge-warning' if patch['days_until'] <= 3 else 'badge-info'
            html += f'''
                <tr>
                    <td><strong>{patch['server']}</strong></td>
                    <td>{patch['date']}</td>
                    <td>{patch['time']}</td>
                    <td><span class="badge {badge_class}">{patch['days_until']} day(s)</span></td>
                    <td>{patch['owner']}</td>
                </tr>
            '''
        
        html += '''
            </tbody>
        </table>
        '''
        return html
    
    def _generate_overdue_approvals_section(self, overdue_approvals):
        """Generate HTML section for overdue approvals"""
        if not overdue_approvals:
            return '''
            <div class="alert alert-success">
                <strong>All approvals are up to date!</strong> No overdue approvals requiring attention.
            </div>
            '''
        
        html = '''
        <div class="alert alert-warning">
            <strong>Attention Required:</strong> The following servers have pending approvals that are due soon.
        </div>
        <table class="table">
            <thead>
                <tr>
                    <th>Server Name</th>
                    <th>Scheduled Date</th>
                    <th>Owner</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for approval in overdue_approvals:
            html += f'''
                <tr>
                    <td><strong>{approval['server']}</strong></td>
                    <td>{approval['date']}</td>
                    <td>{approval['owner']}</td>
                    <td><span class="badge badge-warning">Approval Needed</span></td>
                </tr>
            '''
        
        html += '''
            </tbody>
        </table>
        '''
        return html
    
    def _generate_pending_action_text(self, stats, overdue_approvals):
        """Generate pending action text for daily report"""
        if overdue_approvals:
            return f'''
            <div class="alert alert-warning">
                <strong>Action Required:</strong> {len(overdue_approvals)} servers need urgent approval for upcoming patches.
            </div>
            '''
        elif stats['pending'] > 0:
            return f'''
            <p><strong>Pending Actions:</strong> {stats['pending']} servers still need approval for this quarter.</p>
            '''
        else:
            return '''
            <div class="alert alert-success">
                <strong>All on track!</strong> No immediate actions required.
            </div>
            '''
    
    def _generate_completed_patches_section(self, completed_patches):
        """Generate HTML section for completed patches"""
        if not completed_patches:
            return ''
        
        html = '''
        <div class="section">
            <h2 class="section-title"><span class="icon">✅</span>Patches Completed This Week</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Server Name</th>
                        <th>Patch Date</th>
                        <th>Patch Time</th>
                        <th>Owner</th>
                        <th>Location</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for patch in completed_patches:
            html += f'''
                <tr>
                    <td><strong>{patch['server']}</strong></td>
                    <td>{patch['date']}</td>
                    <td>{patch['time']}</td>
                    <td>{patch['owner']}</td>
                    <td>{patch['location']}</td>
                    <td><span class="badge badge-success">Completed</span></td>
                </tr>
            '''
        
        html += '''
                </tbody>
            </table>
        </div>
        '''
        return html
    
    def _generate_failed_patches_section(self, failed_patches):
        """Generate HTML section for failed patches"""
        if not failed_patches:
            return ''
        
        html = '''
        <div class="section">
            <h2 class="section-title"><span class="icon">[FAILED]</span>Failed Patches This Week</h2>
            <div class="alert alert-danger">
                <strong>Attention Required:</strong> The following patches failed and may need investigation.
            </div>
            <table class="table">
                <thead>
                    <tr>
                        <th>Server Name</th>
                        <th>Scheduled Date</th>
                        <th>Scheduled Time</th>
                        <th>Owner</th>
                        <th>Location</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for patch in failed_patches:
            html += f'''
                <tr>
                    <td><strong>{patch['server']}</strong></td>
                    <td>{patch['date']}</td>
                    <td>{patch['time']}</td>
                    <td>{patch['owner']}</td>
                    <td>{patch['location']}</td>
                    <td><span class="badge badge-danger">Failed</span></td>
                </tr>
            '''
        
        html += '''
                </tbody>
            </table>
        </div>
        '''
        return html
    
    def _generate_completed_summary(self, completed_patches):
        """Generate completed patches summary for activity card"""
        if not completed_patches:
            return '''
            <div class="alert alert-info">
                No patches completed this week.
            </div>
            '''
        
        return f'''
        <div class="stat-number" style="color: #28a745; font-size: 3em; margin-bottom: 10px;">
            {len(completed_patches)}
        </div>
        <p class="text-muted">Patches successfully completed</p>
        '''
    
    def _generate_failed_summary(self, failed_patches):
        """Generate failed patches summary for activity card"""
        if not failed_patches:
            return '''
            <div class="alert alert-success">
                No patch failures this week!
            </div>
            '''
        
        return f'''
        <div class="stat-number" style="color: #dc3545; font-size: 3em; margin-bottom: 10px;">
            {len(failed_patches)}
        </div>
        <p class="text-muted">Patches that failed</p>
        '''
    
    def _generate_weekly_activity_summary(self, completed_patches, failed_patches):
        """Generate weekly activity summary"""
        if not completed_patches and not failed_patches:
            return '<p><strong>Weekly Activity:</strong> No patches executed this week</p>'
        
        total_patches = len(completed_patches) + len(failed_patches)
        success_rate = (len(completed_patches) / total_patches * 100) if total_patches > 0 else 0
        
        html = f'<p><strong>Weekly Activity:</strong> {len(completed_patches)} patches completed, {len(failed_patches)} failed</p>'
        
        if completed_patches:
            html += f'<p><strong>Success Rate:</strong> {success_rate:.1f}% this week</p>'
        
        return html
    
    def _generate_action_items_text(self, stats):
        """Generate action items text"""
        if stats['pending'] > 0:
            return f'<p><strong>Action Items:</strong> {stats["pending"]} servers still need approval</p>'
        return ''
    
    def _generate_next_week_text(self, upcoming_patches):
        """Generate next week text"""
        if upcoming_patches:
            return f'<p><strong>Next Week:</strong> {len(upcoming_patches)} patches scheduled in the next 7 days</p>'
        return ''
    
    def _generate_recommendation_text(self, failed_patches, stats, upcoming_patches):
        """Generate recommendation text"""
        if failed_patches:
            return 'Review and address the failed patches listed above. Consider rescheduling if necessary.'
        elif stats['pending'] > 10:
            return 'Focus on getting pending approvals to stay on track for the quarter.'
        elif upcoming_patches:
            return 'Monitor upcoming patches and ensure all pre-checks are completed.'
        else:
            return 'System is running smoothly. Continue monitoring for any new requirements.'
    
    def _generate_monthly_activity_summary(self, completed_patches, failed_patches):
        """Generate monthly activity summary"""
        if not completed_patches and not failed_patches:
            return '<p><strong>Monthly Activity:</strong> No patches executed this month</p>'
        
        total_patches = len(completed_patches) + len(failed_patches)
        success_rate = (len(completed_patches) / total_patches * 100) if total_patches > 0 else 0
        
        html = f'<p><strong>Monthly Activity:</strong> {len(completed_patches)} patches completed, {len(failed_patches)} failed</p>'
        html += f'<p><strong>Monthly Success Rate:</strong> {success_rate:.1f}%</p>'
        
        return html
    
    def _generate_monthly_insights(self, stats, completed_patches, failed_patches):
        """Generate monthly insights"""
        total_patches = len(completed_patches) + len(failed_patches)
        
        html = '<div class="monthly-insights">'
        html += f'<h4>Monthly Performance Insights</h4>'
        
        if total_patches > 0:
            html += f'<p><strong>Patch Volume:</strong> {total_patches} patches executed this month</p>'
            
            if len(completed_patches) > len(failed_patches):
                html += f'<p>✅ <strong>Positive Trend:</strong> More patches completed successfully than failed</p>'
            elif len(failed_patches) > 0:
                html += f'<p><strong>Attention Needed:</strong> {len(failed_patches)} patches failed and may need follow-up</p>'
        
        approval_rate = (stats['approved'] / stats['total_servers'] * 100) if stats['total_servers'] > 0 else 0
        if approval_rate > 80:
            html += f'<p>🎯 <strong>Approval Progress:</strong> {approval_rate:.1f}% of servers approved - excellent progress!</p>'
        elif approval_rate > 60:
            html += f'<p>📈 <strong>Approval Progress:</strong> {approval_rate:.1f}% of servers approved - good progress</p>'
        else:
            html += f'<p>🔄 <strong>Approval Progress:</strong> {approval_rate:.1f}% of servers approved - needs acceleration</p>'
        
        html += '</div>'
        return html
    
    def _get_default_monthly_template(self):
        """Default monthly report email template"""
        return """
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: #007bff; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }}
                .stat-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                .stat-label {{ color: #6c757d; font-size: 0.9em; }}
                .section {{ margin-bottom: 30px; }}
                .section-title {{ color: #495057; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-bottom: 15px; }}
                .monthly-insights {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Monthly Patching Report</h1>
                    <p>{month_name} {year} | Quarter: {quarter}</p>
                </div>
                
                <div class="section">
                    <h2 class="section-title">Monthly Overview</h2>
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-number">{total_monthly_patches}</div>
                            <div class="stat-label">Total Patches</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #28a745;">{completed_this_month}</div>
                            <div class="stat-label">Completed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #dc3545;">{failed_this_month}</div>
                            <div class="stat-label">Failed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #17a2b8;">{monthly_success_rate:.1f}%</div>
                            <div class="stat-label">Success Rate</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2 class="section-title">Monthly Performance</h2>
                    {monthly_activity_summary}
                </div>
                
                <div class="section">
                    <h2 class="section-title">System Status</h2>
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-number">{stats[total_servers]}</div>
                            <div class="stat-label">Total Servers</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #28a745;">{stats[approved]}</div>
                            <div class="stat-label">Approved</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #ffc107;">{stats[pending]}</div>
                            <div class="stat-label">Pending</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" style="color: #17a2b8;">{approval_percentage:.1f}%</div>
                            <div class="stat-label">Approval Rate</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    {monthly_insights}
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 0.9em; text-align: center;">
                    <p>Monthly report for {month_name} {year} covering period from {month_start} to {current_date}</p>
                    <p>Report generated at: {generation_time}</p>
                </div>
            </div>
        </body>
        </html>
        """

if __name__ == "__main__":
    admin_manager = AdminManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "daily-report":
            admin_manager.send_daily_report()
        elif command == "weekly-report":
            admin_manager.send_weekly_report()
        elif command == "monthly-report":
            admin_manager.send_monthly_report()
        elif command == "sync-database":
            admin_manager.sync_csv_to_database()
        elif command == "cleanup":
            admin_manager.cleanup_old_data()
        else:
            print("Usage: python admin_manager.py [daily-report|weekly-report|monthly-report|sync-database|cleanup]")
    else:
        print("Admin Manager - Available commands:")
        print("  daily-report    - Send daily report to admin")
        print("  weekly-report   - Send weekly report to admin")
        print("  monthly-report  - Send monthly report to admin")
        print("  sync-database   - Sync CSV to database")
        print("  cleanup         - Clean up old data")