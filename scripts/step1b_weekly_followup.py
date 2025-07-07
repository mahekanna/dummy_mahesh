# scripts/step1b_weekly_followup.py
from datetime import datetime, timedelta
from utils.csv_handler import CSVHandler
from utils.email_sender import EmailSender
from utils.logger import Logger
from config.settings import Config

class WeeklyFollowupHandler:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.email_sender = EmailSender()
        self.logger = Logger('weekly_followup')
    
    def send_weekly_followup(self, quarter):
        """Send weekly followup to servers without schedule response"""
        servers = self.csv_handler.read_servers()
        
        # Find servers that need followup (no schedule set or no approval response)
        followup_needed = []
        for server in servers:
            patch_date = server.get(f'Q{quarter} Patch Date')
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            
            # Include servers with no patch date set or those with dates but no approval
            if not patch_date or approval_status == 'Pending':
                followup_needed.append(server)
        
        if not followup_needed:
            self.logger.info("No servers require weekly followup")
            return
        
        # Group servers by owner
        owner_servers = self.group_servers_by_owner(followup_needed)
        
        # Send followup emails to each owner
        for owner_email, servers_list in owner_servers.items():
            self.send_owner_followup(owner_email, servers_list, quarter)
        
        self.logger.info(f"Weekly followup sent to {len(owner_servers)} owners for {len(followup_needed)} servers")
    
    def send_owner_followup(self, owner_email, servers_list, quarter):
        """Send followup to individual owner"""
        with open(f'{Config.TEMPLATES_DIR}/weekly_followup.html', 'r') as f:
            template = f.read()
        
        server_table = self.generate_followup_table(servers_list, quarter)
        
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        
        # Get quarter description
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        quarter_description = quarter_descriptions.get(quarter, 'Unknown')
        
        # Calculate deadline (48 hours from now)
        deadline_date = (datetime.now() + timedelta(hours=48)).strftime('%Y-%m-%d %H:%M')
        original_notice_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Get default time assignment
        default_time = self.get_default_time_assignment(servers_list)
        
        email_content = template.format(
            owner_email=owner_email,
            quarter=quarter_name,
            server_table=server_table,
            deadline_date=deadline_date,
            default_time=default_time,
            quarter_description=quarter_description,
            original_notice_date=original_notice_date
        )
        
        subject = f"FINAL NOTICE: {quarter_name} Patching Schedule - Auto-Approval in 48 Hours"
        self.email_sender.send_email(owner_email, subject, email_content, is_html=True)
    
    def generate_followup_table(self, servers_list, quarter):
        """Generate HTML table for followup email"""
        table_rows = ""
        for server in servers_list:
            # Get current patch date and time for the specified quarter
            patch_date = server.get(f'Q{quarter} Patch Date', 'Not Set')
            patch_time = server.get(f'Q{quarter} Patch Time', 'Not Set')
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            
            # Determine status color and message
            if not server.get(f'Q{quarter} Patch Date'):
                status_display = '<span style="color: #dc3545; font-weight: bold;">No Schedule Set</span>'
            elif approval_status == 'Pending':
                status_display = '<span style="color: #ffc107; font-weight: bold;">Awaiting Approval</span>'
            else:
                status_display = f'<span style="color: #28a745; font-weight: bold;">{approval_status}</span>'
            
            table_rows += f"""
            <tr>
                <td>{server['Server Name']}</td>
                <td>{patch_date}</td>
                <td>{patch_time}</td>
                <td>{server['Server Timezone']}</td>
                <td>{status_display}</td>
                <td><span style="color: #0056b3; font-weight: bold;">{server.get('primary_owner', 'Not Set')}</span></td>
                <td>{server.get('secondary_owner', 'Not Set') if server.get('secondary_owner') else '<em>Not Set</em>'}</td>
                <td>{server.get('location', '')}</td>
            </tr>
            """
        
        return f"""
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Server Name</th>
                <th>Current Patch Date</th>
                <th>Current Patch Time</th>
                <th>Timezone</th>
                <th>Status</th>
                <th>Primary Owner</th>
                <th>Secondary Owner</th>
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
    
    def get_default_time_assignment(self, servers_list):
        """Calculate intelligent default time assignment based on server count"""
        # Base evening time for patching
        base_hour = 20  # 8 PM
        
        # Stagger time based on server count to avoid overload
        server_count = len(servers_list)
        
        if server_count <= 3:
            return f"{base_hour:02d}:00"
        elif server_count <= 6:
            return f"{base_hour:02d}:30"
        elif server_count <= 10:
            return f"{base_hour + 1:02d}:00"
        else:
            return f"{base_hour + 1:02d}:30"
    
    def auto_approve_pending_servers(self, quarter):
        """Auto-approve servers that haven't responded after deadline"""
        servers = self.csv_handler.read_servers()
        auto_approved_count = 0
        
        for server in servers:
            patch_date = server.get(f'Q{quarter} Patch Date')
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            
            # Auto-approve servers with no schedule or pending approval
            if not patch_date or approval_status == 'Pending':
                # Assign default date/time if not set
                if not patch_date:
                    default_date = self.get_next_available_thursday()
                    default_time = self.get_default_time_assignment([server])
                    server[f'Q{quarter} Patch Date'] = default_date
                    server[f'Q{quarter} Patch Time'] = default_time
                
                # Set auto-approval status
                server[f'Q{quarter} Approval Status'] = 'Auto-Approved'
                
                # Update patching status if current quarter
                if quarter == Config.get_current_quarter():
                    server['Current Quarter Patching Status'] = 'Auto-Approved'
                
                auto_approved_count += 1
                self.logger.info(f"Auto-approved: {server['Server Name']} - {server[f'Q{quarter} Patch Date']} {server[f'Q{quarter} Patch Time']}")
        
        if auto_approved_count > 0:
            self.csv_handler.write_servers(servers)
            self.logger.info(f"Auto-approved {auto_approved_count} servers for Q{quarter}")
            
            # Send confirmation emails
            self.send_auto_approval_confirmations(servers, quarter)
        
        return auto_approved_count
    
    def get_next_available_thursday(self):
        """Get the next available Thursday for assignment"""
        today = datetime.now().date()
        days_until_thursday = (3 - today.weekday()) % 7  # 3 = Thursday
        
        if days_until_thursday == 0:  # If today is Thursday
            days_until_thursday = 7  # Next Thursday
        
        next_thursday = today + timedelta(days=days_until_thursday)
        return next_thursday.strftime('%Y-%m-%d')
    
    def send_auto_approval_confirmations(self, servers, quarter):
        """Send confirmation emails for auto-approved servers"""
        auto_approved_servers = [
            s for s in servers 
            if s.get(f'Q{quarter} Approval Status') == 'Auto-Approved'
        ]
        
        if not auto_approved_servers:
            return
        
        # Group by owner and send confirmations
        owner_servers = self.group_servers_by_owner(auto_approved_servers)
        
        for owner_email, servers_list in owner_servers.items():
            self.send_auto_approval_confirmation(owner_email, servers_list, quarter)
    
    def send_auto_approval_confirmation(self, owner_email, servers_list, quarter):
        """Send auto-approval confirmation to owner"""
        # Reuse the existing approval confirmation template with modifications
        from web_portal.app import generate_approval_confirmation_table
        
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        server_table = generate_approval_confirmation_table(servers_list, quarter)
        
        subject = f"AUTO-APPROVED: {quarter_name} Patching Schedule - Default Settings Applied"
        
        # Simple notification about auto-approval
        email_content = f"""
        <h2>Auto-Approval Notification - {quarter_name}</h2>
        <p>Dear {owner_email},</p>
        <p>Your patching schedule has been <strong>automatically approved</strong> with default settings due to no response within the deadline.</p>
        {server_table}
        <p>The patching will proceed as scheduled. For any concerns, please contact the Infrastructure Team immediately.</p>
        <p>Best regards,<br>Infrastructure Patching Team</p>
        """
        
        self.email_sender.send_email(owner_email, subject, email_content, is_html=True)
        self.logger.info(f"Auto-approval confirmation sent to: {owner_email}")