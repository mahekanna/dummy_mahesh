# scripts/step5_patch_validation.py
import subprocess
import json
import os
from datetime import datetime
from utils.csv_handler import CSVHandler
from utils.email_sender import EmailSender
from utils.logger import Logger
from database.models import DatabaseManager
from config.settings import Config

class PatchValidator:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.email_sender = EmailSender()
        self.logger = Logger('patch_validator')
        self.db_manager = None
    
    def connect_db(self):
        """Connect to database"""
        if not self.db_manager:
            self.db_manager = DatabaseManager()
            self.db_manager.connect()
    
    def validate_patches(self, server_name):
        """Validate installed patches on server"""
        self.logger.info(f"Starting patch validation for {server_name}")
        
        validation_results = {
            'server_name': server_name,
            'validation_time': datetime.now().isoformat(),
            'patches_applied': [],
            'failed_patches': [],
            'system_status': 'unknown',
            'reboot_required': False
        }
        
        try:
            # Check system status
            validation_results['system_status'] = self.check_system_status(server_name)
            
            # Validate applied patches
            validation_results['patches_applied'] = self.get_applied_patches(server_name)
            
            # Check for failed patches
            validation_results['failed_patches'] = self.get_failed_patches(server_name)
            
            # Check if reboot is required
            validation_results['reboot_required'] = self.check_reboot_required(server_name)
            
            # Process results
            success = self.process_validation_results(validation_results)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Patch validation failed for {server_name}: {e}")
            self.send_validation_failure_alert(server_name, str(e))
            return False
    
    def check_system_status(self, server_name):
        """Check overall system status"""
        try:
            result = subprocess.run(
                ['ssh', server_name, 'systemctl', 'is-system-running'],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Error checking system status for {server_name}: {e}")
            return 'unknown'
    
    def get_applied_patches(self, server_name):
        """Get list of applied patches"""
        patches = []
        try:
            # Check OS type first
            os_result = subprocess.run(
                ['ssh', server_name, 'cat', '/etc/os-release'],
                capture_output=True, text=True, timeout=30
            )
            
            if 'rhel' in os_result.stdout.lower() or 'red hat' in os_result.stdout.lower():
                # RHEL 8.10 specific handling with 4 batches
                patches = self.get_rhel_batch_patches(server_name)
            elif 'ubuntu' in os_result.stdout.lower() or 'debian' in os_result.stdout.lower():
                # Ubuntu/Debian systems - keep as is
                patches = self.get_ubuntu_patches(server_name)
            else:
                # Generic RHEL/CentOS handling
                patches = self.get_generic_rhel_patches(server_name)
                    
        except Exception as e:
            self.logger.warning(f"Could not retrieve patch list for {server_name}: {e}")
        
        return patches
    
    def get_rhel_batch_patches(self, server_name):
        """Get RHEL 8.10 batch patch information from yum history and custom logs"""
        patches = []
        batch_info = {
            'java_batches': [],
            'security_kernel_batch': {},
            'total_patches': 0,
            'batch_times': []
        }
        
        try:
            # Get recent yum history transactions (last 10)
            result = subprocess.run(
                ['ssh', server_name, 'yum', 'history', 'list', 'last', '10'],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                transaction_ids = []
                
                # Extract transaction IDs from today's operations
                for line in lines[2:]:  # Skip header lines
                    if 'Update' in line or 'Install' in line:
                        # Extract transaction ID (first column)
                        tid = line.strip().split()[0]
                        if tid.isdigit():
                            transaction_ids.append(tid)
                
                # Get detailed info for each transaction (last 4 should be our batches)
                for tid in transaction_ids[-4:]:  # Last 4 transactions
                    batch_details = self.get_yum_history_details(server_name, tid)
                    if batch_details:
                        patches.append(batch_details)
                        batch_info['batch_times'].append({
                            'transaction_id': tid,
                            'begin_time': batch_details.get('begin_time'),
                            'end_time': batch_details.get('end_time'),
                            'return_code': batch_details.get('return_code'),
                            'packages_count': len(batch_details.get('packages', []))
                        })
            
            # Also check custom yum update logs if available
            custom_logs = self.get_custom_yum_logs(server_name)
            if custom_logs:
                batch_info['custom_logs'] = custom_logs
                patches.extend(custom_logs)
            
            # Log batch summary
            self.logger.info(f"RHEL Batch Summary for {server_name}: {json.dumps(batch_info, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Error getting RHEL batch patches for {server_name}: {e}")
        
        return patches
    
    def get_yum_history_details(self, server_name, transaction_id):
        """Get detailed information for a specific yum transaction"""
        try:
            result = subprocess.run(
                ['ssh', server_name, 'yum', 'history', 'info', transaction_id],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                details = {
                    'transaction_id': transaction_id,
                    'packages': [],
                    'begin_time': None,
                    'end_time': None,
                    'return_code': None,
                    'command_line': None
                }
                
                lines = result.stdout.strip().split('\n')
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    
                    if 'Begin time' in line:
                        details['begin_time'] = line.split(':', 1)[1].strip()
                    elif 'End time' in line:
                        details['end_time'] = line.split(':', 1)[1].strip()
                    elif 'Return-Code' in line:
                        details['return_code'] = line.split(':', 1)[1].strip()
                    elif 'Command Line' in line:
                        details['command_line'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Updated') or line.startswith('Installed'):
                        current_section = 'packages'
                    elif current_section == 'packages' and line and not line.startswith(' '):
                        if any(char.isdigit() for char in line):  # Package line with version
                            details['packages'].append(line)
                
                return details
                
        except Exception as e:
            self.logger.warning(f"Could not get yum history details for transaction {transaction_id}: {e}")
        
        return None
    
    def get_custom_yum_logs(self, server_name):
        """Get information from custom yum update logs in /var/log/kickstart/yumupdate"""
        logs = []
        try:
            # Check if custom log directory exists
            result = subprocess.run(
                ['ssh', server_name, 'ls', '-la', '/var/log/kickstart/yumupdate/'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                # Get today's log files
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Look for batch log files
                for batch_num in [1, 2, 3, 4]:
                    log_pattern = f"*{today}*batch{batch_num}*"
                    log_result = subprocess.run(
                        ['ssh', server_name, 'find', '/var/log/kickstart/yumupdate/', 
                         '-name', log_pattern, '-type', 'f'],
                        capture_output=True, text=True, timeout=30
                    )
                    
                    if log_result.returncode == 0 and log_result.stdout.strip():
                        log_files = log_result.stdout.strip().split('\n')
                        for log_file in log_files:
                            log_content = self.parse_custom_yum_log(server_name, log_file, batch_num)
                            if log_content:
                                logs.append(log_content)
                                
        except Exception as e:
            self.logger.warning(f"Could not access custom yum logs for {server_name}: {e}")
        
        return logs
    
    def parse_custom_yum_log(self, server_name, log_file, batch_num):
        """Parse individual custom yum log file"""
        try:
            result = subprocess.run(
                ['ssh', server_name, 'cat', log_file],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                content = result.stdout
                
                log_info = {
                    'batch_number': batch_num,
                    'log_file': log_file,
                    'batch_type': 'java_updates' if batch_num <= 3 else 'security_kernel_updates',
                    'packages_updated': [],
                    'errors': [],
                    'start_time': None,
                    'end_time': None
                }
                
                # Parse log content for relevant information
                lines = content.split('\n')
                for line in lines:
                    if 'Updated:' in line or 'Installed:' in line:
                        log_info['packages_updated'].append(line.strip())
                    elif 'Error:' in line or 'FAILED' in line:
                        log_info['errors'].append(line.strip())
                    elif any(time_marker in line for time_marker in ['Started', 'Begin', 'Starting']):
                        log_info['start_time'] = line.strip()
                    elif any(time_marker in line for time_marker in ['Completed', 'Finished', 'End']):
                        log_info['end_time'] = line.strip()
                
                return log_info
                
        except Exception as e:
            self.logger.warning(f"Could not parse custom yum log {log_file}: {e}")
        
        return None
    
    def get_ubuntu_patches(self, server_name):
        """Get Ubuntu/Debian patch information - keep existing logic"""
        patches = []
        try:
            result = subprocess.run(
                ['ssh', server_name, 'grep', 'install', '/var/log/dpkg.log'],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # Get last 10 entries
                    patches.append(line.strip())
                    
        except Exception as e:
            self.logger.warning(f"Could not retrieve Ubuntu patches for {server_name}: {e}")
        
        return patches
    
    def get_generic_rhel_patches(self, server_name):
        """Get generic RHEL/CentOS patch information"""
        patches = []
        try:
            result = subprocess.run(
                ['ssh', server_name, 'yum', 'history', 'list', 'last'],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[2:]:  # Skip header lines
                    if 'Update' in line or 'Install' in line:
                        patches.append(line.strip())
                        
        except Exception as e:
            self.logger.warning(f"Could not retrieve generic RHEL patches for {server_name}: {e}")
        
        return patches
    
    def get_failed_patches(self, server_name):
        """Check for failed package installations"""
        failed = []
        try:
            # Check OS type first
            os_result = subprocess.run(
                ['ssh', server_name, 'cat', '/etc/os-release'],
                capture_output=True, text=True, timeout=30
            )
            
            if 'rhel' in os_result.stdout.lower() or 'red hat' in os_result.stdout.lower():
                # RHEL 8.10 specific failure checking
                failed = self.get_rhel_batch_failures(server_name)
            else:
                # Generic failure checking
                failed = self.get_generic_failures(server_name)
                        
        except Exception as e:
            self.logger.warning(f"Could not check for failed patches on {server_name}: {e}")
        
        return failed
    
    def get_rhel_batch_failures(self, server_name):
        """Check for RHEL batch update failures"""
        failures = []
        
        try:
            # Check yum history for failed transactions
            result = subprocess.run(
                ['ssh', server_name, 'yum', 'history', 'list', 'last', '10'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                transaction_ids = []
                
                for line in lines[2:]:  # Skip header lines
                    if 'Update' in line or 'Install' in line:
                        tid = line.strip().split()[0]
                        if tid.isdigit():
                            transaction_ids.append(tid)
                
                # Check return codes for recent transactions
                for tid in transaction_ids[-4:]:  # Last 4 transactions (our batches)
                    details = self.get_yum_history_details(server_name, tid)
                    if details and details.get('return_code'):
                        return_code = details['return_code']
                        if return_code != 'Success' and return_code != '0':
                            failures.append({
                                'transaction_id': tid,
                                'return_code': return_code,
                                'command': details.get('command_line', ''),
                                'begin_time': details.get('begin_time'),
                                'end_time': details.get('end_time')
                            })
            
            # Also check custom logs for errors
            custom_log_failures = self.check_custom_log_failures(server_name)
            if custom_log_failures:
                failures.extend(custom_log_failures)
                
        except Exception as e:
            self.logger.warning(f"Could not check RHEL batch failures for {server_name}: {e}")
        
        return failures
    
    def check_custom_log_failures(self, server_name):
        """Check custom yum logs for failures"""
        failures = []
        
        try:
            # Check if custom log directory exists
            result = subprocess.run(
                ['ssh', server_name, 'ls', '/var/log/kickstart/yumupdate/'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Check each batch log for errors
                for batch_num in [1, 2, 3, 4]:
                    log_pattern = f"*{today}*batch{batch_num}*"
                    log_result = subprocess.run(
                        ['ssh', server_name, 'find', '/var/log/kickstart/yumupdate/', 
                         '-name', log_pattern, '-type', 'f'],
                        capture_output=True, text=True, timeout=30
                    )
                    
                    if log_result.returncode == 0 and log_result.stdout.strip():
                        log_files = log_result.stdout.strip().split('\n')
                        for log_file in log_files:
                            # Check for errors in log file
                            error_result = subprocess.run(
                                ['ssh', server_name, 'grep', '-i', 
                                 '-E', '(error|fail|abort|exception)', log_file],
                                capture_output=True, text=True, timeout=30
                            )
                            
                            if error_result.returncode == 0 and error_result.stdout.strip():
                                failures.append({
                                    'batch_number': batch_num,
                                    'log_file': log_file,
                                    'errors': error_result.stdout.strip().split('\n')
                                })
                                
        except Exception as e:
            self.logger.warning(f"Could not check custom log failures for {server_name}: {e}")
        
        return failures
    
    def get_generic_failures(self, server_name):
        """Generic failure checking for non-RHEL systems"""
        failed = []
        
        try:
            # Check yum/dnf transaction failures
            result = subprocess.run(
                ['ssh', server_name, 'yum', 'history', 'list', 'last'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Failed' in line or 'Error' in line:
                        failed.append(line.strip())
                        
        except Exception as e:
            self.logger.warning(f"Could not check generic failures for {server_name}: {e}")
        
        return failed
    
    def check_reboot_required(self, server_name):
        """Check if system reboot is required"""
        try:
            # Check for reboot-required file (Ubuntu/Debian)
            result = subprocess.run(
                ['ssh', server_name, 'test', '-f', '/var/run/reboot-required'],
                capture_output=True, timeout=15
            )
            
            if result.returncode == 0:
                return True
            
            # Check for needs-restarting (RHEL/CentOS)
            result = subprocess.run(
                ['ssh', server_name, 'needs-restarting', '-r'],
                capture_output=True, timeout=15
            )
            
            return result.returncode == 1  # needs-restarting returns 1 if reboot needed
            
        except Exception as e:
            self.logger.warning(f"Could not check if reboot required for {server_name}: {e}")
            return True  # Default to requiring reboot for safety
    
    def process_validation_results(self, results):
        """Process validation results and determine success"""
        server_name = results['server_name']
        
        # Log results
        self.logger.info(f"Validation results for {server_name}: {json.dumps(results, indent=2)}")
        
        # Determine if validation passed - enhanced for RHEL batch processing
        success = self.evaluate_batch_success(results)
        
        # Record results in database
        self.connect_db()
        
        # Find server details to get quarter info
        servers = self.csv_handler.read_servers()
        server_info = None
        for server in servers:
            if server['Server Name'] == server_name:
                server_info = server
                break
        
        if server_info:
            # Determine current quarter and year
            current_quarter = int(Config.get_current_quarter())
            current_year = datetime.now().year
            
            # Get patch date and time
            patch_date = server_info.get(f'Q{current_quarter} Patch Date')
            patch_time = server_info.get(f'Q{current_quarter} Patch Time')
            
            # Update patch status in database
            if self.db_manager:
                status = 'completed' if success else 'failed'
                details = json.dumps(results)
                
                # Record in patch history
                self.db_manager.record_patch_history(
                    server_name, patch_date, patch_time, 
                    current_quarter, current_year, status, details
                )
        
        if not success:
            self.send_validation_failure_alert(server_name, results)
        
        return success
    
    def evaluate_batch_success(self, results):
        """Evaluate success based on patch type and batch results"""
        
        # Basic system status check
        if results['system_status'] not in ['running', 'degraded']:
            return False
        
        failed_patches = results.get('failed_patches', [])
        applied_patches = results.get('patches_applied', [])
        
        # If we have batch-specific data (RHEL), analyze each batch
        if isinstance(applied_patches, list) and len(applied_patches) > 0:
            if isinstance(applied_patches[0], dict) and 'transaction_id' in applied_patches[0]:
                # This is RHEL batch data
                return self.evaluate_rhel_batch_results(applied_patches, failed_patches)
        
        # For non-batch systems or generic validation
        return len(failed_patches) == 0
    
    def evaluate_rhel_batch_results(self, batch_results, failed_patches):
        """Evaluate RHEL batch update results"""
        
        total_batches = len(batch_results)
        successful_batches = 0
        java_batches_success = 0
        security_kernel_success = False
        
        self.logger.info(f"Evaluating {total_batches} RHEL batch results")
        
        for batch in batch_results:
            if isinstance(batch, dict):
                return_code = batch.get('return_code', 'Unknown')
                transaction_id = batch.get('transaction_id', 'Unknown')
                packages_count = len(batch.get('packages', []))
                
                # Check if batch was successful
                batch_success = (return_code in ['Success', '0', 'Complete'])
                
                if batch_success:
                    successful_batches += 1
                
                self.logger.info(f"Batch {transaction_id}: {return_code}, {packages_count} packages, Success: {batch_success}")
        
        # Also check custom log results if available
        for failure in failed_patches:
            if isinstance(failure, dict):
                if failure.get('batch_number'):
                    batch_num = failure['batch_number']
                    errors = failure.get('errors', [])
                    if errors:
                        self.logger.warning(f"Batch {batch_num} has errors: {len(errors)} error lines")
        
        # Success criteria for RHEL batches:
        # - At least 3 out of 4 batches should be successful
        # - If java batches (1-3) fail, it's less critical than security/kernel batch (4)
        
        success_rate = successful_batches / max(total_batches, 1)
        
        # Log batch summary
        summary = {
            'total_batches': total_batches,
            'successful_batches': successful_batches,
            'success_rate': success_rate,
            'failures': len(failed_patches)
        }
        
        self.logger.info(f"RHEL Batch Summary: {json.dumps(summary, indent=2)}")
        
        # Consider successful if at least 75% of batches succeeded and no critical failures
        return success_rate >= 0.75 and len([f for f in failed_patches if isinstance(f, dict) and f.get('errors')]) == 0
    
    def send_validation_failure_alert(self, server_name, error_info):
        """Send alert for patch validation failure"""
        subject = f"Patch Validation Failed: {server_name}"
        
        if isinstance(error_info, dict):
            message_body = f"""
            Patch validation failed for server: {server_name}
            
            System Status: {error_info.get('system_status', 'unknown')}
            Failed Patches: {len(error_info.get('failed_patches', []))}
            Applied Patches: {len(error_info.get('patches_applied', []))}
            
            Failed Patch Details:
            {chr(10).join(error_info.get('failed_patches', []))}
            
            Please investigate and remediate before proceeding.
            """
        else:
            message_body = f"""
            Patch validation failed for server: {server_name}
            
            Error: {error_info}
            
            Please investigate and remediate.
            """
        
        # Send to admin email
        admin_email = "admin@company.com"  # Configure this
        self.email_sender.send_email(admin_email, subject, message_body)
        
        # Send to server owners
        servers = self.csv_handler.read_servers()
        for server in servers:
            if server['Server Name'] == server_name:
                recipients = []
                if server.get('primary_owner'):
                    recipients.append(server['primary_owner'])
                if server.get('secondary_owner'):
                    recipients.append(server['secondary_owner'])
                
                for recipient in recipients:
                    if recipient:
                        self.email_sender.send_email(recipient, subject, message_body)
                break
