# scripts/step7_email_handler.py
from utils.email_sender import EmailSender
from utils.logger import Logger
from config.settings import Config
from datetime import datetime
import os

class EmailHandler:
    def __init__(self):
        self.email_sender = EmailSender()
        self.logger = Logger('email_handler')
    
    def get_quarter_description(self, quarter):
        """Get quarter description"""
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        return quarter_descriptions.get(quarter, 'Unknown')
    
    def send_notification(self, notification_type, recipients, data=None):
        """Send notification based on type"""
        if notification_type == 'monthly_notice':
            self.send_monthly_notice(recipients, data)
        elif notification_type == 'weekly_reminder':
            self.send_weekly_reminder(recipients, data)
        elif notification_type == 'daily_reminder':
            self.send_daily_reminder(recipients, data)
        elif notification_type == 'completion':
            self.send_completion_notice(recipients, data)
        elif notification_type == 'failure':
            self.send_failure_notice(recipients, data)
        elif notification_type == 'precheck_alert':
            self.send_precheck_alert(recipients, data)
        else:
            self.logger.error(f"Unknown notification type: {notification_type}")
            return False
        
        return True
    
    def send_monthly_notice(self, recipients, data):
        """Send monthly notice to server owners"""
        template_path = os.path.join(Config.TEMPLATES_DIR, 'monthly_notice.html')
        
        if not os.path.exists(template_path):
            self.logger.error(f"Template not found: {template_path}")
            return False
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        quarter = data.get('quarter', '3')
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        quarter_description = self.get_quarter_description(quarter)
        
        for recipient, recipient_data in recipients.items():
            servers = recipient_data.get('servers', [])
            proposed_dates = recipient_data.get('proposed_dates', [])
            
            server_table = self.generate_server_table(servers, quarter)
            proposed_dates_list = '<br>'.join([f"• {date}" for date in proposed_dates])
            
            email_content = template.format(
                owner_email=recipient,
                quarter=quarter_name,
                proposed_dates=proposed_dates_list,
                server_table=server_table,
                deadline_date=data.get('deadline_date', 'Two weeks from now'),
                quarter_description=quarter_description
            )
            
            subject = f"Monthly Patching Notice - {quarter_name} Schedule Selection Required"
            self.email_sender.send_email(recipient, subject, email_content, is_html=True)
    
    def send_weekly_reminder(self, recipients, data):
        """Send weekly reminder email"""
        template_path = os.path.join(Config.TEMPLATES_DIR, 'weekly_reminder.html')
        
        if not os.path.exists(template_path):
            self.logger.error(f"Template not found: {template_path}")
            return False
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        quarter = data.get('quarter', '3')
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        quarter_description = self.get_quarter_description(quarter)
        week_start = data.get('week_start', datetime.now().strftime('%Y-%m-%d'))
        week_end = data.get('week_end', datetime.now().strftime('%Y-%m-%d'))
        
        for recipient, recipient_data in recipients.items():
            servers = recipient_data.get('servers', [])
            
            email_content = template.format(
                owner_email=recipient,
                week_start=week_start,
                week_end=week_end,
                quarter=quarter_name,
                server_table=self.generate_reminder_table(servers, quarter),
                quarter_description=quarter_description
            )
            
            subject = f"Weekly Patching Reminder - {quarter_name} - Week of {week_start}"
            self.email_sender.send_email(recipient, subject, email_content, is_html=True)
    
    def send_daily_reminder(self, recipients, data):
        """Send 24-hour reminder email"""
        template_path = os.path.join(Config.TEMPLATES_DIR, 'daily_reminder.html')
        
        if not os.path.exists(template_path):
            self.logger.error(f"Template not found: {template_path}")
            return False
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        quarter = data.get('quarter', '3')
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        quarter_description = self.get_quarter_description(quarter)
        patch_date = data.get('patch_date', datetime.now().strftime('%Y-%m-%d'))
        
        for recipient, recipient_data in recipients.items():
            servers = recipient_data.get('servers', [])
            
            email_content = template.format(
                owner_email=recipient,
                patch_date=patch_date,
                quarter=quarter_name,
                server_table=self.generate_reminder_table(servers, quarter),
                quarter_description=quarter_description
            )
            
            subject = f"24-Hour Patching Reminder - {quarter_name} - {patch_date}"
            self.email_sender.send_email(recipient, subject, email_content, is_html=True)
    
    def send_completion_notice(self, recipients, data):
        """Send completion notice email"""
        template_path = os.path.join(Config.TEMPLATES_DIR, 'completion_notice.html')
        
        if not os.path.exists(template_path):
            self.logger.error(f"Template not found: {template_path}")
            return False
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        server_name = data.get('server_name', 'Unknown')
        status = data.get('status', 'COMPLETED')
        validation_summary = data.get('validation_summary', '')
        location = data.get('location', 'Unknown')
        completion_time = data.get('completion_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Determine current quarter
        current_quarter = Config.get_current_quarter()
        quarter_name = Config.QUARTERS.get(current_quarter, {}).get('name', f'Q{current_quarter}')
        
        # Determine status and banner classes
        if status.upper() == 'SUCCESSFUL':
            banner_class = 'banner-success'
            status_class = 'success'
        else:
            banner_class = 'banner-warning'
            status_class = 'warning'
        
        email_content = template.format(
            server_name=server_name,
            status=status,
            completion_time=completion_time,
            validation_summary=validation_summary,
            location=location,
            banner_class=banner_class,
            status_class=status_class
        )
        
        subject = f"{quarter_name} Patching {status}: {server_name}"
        
        for recipient in recipients:
            self.email_sender.send_email(recipient, subject, email_content, is_html=True)
    
    def send_failure_notice(self, recipients, data):
        """Send failure notification email"""
        server_name = data.get('server_name', 'Unknown')
        error_message = data.get('error', 'Unknown error')
        
        # Determine current quarter
        current_quarter = Config.get_current_quarter()
        quarter_name = Config.QUARTERS.get(current_quarter, {}).get('name', f'Q{current_quarter}')
        
        subject = f"{quarter_name} Patching FAILED: {server_name}"
        
        message_body = f"""
        Patching process failed for server: {server_name}
        
        Error: {error_message}
        Failure Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Please investigate immediately and take appropriate action.
        
        Server may require manual intervention to restore to operational status.
        """
        
        for recipient in recipients:
            self.email_sender.send_email(recipient, subject, message_body)
    
    def send_precheck_alert(self, recipients, data):
        """Send alert email for pre-check failures"""
        server_name = data.get('server_name', 'Unknown')
        results = data.get('results', {})
        
        subject = f"Pre-check Alert: {server_name}"
        
        message_body = f"""
        Pre-check alert for server: {server_name}
        
        Results:
        - Connectivity: {'PASS' if results.get('connectivity', False) else 'FAIL'}
        - Disk Check: {'PASS' if results.get('disk_check', False) else 'FAIL'}
        - Dell Hardware Check: {'PASS' if results.get('dell_check', False) else 'FAIL'}
        
        Errors: {', '.join(results.get('errors', [])) if results.get('errors', []) else 'None'}
        
        Please investigate before proceeding with patching.
        """
        
        for recipient in recipients:
            self.email_sender.send_email(recipient, subject, message_body)
    
    def generate_server_table(self, servers_list, quarter):
        """Generate HTML table for servers"""
        table_rows = ""
        for server in servers_list:
            # Get patch date and time for the specified quarter
            patch_date = server.get(f'Q{quarter} Patch Date', 'Not Set')
            patch_time = server.get(f'Q{quarter} Patch Time', 'Not Set')
            
            table_rows += f"""
            <tr>
                <td>{server['Server Name']}</td>
                <td>{server['Server Timezone']}</td>
                <td>{patch_date}</td>
                <td>{patch_time}</td>
                <td>{server.get('location', '')}</td>
            </tr>
            """
        
        return f"""
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Server Name</th>
                <th>Timezone</th>
                <th>Current Patch Date</th>
                <th>Current Patch Time</th>
                <th>Location</th>
            </tr>
            {table_rows}
        </table>
        """
    
    def generate_reminder_table(self, servers_list, quarter):
        """Generate HTML table for reminder emails"""
        table_rows = ""
        for server in servers_list:
            # Get patch date and time for the specified quarter
            patch_date = server.get(f'Q{quarter} Patch Date', 'Not Set')
            patch_time = server.get(f'Q{quarter} Patch Time', 'Not Set')
            
            table_rows += f"""
            <tr>
                <td>{server['Server Name']}</td>
                <td>{patch_date}</td>
                <td>{patch_time}</td>
                <td>{server['Server Timezone']}</td>
                <td>{server.get('incident_ticket', 'Not Set')}</td>
                <td>{server.get('patcher_email', 'Not Set')}</td>
                <td>{server.get('location', '')}</td>
            </tr>
            """
        
        return f"""
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Server Name</th>
                <th>Patch Date</th>
                <th>Patch Time</th>
                <th>Timezone</th>
                <th>Incident Ticket</th>
                <th>Patcher Email</th>
                <th>Location</th>
            </tr>
            {table_rows}
        </table>
        """
