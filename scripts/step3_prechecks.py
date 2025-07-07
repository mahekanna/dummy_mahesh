# scripts/step3_prechecks.py
import subprocess
import re
import json
from datetime import datetime, timedelta
from utils.csv_handler import CSVHandler
from utils.email_sender import EmailSender
from utils.timezone_handler import TimezoneHandler
from utils.logger import Logger
from config.settings import Config

class PreCheckHandler:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.email_sender = EmailSender()
        self.timezone_handler = TimezoneHandler()
        self.logger = Logger('precheck')
    
    def run_prechecks(self, quarter):
        """Run pre-checks for servers scheduled in the next 5 hours"""
        target_time = datetime.now() + timedelta(hours=Config.PRECHECK_HOURS_BEFORE)
        servers = self.csv_handler.read_servers()
        
        for server in servers:
            # Only run prechecks for approved servers
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            if approval_status == 'Approved' and self.is_server_due_for_precheck(server, target_time, quarter):
                self.logger.info(f"Running pre-checks for {server['Server Name']} (Approved)")
                self.run_server_precheck(server)
            elif approval_status != 'Approved' and self.is_server_due_for_precheck(server, target_time, quarter):
                self.logger.warning(f"Skipping pre-checks for {server['Server Name']} - not approved (Status: {approval_status})")
    
    def is_server_due_for_precheck(self, server, target_time, quarter):
        """Check if server is due for pre-check"""
        patch_date_str = server.get(f'Q{quarter} Patch Date')
        patch_time_str = server.get(f'Q{quarter} Patch Time')
        server_timezone = server.get('Server Timezone', 'UTC')
        
        if not patch_date_str or not patch_time_str:
            return False
        
        try:
            # Convert scheduled time to UTC for comparison
            local_dt_str = f"{patch_date_str} {patch_time_str}"
            local_dt = datetime.strptime(local_dt_str, '%Y-%m-%d %H:%M')
            
            # Convert server's local time to UTC
            scheduled_dt_utc = self.timezone_handler.convert_timezone(
                local_dt, server_timezone, 'UTC'
            )
            
            # Check if target time is within 1 hour of the precheck window
            time_diff = abs((scheduled_dt_utc - target_time).total_seconds())
            return time_diff <= 3600  # Within 1 hour
            
        except Exception as e:
            self.logger.error(f"Error parsing datetime for {server['Server Name']}: {e}")
            return False
    
    def run_server_precheck(self, server):
        """Run comprehensive pre-checks for a server"""
        server_name = server['Server Name']
        results = {
            'server_name': server_name,
            'disk_check': False,
            'dell_check': False,
            'connectivity': False,
            'errors': []
        }
        
        # Check connectivity
        if self.check_server_connectivity(server_name):
            results['connectivity'] = True
            
            # Run disk space checks
            results['disk_check'] = self.run_disk_checks(server_name)
            
            # Run Dell hardware checks if applicable
            results['dell_check'] = self.run_dell_checks(server_name)
        else:
            results['errors'].append("Server connectivity failed")
        
        # Log results and send alerts if needed
        self.process_precheck_results(server, results)
    
    def check_server_connectivity(self, server_name):
        """Check SSH connectivity to server"""
        try:
            result = subprocess.run(
                ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', 
                 server_name, 'echo "connectivity_check"'],
                capture_output=True, text=True, timeout=15
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Connectivity check failed for {server_name}: {e}")
            return False
    
    def run_disk_checks(self, server_name):
        """Run disk space checks using bash script"""
        try:
            import os
            script_path = os.path.join(os.path.dirname(__file__), '..', 'bash_scripts', 'disk_check.sh')
            result = subprocess.run(
                ['bash', script_path, server_name],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Disk check failed for {server_name}: {e}")
            return False
    
    def run_dell_checks(self, server_name):
        """Run Dell iDRAC checks using bash script"""
        try:
            import os
            script_path = os.path.join(os.path.dirname(__file__), '..', 'bash_scripts', 'dell_idrac_check.sh')
            result = subprocess.run(
                ['bash', script_path, server_name],
                capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Dell check failed for {server_name}: {e}")
            return False
    
    def process_precheck_results(self, server, results):
        """Process and act on pre-check results"""
        if all([results['connectivity'], results['disk_check'], results['dell_check']]):
            self.logger.info(f"All pre-checks passed for {server['Server Name']}")
        else:
            self.logger.warning(f"Pre-check failures for {server['Server Name']}: {json.dumps(results)}")
            self.send_precheck_alert(server, results)
    
    def send_precheck_alert(self, server, results):
        """Send alert email for pre-check failures"""
        subject = f"Pre-check Alert: {server['Server Name']}"
        
        message_body = f"""
        Pre-check alert for server: {server['Server Name']}
        
        Results:
        - Connectivity: {'PASS' if results['connectivity'] else 'FAIL'}
        - Disk Check: {'PASS' if results['disk_check'] else 'FAIL'}
        - Dell Hardware Check: {'PASS' if results['dell_check'] else 'FAIL'}
        
        Errors: {', '.join(results['errors']) if results['errors'] else 'None'}
        
        Please investigate before proceeding with patching.
        """
        
        # Send to primary and secondary owners
        recipients = []
        if server.get('primary_owner'):
            recipients.append(server['primary_owner'])
        if server.get('secondary_owner'):
            recipients.append(server['secondary_owner'])
        
        for recipient in recipients:
            if recipient:
                self.email_sender.send_email(recipient, subject, message_body)
