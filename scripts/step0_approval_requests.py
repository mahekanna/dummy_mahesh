# scripts/step0_approval_requests.py
from datetime import datetime, timedelta
from utils.csv_handler import CSVHandler
from utils.email_sender import EmailSender
from utils.logger import Logger
from config.settings import Config

class ApprovalRequestHandler:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.email_sender = EmailSender()
        self.logger = Logger('approval_requests')
    
    def send_approval_requests(self, quarter):
        """Send approval request emails to owners with pending approvals"""
        servers = self.csv_handler.read_servers()
        
        # Find servers with pending approvals for the quarter
        pending_servers = []
        for server in servers:
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            patch_date = server.get(f'Q{quarter} Patch Date')
            
            # Only include servers that have patch dates but pending approvals
            if approval_status == 'Pending' and patch_date:
                pending_servers.append(server)
        
        if not pending_servers:
            self.logger.info("No servers with pending approvals found")
            return
        
        # Group servers by owner
        owner_servers = self.group_servers_by_owner(pending_servers)
        
        # Send approval requests to each owner
        for owner_email, servers_list in owner_servers.items():
            self.send_owner_approval_request(owner_email, servers_list, quarter)
        
        self.logger.info(f"Approval requests sent to {len(owner_servers)} owners for {len(pending_servers)} servers")
    
    def send_owner_approval_request(self, owner_email, servers_list, quarter):
        """Send approval request to individual owner"""
        with open(f'{Config.TEMPLATES_DIR}/approval_request.html', 'r') as f:
            template = f.read()
        
        server_table = self.generate_approval_table(servers_list, quarter)
        
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        
        # Get quarter description
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        quarter_description = quarter_descriptions.get(quarter, 'Unknown')
        
        # Calculate deadline (next Tuesday)
        today = datetime.now()
        days_until_tuesday = (1 - today.weekday()) % 7  # 1 = Tuesday
        if days_until_tuesday == 0 and today.weekday() >= 1:  # If today is Tuesday or later
            days_until_tuesday = 7  # Next Tuesday
        deadline_date = today + timedelta(days=days_until_tuesday)
        
        email_content = template.format(
            owner_email=owner_email,
            quarter=quarter_name,
            server_table=server_table,
            deadline_date=deadline_date.strftime('%Y-%m-%d'),
            quarter_description=quarter_description
        )
        
        subject = f"URGENT: Approval Required - {quarter_name} Patching Schedule (Due Tuesday EOD)"
        self.email_sender.send_email(owner_email, subject, email_content, is_html=True)
    
    def generate_approval_table(self, servers_list, quarter):
        """Generate HTML table for approval request"""
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
                <td><span style="color: #dc3545; font-weight: bold;">{approval_status}</span></td>
                <td><span style="color: #0056b3; font-weight: bold;">{server.get('primary_owner', 'Not Set')}</span></td>
                <td>{server.get('secondary_owner', 'Not Set') if server.get('secondary_owner') else '<em>Not Set</em>'}</td>
                <td>{server.get('incident_ticket', 'Not Set')}</td>
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
                <th>Primary Owner</th>
                <th>Secondary Owner</th>
                <th>Incident Ticket</th>
                <th>Location</th>
            </tr>
            {table_rows}
        </table>
        """
    
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
    
    def check_approval_deadline(self, quarter):
        """Check if we're approaching the approval deadline"""
        today = datetime.now()
        current_weekday = today.weekday()  # 0=Monday, 6=Sunday
        
        # Send approval requests on Monday (before Tuesday deadline)
        if current_weekday == 0:  # Monday
            return True
        
        return False
    
    def get_unapproved_servers(self, quarter):
        """Get list of servers that don't have approval yet"""
        servers = self.csv_handler.read_servers()
        unapproved = []
        
        for server in servers:
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            patch_date = server.get(f'Q{quarter} Patch Date')
            
            # Include servers with patch dates but no approval
            if approval_status == 'Pending' and patch_date:
                unapproved.append(server)
        
        return unapproved