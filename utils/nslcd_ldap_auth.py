# utils/nslcd_ldap_auth.py
import pwd
import grp
import subprocess
import os
import logging
from typing import Optional, Dict, List, Tuple
from utils.logger import Logger

class NSLCDLDAPAuthenticator:
    """
    LDAP authentication using existing nslcd.conf configuration
    Uses system's configured LDAP via nslcd for authentication
    """
    
    def __init__(self):
        self.logger = Logger('nslcd_ldap_auth')
        self.admin_netgroup = os.getenv('ADMIN_NETGROUP', 'patching_admins')
        self.nslcd_available = self._check_nslcd_availability()
        
    def _check_nslcd_availability(self) -> bool:
        """Check if nslcd service is available and running"""
        try:
            # Check if nslcd is running
            result = subprocess.run(
                ['systemctl', 'is-active', 'nslcd'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip() == 'active':
                self.logger.info("NSLCD service is active")
                return True
            else:
                self.logger.warning(f"NSLCD service status: {result.stdout.strip()}")
                
                # Also check nscd if nslcd is not active
                result = subprocess.run(
                    ['systemctl', 'is-active', 'nscd'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    self.logger.info("NSCD service is active (alternative caching)")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking nslcd availability: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user using system LDAP (nslcd configuration)
        """
        if not username or not password:
            return None
            
        try:
            # Use su command to test authentication (works with nslcd/sssd)
            # This leverages the system's PAM configuration
            auth_success = self._test_user_authentication(username, password)
            
            if not auth_success:
                self.logger.warning(f"Authentication failed for user: {username}")
                return None
            
            # Get user information from system (via nslcd/getent)
            user_info = self._get_user_info_from_system(username)
            if not user_info:
                self.logger.error(f"Could not retrieve user info for: {username}")
                return None
            
            # Determine user role based on netgroup membership and server ownership
            role = self._determine_user_role(username, user_info)
            
            # Get user permissions based on role
            permissions = self._get_user_permissions(username, role)
            
            return {
                'username': username,
                'email': user_info.get('email', f"{username}@{self._get_domain()}"),
                'name': user_info.get('full_name', username),
                'role': role,
                'permissions': permissions,
                'uid': user_info.get('uid'),
                'gid': user_info.get('gid'),
                'home': user_info.get('home'),
                'shell': user_info.get('shell'),
                'groups': user_info.get('groups', []),
                'active': True,
                'auth_method': 'nslcd_ldap'
            }
            
        except Exception as e:
            self.logger.error(f"Error during authentication for {username}: {e}")
            return None
    
    def _test_user_authentication(self, username: str, password: str) -> bool:
        """
        Test user authentication using su command
        This works with PAM and respects nslcd configuration
        """
        try:
            # Create a simple test command that the user can execute
            test_cmd = "echo 'auth_test'"
            
            # Use su to test authentication
            process = subprocess.Popen(
                ['su', '-', username, '-c', test_cmd],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send password to su command
            stdout, stderr = process.communicate(input=password + '\n', timeout=10)
            
            # Check if authentication succeeded
            if process.returncode == 0 and 'auth_test' in stdout:
                self.logger.info(f"Authentication successful for user: {username}")
                return True
            else:
                self.logger.warning(f"Authentication failed for user: {username}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Authentication timeout for user: {username}")
            return False
        except Exception as e:
            self.logger.error(f"Error testing authentication for {username}: {e}")
            return False
    
    def _get_user_info_from_system(self, username: str) -> Optional[Dict]:
        """
        Get user information from system using getent (works with nslcd)
        """
        try:
            # Get user info using pwd module (works with nslcd)
            user_pwd = pwd.getpwnam(username)
            
            user_info = {
                'username': username,
                'uid': user_pwd.pw_uid,
                'gid': user_pwd.pw_gid,
                'full_name': user_pwd.pw_gecos.split(',')[0] if user_pwd.pw_gecos else username,
                'home': user_pwd.pw_dir,
                'shell': user_pwd.pw_shell
            }
            
            # Try to get email from GECOS field or construct it
            gecos_parts = user_pwd.pw_gecos.split(',')
            email = None
            
            # Look for email in GECOS field
            for part in gecos_parts:
                if '@' in part:
                    email = part.strip()
                    break
            
            if not email:
                # Construct email from username and domain
                email = f"{username}@{self._get_domain()}"
            
            user_info['email'] = email
            
            # Get user's groups
            groups = self._get_user_groups(username)
            user_info['groups'] = groups
            
            self.logger.debug(f"Retrieved user info for {username}: {user_info}")
            return user_info
            
        except KeyError:
            self.logger.error(f"User {username} not found in system")
            return None
        except Exception as e:
            self.logger.error(f"Error getting user info for {username}: {e}")
            return None
    
    def _get_user_groups(self, username: str) -> List[str]:
        """Get list of groups the user belongs to"""
        try:
            groups = []
            
            # Get all groups and check membership
            for group in grp.getgrall():
                if username in group.gr_mem:
                    groups.append(group.gr_name)
                # Also check if user's primary group
                try:
                    user_pwd = pwd.getpwnam(username)
                    if group.gr_gid == user_pwd.pw_gid:
                        groups.append(group.gr_name)
                except:
                    pass
            
            return list(set(groups))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error getting groups for {username}: {e}")
            return []
    
    def _determine_user_role(self, username: str, user_info: Dict) -> str:
        """
        Determine user role based on netgroup membership and server ownership
        """
        try:
            # Check if user is in admin netgroup
            if self._is_user_in_netgroup(username, self.admin_netgroup):
                self.logger.info(f"User {username} is admin (member of {self.admin_netgroup})")
                return 'admin'
            
            # Check if user owns any servers in the database
            if self._user_owns_servers(username):
                self.logger.info(f"User {username} is server owner")
                return 'user'
            
            # Default to readonly
            self.logger.info(f"User {username} has readonly access")
            return 'readonly'
            
        except Exception as e:
            self.logger.error(f"Error determining role for {username}: {e}")
            return 'readonly'
    
    def _is_user_in_netgroup(self, username: str, netgroup: str) -> bool:
        """
        Check if user is member of a Linux netgroup
        """
        try:
            # Method 1: Use getent command
            result = subprocess.run(
                ['getent', 'netgroup', netgroup],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Look for username in the netgroup entries
                if f",{username}," in output or f"({username}," in output or f" {username} " in output:
                    return True
            
            # Method 2: Use innetgr command if available
            result = subprocess.run(
                ['innetgr', netgroup, '-', username, '-'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True
            
            # Method 3: Check /etc/netgroup file directly
            try:
                with open('/etc/netgroup', 'r') as f:
                    for line in f:
                        if line.startswith(netgroup):
                            if f",{username}," in line or f"({username}," in line or f" {username} " in line:
                                return True
            except FileNotFoundError:
                pass
            
            return False
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Timeout checking netgroup {netgroup} for user {username}")
            return False
        except Exception as e:
            self.logger.error(f"Error checking netgroup membership for {username}: {e}")
            return False
    
    def _user_owns_servers(self, username: str) -> bool:
        """
        Check if user owns any servers in the database (using linux_user fields)
        """
        try:
            from utils.csv_handler import CSVHandler
            csv_handler = CSVHandler()
            servers = csv_handler.read_servers()
            
            for server in servers:
                primary_linux_user = server.get('primary_linux_user', '')
                secondary_linux_user = server.get('secondary_linux_user', '')
                
                if (primary_linux_user == username or secondary_linux_user == username):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking server ownership for {username}: {e}")
            return False
    
    def _get_user_permissions(self, username: str, role: str) -> List[str]:
        """
        Get user permissions based on role
        """
        base_permissions = {
            'admin': [
                'view_all_servers',
                'modify_all_schedules', 
                'approve_all_schedules',
                'update_incident_tickets',
                'update_patcher_emails',
                'manage_users',
                'send_notifications',
                'export_data',
                'system_admin',
                'manage_netgroups',
                'nslcd_admin'
            ],
            'user': [
                'view_owned_servers',
                'modify_owned_schedules',
                'approve_owned_schedules',
                'view_reports'
            ],
            'readonly': [
                'view_owned_servers',
                'view_reports'
            ]
        }
        
        return base_permissions.get(role, base_permissions['readonly'])
    
    def _get_domain(self) -> str:
        """
        Get domain from system configuration
        """
        try:
            # Try to get domain from hostname
            result = subprocess.run(
                ['hostname', '-d'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            # Fallback: try to get from /etc/resolv.conf
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('domain '):
                            return line.split()[1]
                        elif line.startswith('search '):
                            return line.split()[1]
            except:
                pass
            
            # Default fallback
            return 'company.com'
            
        except Exception as e:
            self.logger.error(f"Error getting domain: {e}")
            return 'company.com'
    
    def get_user_servers(self, username: str, role: str) -> List[Dict]:
        """
        Get servers that the user has access to based on linux_user ownership
        """
        try:
            from utils.csv_handler import CSVHandler
            csv_handler = CSVHandler()
            all_servers = csv_handler.read_servers()
            
            if role == 'admin':
                return all_servers
            
            # For regular users, return only owned servers (using linux_user fields)
            user_servers = []
            
            for server in all_servers:
                primary_linux_user = server.get('primary_linux_user', '')
                secondary_linux_user = server.get('secondary_linux_user', '')
                
                if (primary_linux_user == username or secondary_linux_user == username):
                    user_servers.append(server)
            
            return user_servers
            
        except Exception as e:
            self.logger.error(f"Error getting servers for {username}: {e}")
            return []
    
    def validate_nslcd_connection(self) -> Tuple[bool, str]:
        """
        Test NSLCD configuration and connectivity
        """
        try:
            # Check if nslcd service is running
            if not self.nslcd_available:
                return False, "NSLCD service is not available or not running"
            
            # Test user lookup via getent (which uses nslcd)
            result = subprocess.run(
                ['getent', 'passwd'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Count lines to see if we have LDAP users
                passwd_lines = result.stdout.strip().split('\n')
                if len(passwd_lines) > 50:  # Likely includes LDAP users
                    return True, f"NSLCD working - found {len(passwd_lines)} users"
                else:
                    return True, "NSLCD working but may have limited user data"
            else:
                return False, "getent passwd failed"
                
        except Exception as e:
            return False, f"NSLCD validation error: {str(e)}"
    
    def get_system_auth_info(self) -> Dict:
        """
        Get information about system authentication configuration
        """
        try:
            info = {
                'nslcd_available': self.nslcd_available,
                'admin_netgroup': self.admin_netgroup,
                'domain': self._get_domain()
            }
            
            # Check nsswitch.conf configuration
            try:
                with open('/etc/nsswitch.conf', 'r') as f:
                    content = f.read()
                    info['nsswitch_passwd'] = 'ldap' in content and 'passwd:' in content
                    info['nsswitch_group'] = 'ldap' in content and 'group:' in content
                    info['nsswitch_netgroup'] = 'ldap' in content and 'netgroup:' in content
            except:
                info['nsswitch_error'] = 'Could not read /etc/nsswitch.conf'
            
            # Check if nslcd.conf exists
            info['nslcd_conf_exists'] = os.path.exists('/etc/nslcd.conf')
            
            # Get service status
            try:
                result = subprocess.run(
                    ['systemctl', 'status', 'nslcd'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                info['nslcd_status'] = 'active' if result.returncode == 0 else 'inactive'
            except:
                info['nslcd_status'] = 'unknown'
            
            return info
            
        except Exception as e:
            return {'error': str(e)}