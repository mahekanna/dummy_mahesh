# utils/ldap_auth.py
import subprocess
import os
import logging
from typing import Optional, Dict, List, Tuple

# Optional LDAP import
try:
    import ldap3
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False
    # Create a dummy ldap3 module for graceful fallback
    class ldap3:
        class Server:
            def __init__(self, *args, **kwargs):
                pass
        class Connection:
            def __init__(self, *args, **kwargs):
                pass
            def bind(self):
                return False
            def unbind(self):
                pass
            def search(self, *args, **kwargs):
                pass
            @property
            def entries(self):
                return []
        SUBTREE = 'SUBTREE'
        ALL = 'ALL'
        class core:
            class exceptions:
                class LDAPException(Exception):
                    pass

from config.settings import Config
from utils.logger import Logger

class LDAPAuthenticator:
    def __init__(self):
        self.logger = Logger('ldap_auth')
        self.ldap_enabled = Config.LDAP_ENABLED and LDAP_AVAILABLE
        self.ldap_server = Config.LDAP_SERVER
        self.ldap_base_dn = Config.LDAP_BASE_DN
        self.ldap_bind_dn = Config.LDAP_BIND_DN
        self.ldap_bind_password = Config.LDAP_BIND_PASSWORD
        self.admin_netgroup = getattr(Config, 'ADMIN_NETGROUP', 'patching_admins')
        
        if Config.LDAP_ENABLED and not LDAP_AVAILABLE:
            self.logger.warning("LDAP is enabled in config but ldap3 module is not available. Install python3-ldap3 or use pip install ldap3.")
        
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate user via LDAP and determine permissions
        Returns user info dict or None if authentication fails
        """
        if not self.ldap_enabled:
            self.logger.warning("LDAP authentication is disabled")
            return None
            
        try:
            # Connect to LDAP server
            server = ldap3.Server(self.ldap_server, get_info=ldap3.ALL)
            
            # Try to bind with user credentials
            user_dn = f"uid={username},{self.ldap_base_dn}"
            connection = ldap3.Connection(server, user_dn, password, auto_bind=True)
            
            if not connection.bind():
                self.logger.warning(f"LDAP authentication failed for user: {username}")
                return None
            
            # Get user information from LDAP
            user_info = self._get_user_info(connection, username)
            connection.unbind()
            
            if not user_info:
                self.logger.error(f"Could not retrieve user info for: {username}")
                return None
            
            # Determine user role based on netgroup membership
            role = self._determine_user_role(username, user_info)
            
            # Get user permissions based on server ownership
            permissions = self._get_user_permissions(username, role)
            
            return {
                'username': username,
                'email': user_info.get('mail', f"{username}@{self._get_domain()}"),
                'name': user_info.get('cn', username),
                'role': role,
                'permissions': permissions,
                'ldap_groups': user_info.get('memberOf', []),
                'department': user_info.get('department', ''),
                'title': user_info.get('title', ''),
                'phone': user_info.get('telephoneNumber', ''),
                'active': True
            }
            
        except ldap3.core.exceptions.LDAPException as e:
            self.logger.error(f"LDAP error during authentication for {username}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during LDAP authentication for {username}: {e}")
            return None
    
    def _get_user_info(self, connection: ldap3.Connection, username: str) -> Optional[Dict]:
        """Get user information from LDAP"""
        try:
            search_filter = f"(uid={username})"
            search_attributes = [
                'cn', 'mail', 'uid', 'memberOf', 'department', 
                'title', 'telephoneNumber', 'employeeNumber', 
                'manager', 'description'
            ]
            
            connection.search(
                search_base=self.ldap_base_dn,
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                attributes=search_attributes
            )
            
            if not connection.entries:
                self.logger.warning(f"No LDAP entry found for user: {username}")
                return None
            
            entry = connection.entries[0]
            user_info = {}
            
            for attr in search_attributes:
                if hasattr(entry, attr):
                    value = getattr(entry, attr).value
                    if isinstance(value, list) and len(value) == 1:
                        user_info[attr] = value[0]
                    else:
                        user_info[attr] = value
            
            return user_info
            
        except Exception as e:
            self.logger.error(f"Error retrieving user info for {username}: {e}")
            return None
    
    def _determine_user_role(self, username: str, user_info: Dict) -> str:
        """
        Determine user role based on Linux netgroup membership
        """
        try:
            # Check if user is in admin netgroup
            if self._is_user_in_netgroup(username, self.admin_netgroup):
                self.logger.info(f"User {username} is admin (member of {self.admin_netgroup})")
                return 'admin'
            
            # Check additional admin criteria (LDAP groups)
            ldap_groups = user_info.get('memberOf', [])
            admin_ldap_groups = [
                'cn=sysadmins,ou=groups,dc=company,dc=com',
                'cn=patching_admins,ou=groups,dc=company,dc=com',
                'cn=infrastructure,ou=groups,dc=company,dc=com'
            ]
            
            for group in ldap_groups:
                if any(admin_group in str(group) for admin_group in admin_ldap_groups):
                    self.logger.info(f"User {username} is admin (member of LDAP group {group})")
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
        Check if user is member of a Linux netgroup using system commands
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
                # Parse netgroup output: netgroup_name (host,user,domain) (host,user,domain)
                output = result.stdout.strip()
                # Look for username in the netgroup entries
                if f",{username}," in output or f"({username}," in output:
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
                            if f",{username}," in line or f"({username}," in line:
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
        Check if user owns any servers in the database
        """
        try:
            from utils.csv_handler import CSVHandler
            csv_handler = CSVHandler()
            servers = csv_handler.read_servers()
            
            user_email = f"{username}@{self._get_domain()}"
            
            for server in servers:
                primary_owner = server.get('primary_owner', '')
                secondary_owner = server.get('secondary_owner', '')
                
                if (primary_owner == username or primary_owner == user_email or
                    secondary_owner == username or secondary_owner == user_email):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking server ownership for {username}: {e}")
            return False
    
    def _get_user_permissions(self, username: str, role: str) -> List[str]:
        """
        Get user permissions based on role and server ownership
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
                'ldap_admin'
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
        """Extract domain from LDAP base DN"""
        try:
            # Extract domain from base DN (e.g., dc=company,dc=com -> company.com)
            domain_parts = []
            for part in self.ldap_base_dn.split(','):
                if part.strip().startswith('dc='):
                    domain_parts.append(part.strip()[3:])
            return '.'.join(domain_parts) if domain_parts else 'company.com'
        except:
            return 'company.com'
    
    def get_user_servers(self, username: str, role: str) -> List[Dict]:
        """
        Get servers that the user has access to based on ownership
        """
        try:
            from utils.csv_handler import CSVHandler
            csv_handler = CSVHandler()
            all_servers = csv_handler.read_servers()
            
            if role == 'admin':
                return all_servers
            
            # For regular users, return only owned servers
            user_email = f"{username}@{self._get_domain()}"
            user_servers = []
            
            for server in all_servers:
                primary_owner = server.get('primary_owner', '')
                secondary_owner = server.get('secondary_owner', '')
                
                if (primary_owner == username or primary_owner == user_email or
                    secondary_owner == username or secondary_owner == user_email):
                    user_servers.append(server)
            
            return user_servers
            
        except Exception as e:
            self.logger.error(f"Error getting servers for {username}: {e}")
            return []
    
    def validate_ldap_connection(self) -> Tuple[bool, str]:
        """
        Test LDAP connection and configuration
        """
        if not self.ldap_enabled:
            return False, "LDAP authentication is disabled"
        
        try:
            server = ldap3.Server(self.ldap_server, get_info=ldap3.ALL)
            connection = ldap3.Connection(
                server, 
                self.ldap_bind_dn, 
                self.ldap_bind_password, 
                auto_bind=True
            )
            
            if connection.bind():
                connection.unbind()
                return True, "LDAP connection successful"
            else:
                return False, "LDAP bind failed"
                
        except Exception as e:
            return False, f"LDAP connection error: {str(e)}"
    
    def sync_user_from_ldap(self, username: str) -> Optional[Dict]:
        """
        Sync user information from LDAP without authentication
        Used for administrative purposes
        """
        if not self.ldap_enabled:
            return None
            
        try:
            server = ldap3.Server(self.ldap_server, get_info=ldap3.ALL)
            connection = ldap3.Connection(
                server,
                self.ldap_bind_dn,
                self.ldap_bind_password,
                auto_bind=True
            )
            
            user_info = self._get_user_info(connection, username)
            connection.unbind()
            
            if user_info:
                role = self._determine_user_role(username, user_info)
                permissions = self._get_user_permissions(username, role)
                
                return {
                    'username': username,
                    'email': user_info.get('mail', f"{username}@{self._get_domain()}"),
                    'name': user_info.get('cn', username),
                    'role': role,
                    'permissions': permissions,
                    'ldap_groups': user_info.get('memberOf', []),
                    'active': True
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error syncing user {username} from LDAP: {e}")
            return None