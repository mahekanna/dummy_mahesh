# scripts/step1_monthly_notice.py
import csv
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from calendar import monthrange
from utils.email_sender import EmailSender
from utils.csv_handler import CSVHandler
from config.settings import Config

class MonthlyNoticeHandler:
    def __init__(self):
        self.email_sender = EmailSender()
        self.csv_handler = CSVHandler()
        
    def generate_proposed_dates(self, year, month, quarter):
        """Generate proposed Thursday dates for the month"""
        proposed_dates = []
        _, last_day = monthrange(year, month)
        
        for day in range(1, last_day + 1):
            date = datetime(year, month, day)
            if date.weekday() == 3:  # Thursday is 3
                proposed_dates.append(date.strftime('%Y-%m-%d'))
        
        return proposed_dates
    
    def get_quarter_months(self, quarter):
        """Get the months for a specific quarter based on custom definition"""
        return Config.QUARTERS.get(quarter, {}).get('months', [])
    
    def send_monthly_notice(self, quarter):
        """Send monthly notice to all server owners"""
        servers = self.csv_handler.read_servers()
        
        # Group servers by owner
        owner_servers = {}
        for server in servers:
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
        
        # Generate proposed dates for all months in the quarter
        now = datetime.now()
        proposed_dates = []
        
        # Get months for the quarter
        quarter_months = self.get_quarter_months(quarter)
        
        # Adjust year based on quarter
        year = now.year
        if quarter == "1" and now.month > 10:  # For Q1 (Nov-Jan), if current month is Nov or Dec, use current year, otherwise next year
            year = now.year
        elif quarter == "1" and now.month < 11:  # For Q1 if current month is before Nov, use next year
            year = now.year + 1
        
        # Generate dates for each month in the quarter
        for month in quarter_months:
            month_year = year if month >= now.month or quarter == "1" else year + 1
            month_dates = self.generate_proposed_dates(month_year, month, quarter)
            proposed_dates.extend(month_dates)
        
        # Send emails to each owner
        for owner_email, servers_list in owner_servers.items():
            self.send_owner_notice(owner_email, servers_list, proposed_dates, quarter)
    
    def send_owner_notice(self, owner_email, servers_list, proposed_dates, quarter):
        """Send notice to individual owner"""
        with open(f'{Config.TEMPLATES_DIR}/monthly_notice.html', 'r') as f:
            template = f.read()
        
        server_table = self.generate_server_table(servers_list, quarter)
        proposed_dates_list = '<br>'.join([f"• {date}" for date in proposed_dates])
        
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        
        # Get quarter description
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        quarter_description = quarter_descriptions.get(quarter, 'Unknown')
        
        email_content = template.format(
            owner_email=owner_email,
            quarter=quarter_name,
            proposed_dates=proposed_dates_list,
            server_table=server_table,
            deadline_date=(datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
            quarter_description=quarter_description
        )
        
        subject = f"Monthly Patching Notice - {quarter_name} Schedule Selection Required"
        self.email_sender.send_email(owner_email, subject, email_content, is_html=True)
    
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
                <td><span style="color: #0056b3; font-weight: bold;">{server.get('primary_owner', 'Not Set')}</span></td>
                <td>{server.get('secondary_owner', 'Not Set') if server.get('secondary_owner') else '<em>Not Set</em>'}</td>
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
                <th>Primary Owner</th>
                <th>Secondary Owner</th>
                <th>Location</th>
            </tr>
            {table_rows}
        </table>
        """
