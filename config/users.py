# config/users.py
"""
User management and role-based access control with LDAP integration
"""

import os
from typing import Optional, Dict, List
from utils.nslcd_ldap_auth import NSLCDLDAPAuthenticator
from utils.logger import Logger
from config.settings import Config

class UserManager:
    # Initialize LDAP authenticator and logger
    def __init__(self):
        self.nslcd_auth = NSLCDLDAPAuthenticator()
        self.logger = Logger('user_manager')
        self.fallback_enabled = getattr(Config, 'ENABLE_FALLBACK_AUTH', True)
    
    # Define user roles and their permissions
    ROLES = {
        'admin': {
            'name': 'Administrator',
            'permissions': [
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
            ]
        },
        'user': {
            'name': 'Server Owner',
            'permissions': [
                'view_owned_servers',
                'modify_owned_schedules',
                'approve_owned_schedules',
                'view_reports'
            ]
        },
        'readonly': {
            'name': 'Read Only User',
            'permissions': [
                'view_owned_servers',
                'view_reports'
            ]
        }
    }
    
    # DEMO/FALLBACK USERS ONLY - Not used when LDAP is enabled
    # In production, ALL authentication is via LDAP/nslcd netgroups
    # These users are ONLY for:
    # 1. Initial setup before LDAP is configured
    # 2. Demo/testing environments
    # 3. Emergency fallback if LDAP is down (when ENABLE_FALLBACK_AUTH=true)
    USERS = {
        # PRIMARY ADMIN - For initial setup and emergency access
        'patchadmin': {
            'password': 'admin123',  # Default password - CHANGE AFTER SETUP
            'role': 'admin', 
            'name': 'Patch Administrator',
            'active': True
        },
        # LEGACY DEMO ADMIN - For backward compatibility
        'admin': {
            'password': 'admin',  # Simple demo password
            'role': 'admin', 
            'name': 'Demo Admin',
            'active': True
        },
        # Example server owner accounts (demo only)
        'dba@company.com': {
            'password': 'demo123',
            'role': 'user',
            'name': 'Database Administrator',
            'active': True
        },
        'dev@company.com': {
            'password': 'demo123',
            'role': 'user',
            'name': 'Development Team',
            'active': True
        },
        'ops@company.com': {
            'password': 'demo123',
            'role': 'user',
            'name': 'Operations Team',
            'active': True
        },
        'backup@company.com': {
            'password': 'demo123',
            'role': 'user',
            'name': 'Backup Team',
            'active': True
        },
        
        # Additional demo users
        'user1': {
            'password': 'demo123',
            'role': 'user',
            'name': 'Demo User 1',
            'active': True
        },
        'readonly': {
            'password': 'demo123',
            'role': 'readonly',
            'name': 'Read Only User',
            'active': True
        }
    }
    
    def authenticate_user(self, username_or_email, password):
        """
        Authenticate user credentials via LDAP first, then fallback to local users
        """
        # Extract username from email if needed
        username = username_or_email.split('@')[0] if '@' in username_or_email else username_or_email
        
        # Try NSLCD LDAP authentication first
        if Config.LDAP_ENABLED:
            try:
                nslcd_user = self.nslcd_auth.authenticate_user(username, password)
                if nslcd_user:
                    self.logger.info(f"NSLCD LDAP authentication successful for user: {username}")
                    return {
                        'email': nslcd_user['email'],
                        'username': nslcd_user['username'],
                        'role': nslcd_user['role'],
                        'name': nslcd_user['name'],
                        'permissions': nslcd_user['permissions'],
                        'auth_method': 'nslcd_ldap',
                        'uid': nslcd_user.get('uid'),
                        'gid': nslcd_user.get('gid'),
                        'home': nslcd_user.get('home'),
                        'shell': nslcd_user.get('shell'),
                        'groups': nslcd_user.get('groups', [])
                    }
            except Exception as e:
                self.logger.error(f"NSLCD LDAP authentication error for {username}: {e}")
        
        # Fallback to local authentication for demo/testing
        if self.fallback_enabled:
            return self._authenticate_local_user(username_or_email, password)
        
        self.logger.warning(f"Authentication failed for user: {username}")
        return None
    
    def _authenticate_local_user(self, email_or_username, password):
        """Authenticate against local user database (fallback)"""
        user_data = self.USERS.get(email_or_username)
        if user_data and user_data['active'] and user_data['password'] == password:
            self.logger.info(f"Local authentication successful for user: {email_or_username}")
            return {
                'email': email_or_username,
                'username': email_or_username.split('@')[0] if '@' in email_or_username else email_or_username,
                'role': user_data['role'],
                'name': user_data['name'],
                'permissions': self.ROLES[user_data['role']]['permissions'],
                'auth_method': 'local'
            }
        return None
    
    # Keep the old class method for backward compatibility
    @classmethod
    def authenticate_user_legacy(cls, email, password):
        """Legacy authentication method - kept for backward compatibility"""
        user_data = cls.USERS.get(email)
        if user_data and user_data['active'] and user_data['password'] == password:
            return {
                'email': email,
                'role': user_data['role'],
                'name': user_data['name'],
                'permissions': cls.ROLES[user_data['role']]['permissions']
            }
        return None
    
    @classmethod
    def get_user_role(cls, email):
        """Get user role"""
        user_data = cls.USERS.get(email)
        return user_data['role'] if user_data else None
    
    @classmethod
    def has_permission(cls, email, permission):
        """Check if user has specific permission"""
        user_data = cls.USERS.get(email)
        if not user_data or not user_data['active']:
            return False
        
        role = user_data['role']
        return permission in cls.ROLES[role]['permissions']
    
    @classmethod
    def is_admin(cls, email):
        """Check if user is admin"""
        return cls.has_permission(email, 'system_admin')
    
    @classmethod
    def can_modify_incident_tickets(cls, email):
        """Check if user can modify incident tickets"""
        return cls.has_permission(email, 'update_incident_tickets')
    
    @classmethod
    def can_modify_patcher_emails(cls, email):
        """Check if user can modify patcher emails"""
        return cls.has_permission(email, 'update_patcher_emails')
    
    @classmethod
    def can_approve_schedules(cls, email, server_owner_email=None):
        """Check if user can approve schedules"""
        # Admins can approve all schedules
        if cls.has_permission(email, 'approve_all_schedules'):
            return True
        
        # Regular users can only approve their own servers
        if cls.has_permission(email, 'approve_owned_schedules'):
            return server_owner_email == email if server_owner_email else True
        
        return False
    
    @classmethod
    def can_modify_schedules(cls, email, server_owner_email=None):
        """Check if user can modify schedules"""
        # Admins can modify all schedules
        if cls.has_permission(email, 'modify_all_schedules'):
            return True
        
        # Regular users can only modify their own servers
        if cls.has_permission(email, 'modify_owned_schedules'):
            return server_owner_email == email if server_owner_email else True
        
        return False
    
    def get_user_info(self, email_or_username):
        """Get user information from LDAP or local database"""
        username = email_or_username.split('@')[0] if '@' in email_or_username else email_or_username
        
        # Try NSLCD LDAP first
        if Config.LDAP_ENABLED:
            try:
                # Get user info from system (using username for nslcd lookup)
                nslcd_user = self.nslcd_auth._get_user_info_from_system(username)
                if nslcd_user:
                    # Determine role based on netgroup membership and server ownership
                    role = self.nslcd_auth._determine_user_role(username, nslcd_user)
                    permissions = self.nslcd_auth._get_user_permissions(username, role)
                    
                    return {
                        'email': nslcd_user['email'],
                        'username': nslcd_user['username'],
                        'name': nslcd_user['full_name'],
                        'role': role,
                        'role_name': self.ROLES[role]['name'],
                        'permissions': permissions,
                        'active': True,
                        'auth_method': 'nslcd_ldap',
                        'uid': nslcd_user.get('uid'),
                        'gid': nslcd_user.get('gid'),
                        'home': nslcd_user.get('home'),
                        'shell': nslcd_user.get('shell'),
                        'groups': nslcd_user.get('groups', [])
                    }
            except Exception as e:
                self.logger.error(f"Error getting NSLCD LDAP user info for {username}: {e}")
        
        # Fallback to local database
        if self.fallback_enabled:
            user_data = self.USERS.get(email_or_username)
            if user_data:
                return {
                    'email': email_or_username,
                    'username': email_or_username.split('@')[0] if '@' in email_or_username else email_or_username,
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'role_name': self.ROLES[user_data['role']]['name'],
                    'permissions': self.ROLES[user_data['role']]['permissions'],
                    'active': user_data['active'],
                    'auth_method': 'local'
                }
        
        return None
    
    def get_user_servers(self, email_or_username, role=None):
        """Get servers that the user can access based on ownership"""
        username = email_or_username.split('@')[0] if '@' in email_or_username else email_or_username
        
        if not role:
            user_info = self.get_user_info(email_or_username)
            role = user_info['role'] if user_info else 'readonly'
        
        if Config.LDAP_ENABLED:
            try:
                return self.nslcd_auth.get_user_servers(username, role)
            except Exception as e:
                self.logger.error(f"Error getting servers for {username}: {e}")
        
        # Fallback to CSV-based server lookup
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
                
                # Check both linux_user fields and fallback to email fields for backward compatibility
                primary_owner = server.get('primary_owner', '')
                secondary_owner = server.get('secondary_owner', '')
                
                if (primary_linux_user == username or secondary_linux_user == username or
                    primary_owner == username or primary_owner == email_or_username or
                    secondary_owner == username or secondary_owner == email_or_username):
                    user_servers.append(server)
            
            return user_servers
            
        except Exception as e:
            self.logger.error(f"Error getting servers for {username}: {e}")
            return []
    
    # Legacy class method - kept for backward compatibility
    @classmethod
    def get_user_info_legacy(cls, email):
        """Get user information (legacy method)"""
        user_data = cls.USERS.get(email)
        if user_data:
            return {
                'email': email,
                'name': user_data['name'],
                'role': user_data['role'],
                'role_name': cls.ROLES[user_data['role']]['name'],
                'permissions': cls.ROLES[user_data['role']]['permissions'],
                'active': user_data['active']
            }
        return None
    
    @classmethod
    def get_all_users(cls):
        """Get all users (admin only)"""
        return [
            {
                'email': email,
                'name': data['name'],
                'role': data['role'],
                'role_name': cls.ROLES[data['role']]['name'],
                'active': data['active']
            }
            for email, data in cls.USERS.items()
        ]