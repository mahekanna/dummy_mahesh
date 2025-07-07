# scripts/step6_post_patch.py
import subprocess
import time
import os
import json
from datetime import datetime
from utils.csv_handler import CSVHandler
from utils.email_sender import EmailSender
from utils.logger import Logger
from config.settings import Config
from database.models import DatabaseManager

class PostPatchValidator:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.email_sender = EmailSender()
        self.logger = Logger('post_patch')
        self.db_manager = None
    
    def connect_db(self):
        """Connect to database"""
        if not self.db_manager:
            self.db_manager = DatabaseManager()
            self.db_manager.connect()
    
    def post_patch_validation(self, server_name):
        """Run post-patch validation and send completion emails"""
        self.logger.info(f"Starting post-patch validation for {server_name}")
        
        # Wait for system to stabilize
        self.logger.info(f"Waiting {Config.POST_PATCH_WAIT_MINUTES} minutes for system stabilization...")
        time.sleep(Config.POST_PATCH_WAIT_MINUTES * 60)
        
        validation_results = {
            'server_name': server_name,
            'ssh_connectivity': False,
            'system_services': False,
            'disk_space': False,
            'system_load': False,
            'patch_completion_time': datetime.now().isoformat()
        }
        
        try:
            # Check SSH connectivity
            validation_results['ssh_connectivity'] = self.check_ssh_connectivity(server_name)
            
            if validation_results['ssh_connectivity']:
                # Check system services
                validation_results['system_services'] = self.check_system_services(server_name)
                
                # Check disk space
                validation_results['disk_space'] = self.check_disk_space_post_patch(server_name)
                
                # Check system load
                validation_results['system_load'] = self.check_system_load(server_name)
            
            # Determine overall success
            overall_success = all(validation_results.values())
            
            # Update database with completion status
            self.connect_db()
            if self.db_manager:
                current_quarter = int(Config.get_current_quarter())
                status = 'completed' if overall_success else 'failed'
                
                # Get the most recent patch history record for this server
                # and update it with completion info
                
                # For real implementation, we would query the patch_history table
                # and update the latest entry
                
                # Update server status in the servers table
                servers = self.csv_handler.read_servers()
                for server in servers:
                    if server['Server Name'] == server_name:
                        # Update CSV with new status
                        server['Current Quarter Patching Status'] = status
                        
                # Write updated servers to CSV
                self.csv_handler.write_servers(servers)
            
            # Send completion email
            self.send_completion_email(server_name, validation_results, overall_success)
            
            return overall_success
            
        except Exception as e:
            self.logger.error(f"Post-patch validation failed for {server_name}: {e}")
            self.send_failure_email(server_name, str(e))
            return False
    
    def check_ssh_connectivity(self, server_name):
        """Check SSH connectivity after reboot"""
        max_attempts = 10
        wait_time = 30
        
        for attempt in range(max_attempts):
            try:
                result = subprocess.run(
                    ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes',
                     server_name, 'echo "post_patch_check"'],
                    capture_output=True, text=True, timeout=15
                )
                
                if result.returncode == 0:
                    self.logger.info(f"SSH connectivity restored for {server_name}")
                    return True
                    
            except Exception as e:
                self.logger.debug(f"SSH attempt {attempt + 1} error: {e}")
            
            self.logger.info(f"SSH attempt {attempt + 1}/{max_attempts} failed for {server_name}, waiting {wait_time}s...")
            time.sleep(wait_time)
        
        self.logger.error(f"SSH connectivity not restored for {server_name} after {max_attempts} attempts")
        return False
    
    def check_system_services(self, server_name):
        """Check critical system services"""
        try:
            # Check if systemd is running
            result = subprocess.run(
                ['ssh', server_name, 'systemctl', 'is-system-running'],
                capture_output=True, text=True, timeout=30
            )
            
            system_status = result.stdout.strip()
            
            # Check critical services
            critical_services = ['sshd', 'network', 'NetworkManager']
            all_services_ok = True
            
            for service in critical_services:
                result = subprocess.run(
                    ['ssh', server_name, 'systemctl', 'is-active', service],
                    capture_output=True, text=True, timeout=15
                )
                
                if result.stdout.strip() != 'active':
                    self.logger.warning(f"Service {service} not active on {server_name}")
                    all_services_ok = False
            
            return system_status in ['running', 'degraded'] and all_services_ok
            
        except Exception as e:
            self.logger.error(f"Failed to check system services on {server_name}: {e}")
            return False
    
    def check_disk_space_post_patch(self, server_name):
        """Check disk space after patching"""
        try:
            script_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run(
                ['bash', f'{script_path}/bash_scripts/server_validation.sh', server_name],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to check disk space on {server_name}: {e}")
            return False
    
    def check_system_load(self, server_name):
        """Check system load and performance"""
        try:
            # Check load average
            result = subprocess.run(
                ['ssh', server_name, 'cat', '/proc/loadavg'],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                load_avg = result.stdout.strip().split()[0]
                
                # Check if load is reasonable (less than number of CPUs)
                cpu_result = subprocess.run(
                    ['ssh', server_name, 'nproc'],
                    capture_output=True, text=True, timeout=15
                )
                
                if cpu_result.returncode == 0:
                    cpu_count = int(cpu_result.stdout.strip())
                    current_load = float(load_avg)
                    
                    return current_load < (cpu_count * 2)  # Allow 2x CPU count as reasonable
            
            return True  # Default to OK if we can't determine
            
        except Exception as e:
            self.logger.warning(f"Could not check system load for {server_name}: {e}")
            return True  # Default to OK
    
    def send_completion_email(self, server_name, validation_results, success):
        """Send completion email to server owners"""
        # Get server details
        servers = self.csv_handler.read_servers()
        server_info = None
        
        for server in servers:
            if server['Server Name'] == server_name:
                server_info = server
                break
        
        if not server_info:
            self.logger.error(f"Server info not found for {server_name}")
            return
        
        # Load email template
        template_file = 'completion_notice.html'
        try:
            with open(f'{Config.TEMPLATES_DIR}/{template_file}', 'r') as f:
                template = f.read()
        except FileNotFoundError:
            template = self.get_default_completion_template()
        
        # Generate validation summary
        validation_summary = self.generate_validation_summary(validation_results)
        
        # Prepare email content
        status = "SUCCESSFUL" if success else "COMPLETED WITH ISSUES"
        email_content = template.format(
            server_name=server_name,
            status=status,
            completion_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            validation_summary=validation_summary,
            location=server_info.get('location', 'Unknown')
        )
        
        # Determine current quarter
        current_quarter = Config.get_current_quarter()
        quarter_name = Config.QUARTERS.get(current_quarter, {}).get('name', f'Q{current_quarter}')
        
        subject = f"{quarter_name} Patching {status}: {server_name}"
        
        # Send to owners
        recipients = []
        if server_info.get('primary_owner'):
            recipients.append(server_info['primary_owner'])
        if server_info.get('secondary_owner'):
            recipients.append(server_info['secondary_owner'])
        
        for recipient in recipients:
            if recipient:
                self.email_sender.send_email(recipient, subject, email_content, is_html=True)
        
        self.logger.info(f"Completion email sent for {server_name} to {recipients}")
    
    def send_failure_email(self, server_name, error_message):
        """Send failure notification email"""
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
        
        # Get server owners
        servers = self.csv_handler.read_servers()
        recipients = ["admin@company.com"]  # Always include admin
        
        for server in servers:
            if server['Server Name'] == server_name:
                if server.get('primary_owner'):
                    recipients.append(server['primary_owner'])
                if server.get('secondary_owner'):
                    recipients.append(server['secondary_owner'])
                break
        
        for recipient in recipients:
            if recipient:
                self.email_sender.send_email(recipient, subject, message_body)
    
    def generate_validation_summary(self, validation_results):
        """Generate HTML summary of validation results"""
        summary_rows = ""
        
        checks = {
            'SSH Connectivity': validation_results['ssh_connectivity'],
            'System Services': validation_results['system_services'],
            'Disk Space': validation_results['disk_space'],
            'System Load': validation_results['system_load']
        }
        
        for check_name, status in checks.items():
            status_text = "PASS" if status else "FAIL"
            color = "green" if status else "red"
            summary_rows += f"""
            <tr>
                <td>{check_name}</td>
                <td style="color: {color}; font-weight: bold;">{status_text}</td>
            </tr>
            """
        
        return f"""
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Validation Check</th>
                <th>Status</th>
            </tr>
            {summary_rows}
        </table>
        """
    
    def get_default_completion_template(self):
        """Default email template if file not found"""
        return """
        <html>
        <body>
            <h2>Patching Completion Notice</h2>
            
            <p><strong>Server:</strong> {server_name}</p>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Completion Time:</strong> {completion_time}</p>
            <p><strong>Location:</strong> {location}</p>
            
            <h3>Validation Results:</h3>
            {validation_summary}
            
            <p>This is an automated notification from the patching system.</p>
        </body>
        </html>
        """
