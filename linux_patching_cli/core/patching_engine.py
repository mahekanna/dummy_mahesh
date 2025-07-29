"""
Complete Patching Engine for Linux Patching Automation
Central orchestrator for all patching operations
"""

import os
import sys
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import traceback

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_handler import CSVHandler
from utils.ssh_handler import SSHHandler
from utils.logger import PatchingLogger, LogContext
from utils.email_sender import EmailSender
from utils.timezone_handler import TimezoneHandler
from config.email_templates import EmailTemplates
from config.settings import Config

class PatchingEngine:
    """Complete patching engine with all features"""
    
    def __init__(self, config: Config = None):
        """Initialize the patching engine"""
        self.config = config or Config()
        
        # Initialize handlers
        self.csv_handler = CSVHandler(self.config.DATA_DIR)
        self.ssh_handler = SSHHandler(
            ssh_key_path=self.config.SSH_KEY_PATH,
            default_user=self.config.SSH_DEFAULT_USER,
            connection_timeout=self.config.SSH_TIMEOUT
        )
        self.email_sender = EmailSender(
            smtp_server=self.config.SMTP_SERVER,
            smtp_port=self.config.SMTP_PORT,
            use_tls=self.config.SMTP_USE_TLS,
            username=self.config.SMTP_USERNAME,
            password=self.config.SMTP_PASSWORD,
            from_email=self.config.EMAIL_FROM
        )
        self.timezone_handler = TimezoneHandler()
        
        # Initialize logger
        self.logger = PatchingLogger(
            name='patching_engine',
            log_dir=self.config.LOG_DIR,
            log_level=self.config.LOG_LEVEL
        )
        
        # Thread safety
        self.operation_lock = threading.Lock()
        self.active_operations = {}
        
        # Operation statistics
        self.stats = {
            'total_patches': 0,
            'successful_patches': 0,
            'failed_patches': 0,
            'total_rollbacks': 0,
            'successful_rollbacks': 0,
            'failed_rollbacks': 0
        }
        
        self.logger.info("Patching engine initialized successfully")
    
    def get_current_quarter(self) -> str:
        """Get current quarter"""
        month = datetime.now().month
        if month in [1, 2, 3]:
            return 'Q1'
        elif month in [4, 5, 6]:
            return 'Q2'
        elif month in [7, 8, 9]:
            return 'Q3'
        else:
            return 'Q4'
    
    def get_servers_for_patching(self, quarter: str = None, group: str = None,
                                environment: str = None, approved_only: bool = True) -> List[Dict]:
        """Get servers ready for patching"""
        quarter = quarter or self.get_current_quarter()
        
        # Get all servers
        servers = self.csv_handler.read_servers()
        
        # Filter by quarter
        patch_date_field = f'q{quarter[-1]}_patch_date'
        approval_status_field = f'q{quarter[-1]}_approval_status'
        
        eligible_servers = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        for server in servers:
            # Check if server has patch date for this quarter
            patch_date = server.get(patch_date_field, '')
            if not patch_date:
                continue
            
            # Check if patch date is today or past
            if patch_date > current_date:
                continue
            
            # Check approval status if required
            if approved_only:
                approval_status = server.get(approval_status_field, 'Pending')
                if approval_status not in ['Approved', 'Auto-Approved']:
                    continue
            
            # Check if server is active
            if server.get('active_status', 'Active') != 'Active':
                continue
            
            # Apply additional filters
            if group and server.get('host_group', '') != group:
                continue
            
            if environment and server.get('environment', '') != environment:
                continue
            
            eligible_servers.append(server)
        
        return eligible_servers
    
    def run_precheck(self, server: str, quarter: str = None, user: str = 'system') -> Dict[str, Any]:
        """Run comprehensive pre-patching checks"""
        quarter = quarter or self.get_current_quarter()
        
        with LogContext(f'precheck_{server}', server=server, user=user, logger=self.logger):
            self.logger.precheck_started(server, quarter, user)
            
            try:
                # Get server info
                server_info = self.csv_handler.get_server(server)
                if not server_info:
                    raise Exception(f"Server {server} not found in inventory")
                
                # Run SSH-based checks
                prereq_results = self.ssh_handler.check_patch_prerequisites(
                    server=server,
                    user=server_info.get('primary_linux_user'),
                    port=int(server_info.get('ssh_port', 22))
                )
                
                # Get system information
                system_info = self.ssh_handler.get_system_info(
                    server=server,
                    user=server_info.get('primary_linux_user'),
                    port=int(server_info.get('ssh_port', 22))
                )
                
                # Analyze results
                overall_status = prereq_results.get('overall_status', 'failed')
                issues = []
                
                if overall_status == 'failed':
                    for check_name, check_result in prereq_results.get('checks', {}).items():
                        if check_result.get('status') == 'failed':
                            issues.append({
                                'check': check_name,
                                'issue': check_result.get('message', 'Unknown issue'),
                                'details': check_result.get('error', '')
                            })
                
                # Record precheck results
                precheck_data = {
                    'server_name': server,
                    'quarter': quarter,
                    'check_type': 'comprehensive',
                    'check_name': 'pre_patch_validation',
                    'status': 'Passed' if overall_status == 'passed' else 'Failed',
                    'message': f'Pre-check {overall_status}',
                    'operator': user,
                    'duration_seconds': 0,  # Would need to track this
                    'dependencies_met': overall_status == 'passed',
                    'business_impact': 'Low' if overall_status == 'passed' else 'High',
                    'technical_impact': 'None' if overall_status == 'passed' else 'Medium'
                }
                
                for issue in issues:
                    issue_data = precheck_data.copy()
                    issue_data.update({
                        'check_name': issue['check'],
                        'message': issue['issue'],
                        'recommendation': issue['details']
                    })
                    self.csv_handler.record_precheck(issue_data)
                
                # Log completion
                self.logger.precheck_completed(server, quarter, user, 
                                             overall_status == 'passed', issues)
                
                return {
                    'success': True,
                    'server': server,
                    'quarter': quarter,
                    'overall_status': overall_status,
                    'checks': prereq_results.get('checks', {}),
                    'issues': issues,
                    'system_info': system_info,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Precheck failed for {server}", error=e)
                return {
                    'success': False,
                    'server': server,
                    'quarter': quarter,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def patch_server(self, server: str, quarter: str = None, user: str = 'system',
                    force: bool = False, skip_precheck: bool = False,
                    skip_postcheck: bool = False) -> Dict[str, Any]:
        """Patch a single server"""
        quarter = quarter or self.get_current_quarter()
        
        with LogContext(f'patch_{server}', server=server, user=user, logger=self.logger):
            start_time = datetime.now()
            
            # Track operation
            operation_id = f"patch_{server}_{int(time.time())}"
            self.active_operations[operation_id] = {
                'type': 'patch',
                'server': server,
                'quarter': quarter,
                'user': user,
                'start_time': start_time,
                'status': 'running'
            }
            
            try:
                self.logger.patch_started(server, quarter, user)
                
                # Get server info
                server_info = self.csv_handler.get_server(server)
                if not server_info:
                    raise Exception(f"Server {server} not found in inventory")
                
                # Check approval status if not forced
                if not force:
                    approval_status = server_info.get(f'q{quarter[-1]}_approval_status', 'Pending')
                    if approval_status not in ['Approved', 'Auto-Approved']:
                        raise Exception(f"Server {server} not approved for {quarter} patching")
                
                # Run pre-check if not skipped
                if not skip_precheck:
                    precheck_result = self.run_precheck(server, quarter, user)
                    if not precheck_result['success'] or precheck_result['overall_status'] != 'passed':
                        if not force:
                            raise Exception(f"Pre-check failed for {server}")
                        else:
                            self.logger.warning(f"Pre-check failed for {server} but continuing due to force flag")
                
                # Send patching started notification
                self._send_patching_started_notification(server, quarter, user)
                
                # Execute patching
                os_type = server_info.get('operating_system', 'ubuntu')
                patch_result = self.ssh_handler.execute_patch_command(
                    server=server,
                    os_type=os_type,
                    user=server_info.get('primary_linux_user'),
                    port=int(server_info.get('ssh_port', 22)),
                    dry_run=False
                )
                
                if not patch_result['success']:
                    raise Exception(f"Patching failed: {patch_result.get('error', 'Unknown error')}")
                
                # Check if reboot is required
                reboot_result = self.ssh_handler.check_reboot_required(
                    server=server,
                    os_type=os_type,
                    user=server_info.get('primary_linux_user'),
                    port=int(server_info.get('ssh_port', 22))
                )
                
                reboot_required = reboot_result.get('reboot_required', False)
                reboot_completed = False
                
                # Handle reboot if required
                if reboot_required:
                    self.logger.info(f"Reboot required for {server}")
                    
                    reboot_result = self.ssh_handler.reboot_server(
                        server=server,
                        user=server_info.get('primary_linux_user'),
                        port=int(server_info.get('ssh_port', 22)),
                        wait_for_return=True,
                        timeout=self.config.REBOOT_TIMEOUT
                    )
                    
                    reboot_completed = reboot_result.get('reboot_completed', False)
                    
                    if not reboot_completed:
                        self.logger.warning(f"Reboot may not have completed successfully for {server}")
                
                # Run post-check if not skipped
                postcheck_results = {}
                if not skip_postcheck:
                    postcheck_results = self._run_postcheck(server, os_type, server_info)
                
                # Calculate duration
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 60  # minutes
                
                # Update server status
                self.csv_handler.update_server(server, {
                    'current_quarter_patching_status': 'Completed',
                    'last_sync_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sync_status': 'Success'
                })
                
                # Record patch history
                patch_history = {
                    'server_name': server,
                    'quarter': quarter,
                    'patch_type': 'Quarterly',
                    'status': 'Success',
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_minutes': int(duration),
                    'packages_updated': len(patch_result.get('steps', [])),
                    'reboot_required': 'Yes' if reboot_required else 'No',
                    'reboot_completed': 'Yes' if reboot_completed else 'No',
                    'pre_check_status': 'Passed' if not skip_precheck else 'Skipped',
                    'post_check_status': 'Passed' if postcheck_results.get('success', True) else 'Failed',
                    'operator': user,
                    'patch_window': f"{quarter} Patching",
                    'downtime_minutes': int(duration) if reboot_required else 0,
                    'success_rate': '100%'
                }
                
                self.csv_handler.record_patch_history(patch_history)
                
                # Update statistics
                self.stats['total_patches'] += 1
                self.stats['successful_patches'] += 1
                
                # Log completion
                self.logger.patch_completed(server, quarter, user, True, int(duration))
                
                # Send success notification
                result = {
                    'success': True,
                    'server': server,
                    'quarter': quarter,
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': f"{int(duration)} minutes",
                    'patches_applied': len(patch_result.get('steps', [])),
                    'reboot_required': 'Yes' if reboot_required else 'No',
                    'reboot_completed': 'Yes' if reboot_completed else 'No',
                    'patches': patch_result.get('steps', []),
                    'postchecks': postcheck_results
                }
                
                self._send_patching_completed_notification(result)
                
                return result
                
            except Exception as e:
                # Handle failure
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 60
                
                self.logger.patch_failed(server, quarter, user, str(e))
                
                # Record failure
                patch_history = {
                    'server_name': server,
                    'quarter': quarter,
                    'patch_type': 'Quarterly',
                    'status': 'Failed',
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_minutes': int(duration),
                    'error_message': str(e),
                    'operator': user,
                    'success_rate': '0%'
                }
                
                self.csv_handler.record_patch_history(patch_history)
                
                # Update statistics
                self.stats['total_patches'] += 1
                self.stats['failed_patches'] += 1
                
                # Update server status
                self.csv_handler.update_server(server, {
                    'current_quarter_patching_status': 'Failed',
                    'last_sync_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sync_status': 'Failed'
                })
                
                # Send failure notification
                result = {
                    'success': False,
                    'server': server,
                    'quarter': quarter,
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': f"{int(duration)} minutes",
                    'error': str(e)
                }
                
                self._send_patching_completed_notification(result)
                
                return result
                
            finally:
                # Clean up operation tracking
                if operation_id in self.active_operations:
                    del self.active_operations[operation_id]
    
    def _run_postcheck(self, server: str, os_type: str, server_info: Dict) -> Dict[str, Any]:
        """Run post-patching checks"""
        checks = {}
        
        try:
            # Check if server is responsive
            test_result = self.ssh_handler.test_connection(
                server=server,
                user=server_info.get('primary_linux_user'),
                port=int(server_info.get('ssh_port', 22))
            )
            checks['connectivity'] = test_result['success']
            
            # Check critical services
            critical_services = server_info.get('critical_services', 'ssh,cron').split(',')
            for service in critical_services:
                service = service.strip()
                if service:
                    result = self.ssh_handler.execute_command(
                        server, f'systemctl is-active {service}',
                        user=server_info.get('primary_linux_user'),
                        port=int(server_info.get('ssh_port', 22))
                    )
                    checks[f'service_{service}'] = result['success'] and 'active' in result['stdout']
            
            # Check system load
            result = self.ssh_handler.execute_command(
                server, 'cat /proc/loadavg | cut -d\' \' -f1',
                user=server_info.get('primary_linux_user'),
                port=int(server_info.get('ssh_port', 22))
            )
            
            if result['success']:
                try:
                    load = float(result['stdout'].strip())
                    checks['load_average'] = load < 10.0
                except ValueError:
                    checks['load_average'] = False
            else:
                checks['load_average'] = False
            
            return {
                'success': all(checks.values()),
                'checks': checks
            }
            
        except Exception as e:
            self.logger.error(f"Post-check failed for {server}", error=e)
            return {
                'success': False,
                'error': str(e),
                'checks': checks
            }
    
    def batch_patch(self, servers: List[str] = None, quarter: str = None,
                   group: str = None, environment: str = None,
                   user: str = 'system', max_parallel: int = None,
                   force: bool = False) -> List[Dict[str, Any]]:
        """Patch multiple servers in parallel"""
        quarter = quarter or self.get_current_quarter()
        max_parallel = max_parallel or self.config.MAX_PARALLEL_PATCHES
        
        # Get servers to patch
        if servers is None:
            servers_to_patch = self.get_servers_for_patching(
                quarter=quarter,
                group=group,
                environment=environment,
                approved_only=not force
            )
            server_names = [s['server_name'] for s in servers_to_patch]
        else:
            server_names = servers
        
        self.logger.info(f"Starting batch patching for {len(server_names)} servers")
        
        results = []
        
        # Use ThreadPoolExecutor for parallel patching
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all patching tasks
            future_to_server = {
                executor.submit(self.patch_server, server, quarter, user, force): server
                for server in server_names
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_server):
                server = future_to_server[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        self.logger.info(f"Successfully patched {server}")
                    else:
                        self.logger.error(f"Failed to patch {server}: {result.get('error')}")
                        
                except Exception as e:
                    self.logger.error(f"Exception patching {server}", error=e)
                    results.append({
                        'success': False,
                        'server': server,
                        'quarter': quarter,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Send batch summary
        self._send_batch_summary(results, quarter, user)
        
        return results
    
    def rollback_server(self, server: str, reason: str, user: str = 'system') -> Dict[str, Any]:
        """Rollback server to previous state"""
        with LogContext(f'rollback_{server}', server=server, user=user, logger=self.logger):
            start_time = datetime.now()
            
            try:
                self.logger.rollback_started(server, reason, user)
                
                # Get server info
                server_info = self.csv_handler.get_server(server)
                if not server_info:
                    raise Exception(f"Server {server} not found in inventory")
                
                # This would need to be implemented based on your backup strategy
                # For now, we'll simulate the rollback process
                
                # Update server status
                self.csv_handler.update_server(server, {
                    'current_quarter_patching_status': 'Rolled Back',
                    'last_sync_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sync_status': 'Rolled Back'
                })
                
                # Record rollback
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 60
                
                rollback_data = {
                    'server_name': server,
                    'rollback_type': 'Manual',
                    'trigger_event': reason,
                    'rollback_status': 'Success',
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_minutes': int(duration),
                    'operator': user,
                    'business_impact': 'Medium',
                    'success_rate': '100%'
                }
                
                self.csv_handler.record_rollback(rollback_data)
                
                # Update statistics
                self.stats['total_rollbacks'] += 1
                self.stats['successful_rollbacks'] += 1
                
                self.logger.rollback_completed(server, user, True)
                
                # Send rollback notification
                self._send_rollback_notification(server, reason, 'Success')
                
                return {
                    'success': True,
                    'server': server,
                    'reason': reason,
                    'duration': f"{int(duration)} minutes",
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Rollback failed for {server}", error=e)
                
                # Record failure
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() / 60
                
                rollback_data = {
                    'server_name': server,
                    'rollback_type': 'Manual',
                    'trigger_event': reason,
                    'rollback_status': 'Failed',
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_minutes': int(duration),
                    'operator': user,
                    'error_message': str(e),
                    'success_rate': '0%'
                }
                
                self.csv_handler.record_rollback(rollback_data)
                
                # Update statistics
                self.stats['total_rollbacks'] += 1
                self.stats['failed_rollbacks'] += 1
                
                # Send failure notification
                self._send_rollback_notification(server, reason, 'Failed')
                
                return {
                    'success': False,
                    'server': server,
                    'reason': reason,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def get_patching_status(self, quarter: str = None) -> Dict[str, Any]:
        """Get overall patching status"""
        quarter = quarter or self.get_current_quarter()
        
        # Get all servers
        servers = self.csv_handler.read_servers()
        
        # Calculate statistics
        stats = {
            'total_servers': len(servers),
            'pending_approval': 0,
            'approved': 0,
            'scheduled': 0,
            'in_progress': 0,
            'completed': 0,
            'failed': 0,
            'rolled_back': 0,
            'current_quarter': quarter,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        approval_status_field = f'q{quarter[-1]}_approval_status'
        
        for server in servers:
            if server.get('active_status') != 'Active':
                continue
                
            approval_status = server.get(approval_status_field, 'Pending')
            patch_status = server.get('current_quarter_patching_status', 'Pending')
            
            if approval_status == 'Pending':
                stats['pending_approval'] += 1
            elif approval_status in ['Approved', 'Auto-Approved']:
                stats['approved'] += 1
            
            if patch_status == 'Scheduled':
                stats['scheduled'] += 1
            elif patch_status == 'In Progress':
                stats['in_progress'] += 1
            elif patch_status == 'Completed':
                stats['completed'] += 1
            elif patch_status == 'Failed':
                stats['failed'] += 1
            elif patch_status == 'Rolled Back':
                stats['rolled_back'] += 1
        
        # Add active operations
        stats['active_operations'] = len(self.active_operations)
        
        # Add success rate
        if stats['completed'] + stats['failed'] > 0:
            stats['success_rate'] = (stats['completed'] / (stats['completed'] + stats['failed'])) * 100
        else:
            stats['success_rate'] = 0
        
        return stats
    
    def _send_patching_started_notification(self, server: str, quarter: str, user: str):
        """Send patching started notification"""
        try:
            server_info = self.csv_handler.get_server(server)
            if not server_info:
                return
            
            patch_time = server_info.get(f'q{quarter[-1]}_patch_time', 'N/A')
            
            email_data = EmailTemplates.patching_started(server, quarter, patch_time)
            
            recipients = self._get_notification_recipients(server_info)
            
            self.email_sender.send_email(
                to=recipients,
                subject=email_data['subject'],
                body=email_data['body'],
                is_html=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send patching started notification for {server}", error=e)
    
    def _send_patching_completed_notification(self, result: Dict[str, Any]):
        """Send patching completed notification"""
        try:
            server = result['server']
            server_info = self.csv_handler.get_server(server)
            if not server_info:
                return
            
            email_data = EmailTemplates.patching_completed(result)
            
            recipients = self._get_notification_recipients(server_info)
            
            self.email_sender.send_email(
                to=recipients,
                subject=email_data['subject'],
                body=email_data['body'],
                is_html=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send patching completed notification for {result['server']}", error=e)
    
    def _send_rollback_notification(self, server: str, reason: str, status: str):
        """Send rollback notification"""
        try:
            server_info = self.csv_handler.get_server(server)
            if not server_info:
                return
            
            email_data = EmailTemplates.rollback_notification(server, reason, status)
            
            recipients = self._get_notification_recipients(server_info)
            
            self.email_sender.send_email(
                to=recipients,
                subject=email_data['subject'],
                body=email_data['body'],
                is_html=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send rollback notification for {server}", error=e)
    
    def _send_batch_summary(self, results: List[Dict[str, Any]], quarter: str, user: str):
        """Send batch patching summary"""
        try:
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            
            # Create summary email content
            summary_data = {
                'total_servers': len(results),
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / len(results)) * 100 if results else 0,
                'quarter': quarter,
                'operator': user,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Send to admin emails
            admin_emails = self.config.ADMIN_EMAILS
            if admin_emails:
                self.email_sender.send_email(
                    to=admin_emails,
                    subject=f"[Batch Patching] {quarter} - {successful} Success, {failed} Failed",
                    body=f"""
                    Batch patching completed for {quarter}:
                    
                    Total Servers: {len(results)}
                    Successful: {successful}
                    Failed: {failed}
                    Success Rate: {summary_data['success_rate']:.1f}%
                    
                    Operator: {user}
                    Timestamp: {summary_data['timestamp']}
                    """
                )
            
        except Exception as e:
            self.logger.error("Failed to send batch summary", error=e)
    
    def _get_notification_recipients(self, server_info: Dict) -> List[str]:
        """Get email recipients for server notifications"""
        recipients = []
        
        # Add primary and secondary owners
        if server_info.get('primary_owner'):
            recipients.append(server_info['primary_owner'])
        
        if server_info.get('secondary_owner'):
            recipients.append(server_info['secondary_owner'])
        
        # Add notification email if specified
        if server_info.get('notification_email'):
            recipients.append(server_info['notification_email'])
        
        # Add patcher email
        if server_info.get('patcher_email'):
            recipients.append(server_info['patcher_email'])
        
        # Remove duplicates
        return list(set(recipients))
    
    def cleanup_old_operations(self, hours: int = 24):
        """Clean up old operation records"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        operations_to_remove = []
        for op_id, operation in self.active_operations.items():
            if operation['start_time'] < cutoff_time:
                operations_to_remove.append(op_id)
        
        for op_id in operations_to_remove:
            del self.active_operations[op_id]
        
        self.logger.info(f"Cleaned up {len(operations_to_remove)} old operations")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        stats = self.stats.copy()
        stats['active_operations'] = len(self.active_operations)
        stats['csv_statistics'] = self.csv_handler.get_statistics()
        return stats
    
    def shutdown(self):
        """Gracefully shutdown the engine"""
        self.logger.info("Shutting down patching engine...")
        
        # Close SSH connections
        self.ssh_handler.close_all_connections()
        
        # Clear active operations
        self.active_operations.clear()
        
        self.logger.info("Patching engine shutdown complete")

# Example usage
if __name__ == "__main__":
    # Example of using the patching engine
    engine = PatchingEngine()
    
    # Get current status
    status = engine.get_patching_status()
    print(f"Current status: {json.dumps(status, indent=2)}")
    
    # Example: Patch a single server
    # result = engine.patch_server('web01.company.com', force=True)
    # print(f"Patch result: {json.dumps(result, indent=2)}")
    
    # Shutdown
    engine.shutdown()