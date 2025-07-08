# utils/ssh_manager.py
"""
SSH Manager for remote server operations
Handles SSH connections, file operations, and command execution on remote servers
"""

import paramiko
import socket
import time
from typing import Optional, Tuple, List, Dict
from config.settings import Config
from utils.logger import Logger

class SSHManager:
    def __init__(self):
        self.logger = Logger('ssh_manager')
        self.config = Config()
        
    def _create_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client
    
    def _get_ssh_connection(self, hostname: str, username: str = None, port: int = 22) -> Tuple[bool, Optional[paramiko.SSHClient], str]:
        """
        Establish SSH connection to a server
        Returns: (success, ssh_client, error_message)
        """
        client = self._create_ssh_client()
        
        try:
            # Use patchadmin user by default
            if not username:
                username = 'patchadmin'
            
            # Try key-based authentication first
            private_key_path = f"{Config.PROJECT_ROOT}/.ssh/id_rsa"
            
            client.connect(
                hostname=hostname,
                port=port,
                username=username,
                key_filename=private_key_path,
                timeout=self.config.SSH_CONNECTION_TIMEOUT,
                banner_timeout=30
            )
            
            self.logger.info(f"SSH connection established to {hostname}")
            return True, client, ""
            
        except paramiko.AuthenticationException:
            try:
                # Fallback: try password authentication (if configured)
                client.connect(
                    hostname=hostname,
                    port=port,
                    username=username,
                    password=None,  # Would need to be configured
                    timeout=self.config.SSH_CONNECTION_TIMEOUT,
                    banner_timeout=30
                )
                return True, client, ""
            except Exception as e:
                error_msg = f"Authentication failed for {hostname}: {str(e)}"
                self.logger.error(error_msg)
                return False, None, error_msg
                
        except socket.timeout:
            error_msg = f"Connection timeout to {hostname}"
            self.logger.error(error_msg)
            return False, None, error_msg
            
        except socket.gaierror as e:
            error_msg = f"DNS resolution failed for {hostname}: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"SSH connection failed to {hostname}: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
    
    def test_connection(self, hostname: str, username: str = None, port: int = 22) -> bool:
        """Test SSH connection to a server"""
        success, client, error = self._get_ssh_connection(hostname, username, port)
        
        if success and client:
            try:
                # Test with a simple command
                stdin, stdout, stderr = client.exec_command('echo "connection_test"', timeout=10)
                result = stdout.read().decode().strip()
                
                if result == "connection_test":
                    self.logger.info(f"SSH connection test successful for {hostname}")
                    return True
                else:
                    self.logger.error(f"SSH command test failed for {hostname}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"SSH command execution failed for {hostname}: {str(e)}")
                return False
            finally:
                client.close()
        
        return False
    
    def execute_command(self, hostname: str, command: str, username: str = None, timeout: int = None) -> Tuple[bool, str, str]:
        """
        Execute a command on remote server
        Returns: (success, stdout, stderr)
        """
        if timeout is None:
            timeout = self.config.SSH_COMMAND_TIMEOUT
            
        success, client, error = self._get_ssh_connection(hostname, username)
        
        if not success:
            return False, "", error
        
        try:
            self.logger.info(f"Executing command on {hostname}: {command}")
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            stdout_data = stdout.read().decode()
            stderr_data = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.logger.info(f"Command executed successfully on {hostname}")
                return True, stdout_data, stderr_data
            else:
                self.logger.error(f"Command failed on {hostname} with exit status {exit_status}")
                return False, stdout_data, stderr_data
                
        except socket.timeout:
            error_msg = f"Command timeout on {hostname}"
            self.logger.error(error_msg)
            return False, "", error_msg
            
        except Exception as e:
            error_msg = f"Command execution failed on {hostname}: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg
            
        finally:
            client.close()
    
    def check_file_exists(self, hostname: str, file_path: str, username: str = None) -> bool:
        """Check if a file exists on remote server"""
        command = f"test -f '{file_path}' && echo 'exists' || echo 'not_found'"
        success, stdout, stderr = self.execute_command(hostname, command, username, timeout=30)
        
        if success and stdout.strip() == 'exists':
            self.logger.info(f"File {file_path} exists on {hostname}")
            return True
        else:
            self.logger.warning(f"File {file_path} not found on {hostname}")
            return False
    
    def check_file_executable(self, hostname: str, file_path: str, username: str = None) -> bool:
        """Check if a file is executable on remote server"""
        command = f"test -x '{file_path}' && echo 'executable' || echo 'not_executable'"
        success, stdout, stderr = self.execute_command(hostname, command, username, timeout=30)
        
        if success and stdout.strip() == 'executable':
            self.logger.info(f"File {file_path} is executable on {hostname}")
            return True
        else:
            self.logger.warning(f"File {file_path} is not executable on {hostname}")
            return False
    
    def execute_patching_script(self, hostname: str, script_args: str = "", username: str = None) -> Tuple[bool, str, str]:
        """
        Execute the configured patching script on remote server
        Returns: (success, stdout, stderr)
        """
        script_path = self.config.PATCHING_SCRIPT_PATH
        
        # Validate script exists if validation is enabled
        if self.config.VALIDATE_PATCHING_SCRIPT:
            if not self.check_file_exists(hostname, script_path, username):
                error_msg = f"Patching script {script_path} not found on {hostname}"
                self.logger.error(error_msg)
                return False, "", error_msg
            
            if not self.check_file_executable(hostname, script_path, username):
                error_msg = f"Patching script {script_path} is not executable on {hostname}"
                self.logger.error(error_msg)
                return False, "", error_msg
        
        # Construct command
        command = f"sudo {script_path}"
        if script_args:
            command += f" {script_args}"
        
        self.logger.info(f"Executing patching script on {hostname}: {command}")
        
        # Execute with extended timeout for patching operations
        return self.execute_command(hostname, command, username, timeout=1800)  # 30 minutes
    
    def get_system_info(self, hostname: str, username: str = None) -> Dict[str, str]:
        """Get basic system information from remote server"""
        info = {}
        
        commands = {
            'hostname': 'hostname',
            'os_release': 'cat /etc/os-release | head -1',
            'kernel': 'uname -r',
            'uptime': 'uptime -p',
            'disk_usage': 'df -h /',
            'memory': 'free -h | head -2 | tail -1',
            'load_average': 'uptime | awk -F\'load average:\' \'{print $2}\''
        }
        
        for key, command in commands.items():
            success, stdout, stderr = self.execute_command(hostname, command, username, timeout=30)
            if success:
                info[key] = stdout.strip()
            else:
                info[key] = f"Error: {stderr.strip()}"
        
        return info
    
    def validate_patching_prerequisites(self, hostname: str, username: str = None) -> Tuple[bool, List[str]]:
        """
        Validate that a server meets patching prerequisites
        Returns: (success, list_of_issues)
        """
        issues = []
        
        # Check script exists and is executable
        if self.config.VALIDATE_PATCHING_SCRIPT:
            if not self.check_file_exists(hostname, self.config.PATCHING_SCRIPT_PATH, username):
                issues.append(f"Patching script {self.config.PATCHING_SCRIPT_PATH} not found")
            elif not self.check_file_executable(hostname, self.config.PATCHING_SCRIPT_PATH, username):
                issues.append(f"Patching script {self.config.PATCHING_SCRIPT_PATH} is not executable")
        
        # Check disk space
        success, stdout, stderr = self.execute_command(hostname, "df / | tail -1 | awk '{print $5}' | sed 's/%//'", username, timeout=30)
        if success:
            try:
                disk_usage = int(stdout.strip())
                if disk_usage > 90:
                    issues.append(f"Root filesystem is {disk_usage}% full")
            except ValueError:
                issues.append("Could not determine disk usage")
        else:
            issues.append("Could not check disk space")
        
        # Check if system is accessible
        if not self.test_connection(hostname, username):
            issues.append("SSH connection test failed")
        
        return len(issues) == 0, issues
    
    def batch_command_execution(self, servers: List[str], command: str, username: str = None, max_concurrent: int = 5) -> Dict[str, Tuple[bool, str, str]]:
        """
        Execute command on multiple servers concurrently
        Returns: {hostname: (success, stdout, stderr)}
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        
        def execute_on_server(hostname):
            return hostname, self.execute_command(hostname, command, username)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_server = {executor.submit(execute_on_server, server): server for server in servers}
            
            for future in as_completed(future_to_server):
                hostname, result = future.result()
                results[hostname] = result
        
        return results