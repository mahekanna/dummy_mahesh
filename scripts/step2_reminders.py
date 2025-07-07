# scripts/step2_reminders.py
from datetime import datetime, timedelta
from utils.email_sender import EmailSender
from utils.csv_handler import CSVHandler
from config.settings import Config

class ReminderHandler:
    def __init__(self):
        self.email_sender = EmailSender()
        self.csv_handler = CSVHandler()
    
    def send_weekly_reminder(self, quarter):
        """Send weekly reminder with upcoming week's servers"""
        today = datetime.now().date()
        week_start = today + timedelta(days=(7 - today.weekday()))
        week_end = week_start + timedelta(days=6)
        
        servers = self.csv_handler.read_servers()
        upcoming_servers = []
        
        for server in servers:
            patch_date_str = server.get(f'Q{quarter} Patch Date')
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            
            # Only include approved servers in reminders
            if patch_date_str and approval_status == 'Approved':
                try:
                    patch_date = datetime.strptime(patch_date_str, '%Y-%m-%d').date()
                    if week_start <= patch_date <= week_end:
                        upcoming_servers.append(server)
                except ValueError:
                    continue
        
        if upcoming_servers:
            self.send_weekly_email(upcoming_servers, week_start, week_end, quarter)
    
    def send_daily_reminder(self, quarter):
        """Send 24-hour reminder for tomorrow's servers"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        servers = self.csv_handler.read_servers()
        tomorrow_servers = []
        
        for server in servers:
            patch_date_str = server.get(f'Q{quarter} Patch Date')
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            
            # Only include approved servers in reminders
            if patch_date_str and approval_status == 'Approved':
                try:
                    patch_date = datetime.strptime(patch_date_str, '%Y-%m-%d').date()
                    if patch_date == tomorrow:
                        tomorrow_servers.append(server)
                except ValueError:
                    continue
        
        if tomorrow_servers:
            self.send_daily_email(tomorrow_servers, tomorrow, quarter)
    
    def send_weekly_email(self, servers_list, week_start, week_end, quarter):
        """Send weekly reminder email"""
        with open(f'{Config.TEMPLATES_DIR}/weekly_reminder.html', 'r') as f:
            template = f.read()
        
        server_table = self.generate_reminder_table(servers_list, quarter)
        
        # Group by owner and send
        owner_servers = self.group_servers_by_owner(servers_list)
        
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        
        # Get quarter description
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        quarter_description = quarter_descriptions.get(quarter, 'Unknown')
        
        for owner_email, owner_servers_list in owner_servers.items():
            email_content = template.format(
                owner_email=owner_email,
                week_start=week_start.strftime('%Y-%m-%d'),
                week_end=week_end.strftime('%Y-%m-%d'),
                quarter=quarter_name,
                server_table=self.generate_reminder_table(owner_servers_list, quarter),
                quarter_description=quarter_description
            )
            
            subject = f"Weekly Patching Reminder - {quarter_name} - Week of {week_start.strftime('%Y-%m-%d')}"
            self.email_sender.send_email(owner_email, subject, email_content, is_html=True)
    
    def send_daily_email(self, servers_list, patch_date, quarter):
        """Send 24-hour reminder email"""
        with open(f'{Config.TEMPLATES_DIR}/daily_reminder.html', 'r') as f:
            template = f.read()
        
        # Group by owner and send
        owner_servers = self.group_servers_by_owner(servers_list)
        
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        
        # Get quarter description
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        quarter_description = quarter_descriptions.get(quarter, 'Unknown')
        
        for owner_email, owner_servers_list in owner_servers.items():
            email_content = template.format(
                owner_email=owner_email,
                patch_date=patch_date.strftime('%Y-%m-%d'),
                quarter=quarter_name,
                server_table=self.generate_reminder_table(owner_servers_list, quarter),
                quarter_description=quarter_description
            )
            
            subject = f"24-Hour Patching Reminder - {quarter_name} - {patch_date.strftime('%Y-%m-%d')}"
            self.email_sender.send_email(owner_email, subject, email_content, is_html=True)
    
    def group_servers_by_owner(self, servers_list):
        """Group servers by owner email"""
        owner_servers = {}
        for server in servers_list:
            primary = server.get('primary_owner', '')
            secondary = server.get('secondary_owner', '')
            
            if primary:
                if primary not in owner_servers:
                    owner_servers[primary] = []
                owner_servers[primary].append(server)
            
            if secondary and secondary != primary:
                if secondary not in owner_servers:
                    owner_servers[secondary] = []
                owner_servers[secondary].append(server)
        
        return owner_servers
    
    def generate_reminder_table(self, servers_list, quarter):
        """Generate HTML table for reminder emails"""
        table_rows = ""
        for server in servers_list:
            # Get patch date and time for the specified quarter
            patch_date = server.get(f'Q{quarter} Patch Date', 'Not Set')
            patch_time = server.get(f'Q{quarter} Patch Time', 'Not Set')
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            
            table_rows += f"""
            <tr>
                <td>{server['Server Name']}</td>
                <td>{patch_date}</td>
                <td>{patch_time}</td>
                <td>{server['Server Timezone']}</td>
                <td><span style="color: #28a745; font-weight: bold;">{approval_status}</span></td>
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
                <th>Approval Status</th>
                <th>Incident Ticket</th>
                <th>Patcher Email</th>
                <th>Location</th>
            </tr>
            {table_rows}
        </table>
        """
