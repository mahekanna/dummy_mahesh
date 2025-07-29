"""
SSH Handler for Linux Patching Automation
Handles all SSH operations for remote server management
"""

import paramiko
import socket
import time
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import subprocess
import select
import sys

from .logger import get_logger

class SSHHandler:
    """Comprehensive SSH handler for remote server operations"""
    
    def __init__(self, ssh_key_path: str = None, default_user: str = 'patchadmin',
                 default_port: int = 22, connection_timeout: int = 30,
                 command_timeout: int = 300):
        """
        Initialize SSH handler
        
        Args:
            ssh_key_path: Path to SSH private key
            default_user: Default SSH user
            default_port: Default SSH port
            connection_timeout: Connection timeout in seconds
            command_timeout: Command execution timeout in seconds
        """
        self.ssh_key_path = ssh_key_path or os.path.expanduser('~/.ssh/id_rsa')
        self.default_user = default_user
        self.default_port = default_port
        self.connection_timeout = connection_timeout
        self.command_timeout = command_timeout
        
        # Connection pool
        self.connections = {}
        self.connection_lock = threading.Lock()
        
        # Load SSH key
        self.ssh_key = self._load_ssh_key()
        
        # Logger
        self.logger = get_logger('ssh_handler')
    
    def _load_ssh_key(self) -> paramiko.RSAKey:
        """Load SSH private key"""
        try:
            if os.path.exists(self.ssh_key_path):
                return paramiko.RSAKey.from_private_key_file(self.ssh_key_path)
            else:
                self.logger.warning(f"SSH key not found at {self.ssh_key_path}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load SSH key: {e}")
            return None
    
    def get_connection(self, server: str, user: str = None, port: int = None,
                      password: str = None) -> paramiko.SSHClient:
        """Get or create SSH connection"""
        user = user or self.default_user
        port = port or self.default_port
        conn_key = f"{user}@{server}:{port}"
        
        with self.connection_lock:
            # Check if connection exists and is alive
            if conn_key in self.connections:
                client = self.connections[conn_key]
                if client.get_transport() and client.get_transport().is_active():
                    return client
                else:
                    # Connection is dead, remove it
                    del self.connections[conn_key]
            
            # Create new connection
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                if password:
                    client.connect(server, port=port, username=user, password=password,
                                 timeout=self.connection_timeout)
                elif self.ssh_key:
                    client.connect(server, port=port, username=user, pkey=self.ssh_key,
                                 timeout=self.connection_timeout)
                else:
                    client.connect(server, port=port, username=user,
                                 timeout=self.connection_timeout)
                
                self.connections[conn_key] = client
                self.logger.debug(f"Created SSH connection to {conn_key}")
                return client
            
            except Exception as e:
                self.logger.error(f"Failed to connect to {conn_key}: {e}")
                raise
    
    def execute_command(self, server: str, command: str, user: str = None,
                       port: int = None, password: str = None,
                       timeout: int = None, sudo: bool = False,
                       sudo_password: str = None) -> Dict[str, Any]:
        """Execute command on remote server"""
        timeout = timeout or self.command_timeout
        
        if sudo and not command.startswith('sudo'):
            command = f"sudo {command}"
        
        try:
            client = self.get_connection(server, user, port, password)
            
            self.logger.debug(f"Executing command on {server}: {command}")
            
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            # Handle sudo password if needed
            if sudo and sudo_password:
                stdin.write(sudo_password + '\n')
                stdin.flush()
            
            # Read output
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            result = {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'stdout': stdout_data,
                'stderr': stderr_data,
                'command': command,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
            
            if exit_code != 0:
                self.logger.warning(f"Command failed on {server}: {command} (exit code: {exit_code})")
                self.logger.debug(f"STDERR: {stderr_data}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to execute command on {server}: {e}")
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'command': command,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
    
    def execute_interactive_command(self, server: str, command: str, 
                                   responses: Dict[str, str] = None,
                                   user: str = None, port: int = None,
                                   timeout: int = None) -> Dict[str, Any]:
        """Execute interactive command with predefined responses"""
        responses = responses or {}
        timeout = timeout or self.command_timeout
        
        try:
            client = self.get_connection(server, user, port)
            
            self.logger.debug(f"Executing interactive command on {server}: {command}")
            
            # Create channel for interactive session
            channel = client.invoke_shell()
            
            # Send command
            channel.send(command + '\n')
            
            output = ""
            start_time = time.time()
            
            while True:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Command timed out after {timeout} seconds")
                
                # Check if data is available
                if channel.recv_ready():
                    data = channel.recv(1024).decode('utf-8')
                    output += data
                    
                    # Check for prompts and send responses
                    for prompt, response in responses.items():
                        if prompt in data:
                            channel.send(response + '\n')
                            break
                
                # Check if command is complete
                if channel.exit_status_ready():
                    break
                
                time.sleep(0.1)
            
            exit_code = channel.recv_exit_status()
            channel.close()
            
            return {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'output': output,
                'command': command,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Failed to execute interactive command on {server}: {e}")
            return {
                'success': False,
                'exit_code': -1,
                'output': str(e),
                'command': command,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
    
    def upload_file(self, server: str, local_path: str, remote_path: str,
                   user: str = None, port: int = None,
                   backup: bool = True) -> Dict[str, Any]:
        """Upload file to remote server"""
        try:
            client = self.get_connection(server, user, port)
            sftp = client.open_sftp()
            
            self.logger.debug(f"Uploading {local_path} to {server}:{remote_path}")
            
            # Create backup if requested
            if backup:
                backup_path = f"{remote_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    sftp.stat(remote_path)  # Check if file exists
                    sftp.rename(remote_path, backup_path)
                    self.logger.debug(f"Created backup: {backup_path}")
                except FileNotFoundError:
                    pass  # File doesn't exist, no backup needed
            
            # Upload file
            sftp.put(local_path, remote_path)
            sftp.close()
            
            return {
                'success': True,
                'local_path': local_path,
                'remote_path': remote_path,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Failed to upload file to {server}: {e}")
            return {
                'success': False,
                'error': str(e),
                'local_path': local_path,
                'remote_path': remote_path,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
    
    def download_file(self, server: str, remote_path: str, local_path: str,
                     user: str = None, port: int = None) -> Dict[str, Any]:
        """Download file from remote server"""
        try:
            client = self.get_connection(server, user, port)
            sftp = client.open_sftp()
            
            self.logger.debug(f"Downloading {server}:{remote_path} to {local_path}")
            
            # Create local directory if it doesn't exist
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            sftp.get(remote_path, local_path)
            sftp.close()
            
            return {
                'success': True,
                'remote_path': remote_path,
                'local_path': local_path,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Failed to download file from {server}: {e}")
            return {
                'success': False,
                'error': str(e),
                'remote_path': remote_path,
                'local_path': local_path,
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
    
    def test_connection(self, server: str, user: str = None, port: int = None,
                       password: str = None) -> Dict[str, Any]:
        """Test SSH connection to server"""
        try:
            start_time = time.time()
            client = self.get_connection(server, user, port, password)
            
            # Test basic command
            result = self.execute_command(server, 'echo "connection_test"', user, port, password)
            
            if result['success'] and 'connection_test' in result['stdout']:
                connection_time = time.time() - start_time
                return {
                    'success': True,
                    'server': server,
                    'connection_time': connection_time,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'server': server,
                    'error': 'Connection test command failed',
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            return {
                'success': False,
                'server': server,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_info(self, server: str, user: str = None, port: int = None) -> Dict[str, Any]:
        """Get system information from remote server"""
        commands = {
            'hostname': 'hostname -f',
            'os_info': 'cat /etc/os-release',
            'uptime': 'uptime',
            'disk_usage': 'df -h',
            'memory_info': 'free -h',
            'cpu_info': 'lscpu',
            'load_average': 'cat /proc/loadavg',
            'kernel_version': 'uname -r',
            'timezone': 'timedatectl | grep "Time zone" || cat /etc/timezone',
            'last_reboot': 'who -b 2>/dev/null || last reboot -n 1',
            'network_info': 'ip addr show | grep -E "inet |link/"',
            'running_services': 'systemctl list-units --type=service --state=running | head -20'
        }
        
        system_info = {
            'server': server,
            'timestamp': datetime.now().isoformat(),
            'success': True,
            'data': {}
        }
        
        for info_type, command in commands.items():
            try:
                result = self.execute_command(server, command, user, port, timeout=30)
                if result['success']:
                    system_info['data'][info_type] = result['stdout'].strip()
                else:
                    system_info['data'][info_type] = f"Error: {result['stderr']}"
            except Exception as e:
                system_info['data'][info_type] = f"Error: {str(e)}"
        
        return system_info
    
    def check_patch_prerequisites(self, server: str, user: str = None, port: int = None) -> Dict[str, Any]:
        """Check if server meets patching prerequisites"""
        checks = {
            'connectivity': {'command': 'echo "connected"', 'expected': 'connected'},
            'sudo_access': {'command': 'sudo -n true', 'expected': None},
            'disk_space': {'command': 'df / | tail -1 | awk \'{print $5}\'', 'threshold': 80},
            'load_average': {'command': 'cat /proc/loadavg | cut -d\' \' -f1', 'threshold': 10.0},
            'memory_usage': {'command': 'free | grep Mem | awk \'{print ($3/$2) * 100.0}\'', 'threshold': 95.0},
            'package_manager': {'command': 'which apt-get || which yum || which dnf', 'expected': None},
            'reboot_required': {'command': '[ -f /var/run/reboot-required ] && echo "yes" || echo "no"', 'expected': None},
            'critical_services': {'command': 'systemctl is-active sshd', 'expected': 'active'},
            'update_availability': {'command': 'apt list --upgradable 2>/dev/null | wc -l || yum check-update -q | wc -l', 'expected': None}
        }
        
        results = {
            'server': server,
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'passed',
            'checks': {}
        }
        
        for check_name, check_config in checks.items():
            try:
                result = self.execute_command(server, check_config['command'], user, port, timeout=30)
                
                check_result = {
                    'command': check_config['command'],
                    'success': result['success'],
                    'output': result['stdout'].strip(),
                    'error': result['stderr'].strip() if result['stderr'] else None
                }
                
                # Evaluate check result
                if not result['success']:
                    check_result['status'] = 'failed'
                    check_result['message'] = f"Command failed: {result['stderr']}"
                    results['overall_status'] = 'failed'
                
                elif check_config.get('expected'):
                    if check_config['expected'] in result['stdout']:
                        check_result['status'] = 'passed'
                        check_result['message'] = 'Check passed'
                    else:
                        check_result['status'] = 'failed'
                        check_result['message'] = f"Expected '{check_config['expected']}' but got '{result['stdout'].strip()}'"
                        results['overall_status'] = 'failed'
                
                elif check_config.get('threshold'):
                    try:
                        value = float(result['stdout'].strip().replace('%', ''))
                        if value < check_config['threshold']:
                            check_result['status'] = 'passed'
                            check_result['message'] = f'Value {value} is below threshold {check_config["threshold"]}'
                        else:
                            check_result['status'] = 'failed'
                            check_result['message'] = f'Value {value} exceeds threshold {check_config["threshold"]}'
                            results['overall_status'] = 'failed'
                    except ValueError:
                        check_result['status'] = 'failed'
                        check_result['message'] = f'Invalid numeric value: {result["stdout"].strip()}'
                        results['overall_status'] = 'failed'
                
                else:
                    check_result['status'] = 'passed'
                    check_result['message'] = 'Check completed'
                
                results['checks'][check_name] = check_result
            
            except Exception as e:
                results['checks'][check_name] = {
                    'command': check_config['command'],
                    'success': False,
                    'status': 'error',
                    'message': f'Exception: {str(e)}',
                    'error': str(e)
                }
                results['overall_status'] = 'failed'
        
        return results
    
    def execute_patch_command(self, server: str, os_type: str, user: str = None, 
                             port: int = None, dry_run: bool = False) -> Dict[str, Any]:
        """Execute patching command based on OS type"""
        commands = {
            'ubuntu': {
                'update': 'sudo apt-get update',
                'upgrade': 'sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y',
                'dry_run': 'sudo apt list --upgradable',
                'autoremove': 'sudo apt-get autoremove -y',
                'clean': 'sudo apt-get clean'
            },
            'debian': {
                'update': 'sudo apt-get update',
                'upgrade': 'sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y',
                'dry_run': 'sudo apt list --upgradable',
                'autoremove': 'sudo apt-get autoremove -y',
                'clean': 'sudo apt-get clean'
            },
            'centos': {
                'update': 'sudo yum check-update || true',
                'upgrade': 'sudo yum update -y',
                'dry_run': 'sudo yum check-update',
                'clean': 'sudo yum clean all'
            },
            'rhel': {
                'update': 'sudo yum check-update || true',
                'upgrade': 'sudo yum update -y',
                'dry_run': 'sudo yum check-update',
                'clean': 'sudo yum clean all'
            },
            'fedora': {
                'update': 'sudo dnf check-update || true',
                'upgrade': 'sudo dnf update -y',
                'dry_run': 'sudo dnf check-update',
                'clean': 'sudo dnf clean all'
            }
        }
        
        os_type = os_type.lower()
        if os_type not in commands:
            return {
                'success': False,
                'error': f'Unsupported OS type: {os_type}',
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
        
        os_commands = commands[os_type]
        results = {
            'server': server,
            'os_type': os_type,
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'steps': []
        }
        
        if dry_run:
            # Only check for available updates
            result = self.execute_command(server, os_commands['dry_run'], user, port, timeout=600)
            results['steps'].append({
                'step': 'dry_run_check',
                'command': os_commands['dry_run'],
                'success': result['success'],
                'output': result['stdout'],
                'error': result['stderr']
            })
            results['success'] = result['success']
        else:
            # Execute full patching sequence
            steps = ['update', 'upgrade']
            if os_type in ['ubuntu', 'debian']:
                steps.extend(['autoremove', 'clean'])
            elif os_type in ['centos', 'rhel', 'fedora']:
                steps.append('clean')
            
            overall_success = True
            
            for step in steps:
                if step not in os_commands:
                    continue
                
                self.logger.info(f"Executing {step} on {server}")
                
                timeout = 3600 if step == 'upgrade' else 600
                result = self.execute_command(server, os_commands[step], user, port, timeout=timeout)
                
                step_result = {
                    'step': step,
                    'command': os_commands[step],
                    'success': result['success'],
                    'output': result['stdout'],
                    'error': result['stderr'],
                    'duration': 0  # Would need to track this
                }
                
                results['steps'].append(step_result)
                
                if not result['success'] and step in ['update', 'upgrade']:
                    overall_success = False
                    break
            
            results['success'] = overall_success
        
        return results
    
    def check_reboot_required(self, server: str, os_type: str, user: str = None, 
                             port: int = None) -> Dict[str, Any]:
        """Check if reboot is required after patching"""
        commands = {
            'ubuntu': '[ -f /var/run/reboot-required ] && echo "yes" || echo "no"',
            'debian': '[ -f /var/run/reboot-required ] && echo "yes" || echo "no"',
            'centos': 'needs-restarting -r > /dev/null 2>&1 && echo "no" || echo "yes"',
            'rhel': 'needs-restarting -r > /dev/null 2>&1 && echo "no" || echo "yes"',
            'fedora': 'needs-restarting -r > /dev/null 2>&1 && echo "no" || echo "yes"'
        }
        
        os_type = os_type.lower()
        if os_type not in commands:
            return {
                'success': False,
                'error': f'Unsupported OS type: {os_type}',
                'server': server,
                'timestamp': datetime.now().isoformat()
            }
        
        result = self.execute_command(server, commands[os_type], user, port, timeout=30)
        
        if result['success']:
            reboot_required = result['stdout'].strip() == 'yes'
            return {
                'success': True,
                'server': server,
                'os_type': os_type,
                'reboot_required': reboot_required,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'server': server,
                'os_type': os_type,
                'error': result['stderr'],
                'timestamp': datetime.now().isoformat()
            }
    
    def reboot_server(self, server: str, user: str = None, port: int = None,
                     wait_for_return: bool = True, timeout: int = 300) -> Dict[str, Any]:
        """Reboot server and optionally wait for it to come back"""
        try:
            # Issue reboot command
            self.logger.info(f"Rebooting server {server}")
            result = self.execute_command(server, 'sudo reboot', user, port, timeout=10)
            
            if not wait_for_return:
                return {
                    'success': True,
                    'server': server,
                    'reboot_initiated': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Wait for server to go down
            self.logger.info(f"Waiting for {server} to go down...")
            time.sleep(30)
            
            # Wait for server to come back up
            self.logger.info(f"Waiting for {server} to come back up...")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    # Remove old connection
                    conn_key = f"{user or self.default_user}@{server}:{port or self.default_port}"
                    if conn_key in self.connections:
                        self.connections[conn_key].close()
                        del self.connections[conn_key]
                    
                    # Test connection
                    test_result = self.test_connection(server, user, port)
                    if test_result['success']:
                        self.logger.info(f"Server {server} is back online")
                        return {
                            'success': True,
                            'server': server,
                            'reboot_initiated': True,
                            'reboot_completed': True,
                            'reboot_time': time.time() - start_time,
                            'timestamp': datetime.now().isoformat()
                        }
                except Exception:
                    pass
                
                time.sleep(10)
            
            # Timeout waiting for server to come back
            return {
                'success': False,
                'server': server,
                'reboot_initiated': True,
                'reboot_completed': False,
                'error': f'Server did not come back online within {timeout} seconds',
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'server': server,
                'reboot_initiated': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close_connection(self, server: str, user: str = None, port: int = None):
        """Close SSH connection to server"""
        user = user or self.default_user
        port = port or self.default_port
        conn_key = f"{user}@{server}:{port}"
        
        with self.connection_lock:
            if conn_key in self.connections:
                try:
                    self.connections[conn_key].close()
                    del self.connections[conn_key]
                    self.logger.debug(f"Closed connection to {conn_key}")
                except Exception as e:
                    self.logger.error(f"Error closing connection to {conn_key}: {e}")
    
    def close_all_connections(self):
        """Close all SSH connections"""
        with self.connection_lock:
            for conn_key, client in list(self.connections.items()):
                try:
                    client.close()
                    self.logger.debug(f"Closed connection to {conn_key}")
                except Exception as e:
                    self.logger.error(f"Error closing connection to {conn_key}: {e}")
            
            self.connections.clear()
    
    def __del__(self):
        """Cleanup connections on object destruction"""
        self.close_all_connections()

# Utility functions
def create_ssh_handler(**kwargs) -> SSHHandler:
    """Create SSH handler with configuration"""
    return SSHHandler(**kwargs)

def test_ssh_connectivity(servers: List[str], user: str = None, 
                         parallel: bool = True) -> Dict[str, Dict[str, Any]]:
    """Test SSH connectivity to multiple servers"""
    ssh_handler = SSHHandler()
    results = {}
    
    if parallel:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_server = {
                executor.submit(ssh_handler.test_connection, server, user): server
                for server in servers
            }
            
            for future in concurrent.futures.as_completed(future_to_server):
                server = future_to_server[future]
                try:
                    results[server] = future.result()
                except Exception as e:
                    results[server] = {
                        'success': False,
                        'server': server,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
    else:
        for server in servers:
            results[server] = ssh_handler.test_connection(server, user)
    
    return results

# Example usage
if __name__ == "__main__":
    # Example of using the SSH handler
    ssh_handler = SSHHandler()
    
    # Test connection
    result = ssh_handler.test_connection('localhost')
    print(f"Connection test: {result}")
    
    # Get system info
    if result['success']:
        info = ssh_handler.get_system_info('localhost')
        print(f"System info: {json.dumps(info, indent=2)}")
    
    # Check prerequisites
    prereqs = ssh_handler.check_patch_prerequisites('localhost')
    print(f"Prerequisites: {json.dumps(prereqs, indent=2)}")
    
    # Close connections
    ssh_handler.close_all_connections()