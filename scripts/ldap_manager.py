#!/usr/bin/env python3
"""
LDAP Integration Manager
Handles LDAP authentication, user synchronization, and group management
"""

import json
import os
import sys
import hashlib
import base64
from datetime import datetime
from utils.logger import Logger
from config.settings import Config

try:
    import ldap3
    LDAP_AVAILABLE = True
except ImportError:
    LDAP_AVAILABLE = False

class LDAPManager:
    def __init__(self):
        self.logger = Logger('ldap_manager')
        self.config_path = os.path.join(Config.CONFIG_DIR, 'admin_config.json')
        self.ldap_config = self._load_ldap_config()
        
    def _load_ldap_config(self):
        """Load LDAP configuration from admin config"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get('ldap_configuration', {})
        except FileNotFoundError:
            self.logger.warning("Admin config not found")
            return {}
    
    def _save_ldap_config(self, ldap_config):
        """Save LDAP configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            config['ldap_configuration'] = ldap_config
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            self.logger.info("LDAP configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save LDAP config: {e}")
            return False
    
    def is_ldap_enabled(self):
        """Check if LDAP is enabled and available"""
        return LDAP_AVAILABLE and self.ldap_config.get('enabled', False)
    
    def test_ldap_connection(self):
        """Test LDAP connection"""
        if not LDAP_AVAILABLE:
            return False, "LDAP library not available. Install with: pip install ldap3"
        
        if not self.ldap_config.get('enabled', False):
            return False, "LDAP is not enabled in configuration"
        
        try:
            server = ldap3.Server(self.ldap_config['server'], get_info=ldap3.ALL)
            conn = ldap3.Connection(
                server,
                user=self.ldap_config.get('bind_dn'),
                password=self._decrypt_password(self.ldap_config.get('bind_password_encrypted', '')),
                auto_bind=True
            )
            
            # Test a simple search
            base_dn = self.ldap_config['base_dn']
            conn.search(base_dn, '(objectClass=*)', search_scope=ldap3.BASE)
            
            conn.unbind()
            return True, "LDAP connection successful"
            
        except Exception as e:
            return False, f"LDAP connection failed: {str(e)}"
    
    def authenticate_user(self, username, password):
        """Authenticate user against LDAP"""
        if not self.is_ldap_enabled():
            return False, "LDAP authentication not available"
        
        try:
            # Build user DN
            user_search_base = self.ldap_config['user_search_base']
            user_dn = f"uid={username},{user_search_base}"
            
            # Try to bind with user credentials
            server = ldap3.Server(self.ldap_config['server'])
            conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)
            
            # Get user information
            user_info = self._get_user_info(conn, username)
            conn.unbind()
            
            return True, user_info
            
        except ldap3.core.exceptions.LDAPBindError:
            return False, "Invalid username or password"
        except Exception as e:
            self.logger.error(f"LDAP authentication error: {e}")
            return False, f"Authentication error: {str(e)}"
    
    def get_user_groups(self, username):
        """Get user's group memberships"""
        if not self.is_ldap_enabled():
            return []
        
        try:
            server = ldap3.Server(self.ldap_config['server'])
            conn = ldap3.Connection(
                server,
                user=self.ldap_config.get('bind_dn'),
                password=self._decrypt_password(self.ldap_config.get('bind_password_encrypted', '')),
                auto_bind=True
            )
            
            # Search for user's groups
            group_search_base = self.ldap_config['group_search_base']
            search_filter = f"(&(objectClass=groupOfNames)(member=uid={username},{self.ldap_config['user_search_base']}))"
            
            conn.search(group_search_base, search_filter, attributes=['cn'])
            
            groups = [entry.cn.value for entry in conn.entries]
            conn.unbind()
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Error getting user groups: {e}")
            return []
    
    def determine_user_role(self, username):
        """Determine user role based on LDAP groups"""
        if not self.is_ldap_enabled():
            return 'user'  # Default role
        
        user_groups = self.get_user_groups(username)
        admin_groups = self.ldap_config.get('admin_groups', [])
        user_groups_config = self.ldap_config.get('user_groups', [])
        
        # Check if user is admin
        if any(group in user_groups for group in admin_groups):
            return 'admin'
        
        # Check if user has user access
        if any(group in user_groups for group in user_groups_config):
            return 'user'
        
        # Default to readonly if no specific groups match
        return 'readonly'
    
    def sync_users_from_ldap(self):
        """Sync users from LDAP to local database"""
        if not self.is_ldap_enabled():
            return False, "LDAP not enabled"
        
        try:
            server = ldap3.Server(self.ldap_config['server'])
            conn = ldap3.Connection(
                server,
                user=self.ldap_config.get('bind_dn'),
                password=self._decrypt_password(self.ldap_config.get('bind_password_encrypted', '')),
                auto_bind=True
            )
            
            # Search for all users
            user_search_base = self.ldap_config['user_search_base']
            conn.search(user_search_base, '(objectClass=inetOrgPerson)', 
                       attributes=['uid', 'cn', 'mail', 'memberOf'])
            
            synced_users = []
            for entry in conn.entries:
                username = entry.uid.value
                full_name = entry.cn.value
                email = entry.mail.value if hasattr(entry, 'mail') else ''
                
                # Determine role
                role = self.determine_user_role(username)
                
                user_data = {
                    'username': username,
                    'full_name': full_name,
                    'email': email,
                    'role': role,
                    'last_sync': datetime.now().isoformat()
                }
                
                synced_users.append(user_data)
            
            conn.unbind()
            
            # Save synced users to a file (you could also save to database)
            sync_file = os.path.join(Config.DATA_DIR, 'ldap_users.json')
            with open(sync_file, 'w') as f:
                json.dump(synced_users, f, indent=4)
            
            self.logger.info(f"Synced {len(synced_users)} users from LDAP")
            return True, f"Synced {len(synced_users)} users"
            
        except Exception as e:
            self.logger.error(f"LDAP user sync failed: {e}")
            return False, f"Sync failed: {str(e)}"
    
    def update_ldap_config(self, new_config):
        """Update LDAP configuration"""
        try:
            # Encrypt password if provided
            if 'bind_password' in new_config:
                encrypted_password = self._encrypt_password(new_config['bind_password'])
                new_config['bind_password_encrypted'] = encrypted_password
                del new_config['bind_password']  # Remove plain text password
            
            # Update configuration
            self.ldap_config.update(new_config)
            
            # Save to file
            success = self._save_ldap_config(self.ldap_config)
            
            if success:
                self.logger.info("LDAP configuration updated successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update LDAP config: {e}")
            return False
    
    def _get_user_info(self, conn, username):
        """Get detailed user information"""
        try:
            user_search_base = self.ldap_config['user_search_base']
            search_filter = f"(uid={username})"
            
            conn.search(user_search_base, search_filter, 
                       attributes=['cn', 'mail', 'telephoneNumber', 'department'])
            
            if conn.entries:
                entry = conn.entries[0]
                return {
                    'username': username,
                    'full_name': entry.cn.value if hasattr(entry, 'cn') else username,
                    'email': entry.mail.value if hasattr(entry, 'mail') else '',
                    'phone': entry.telephoneNumber.value if hasattr(entry, 'telephoneNumber') else '',
                    'department': entry.department.value if hasattr(entry, 'department') else ''
                }
            
            return {'username': username, 'full_name': username}
            
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return {'username': username, 'full_name': username}
    
    def _encrypt_password(self, password):
        """Encrypt password for storage (simple base64 encoding for demo)"""
        # In production, use proper encryption like Fernet
        return base64.b64encode(password.encode()).decode()
    
    def _decrypt_password(self, encrypted_password):
        """Decrypt password for use"""
        try:
            return base64.b64decode(encrypted_password.encode()).decode()
        except:
            return encrypted_password  # Return as-is if decryption fails

class LDAPScheduler:
    """Handles scheduled LDAP operations"""
    
    def __init__(self):
        self.logger = Logger('ldap_scheduler')
        self.ldap_manager = LDAPManager()
    
    def run_scheduled_sync(self):
        """Run scheduled LDAP user synchronization"""
        config = self.ldap_manager.ldap_config
        sync_config = config.get('sync_schedule', {})
        
        if not sync_config.get('enabled', False):
            self.logger.info("LDAP sync not enabled")
            return
        
        # Check if it's time to sync (simplified - in production use cron or similar)
        current_time = datetime.now().strftime('%H:%M')
        sync_time = sync_config.get('time', '02:00')
        
        if current_time == sync_time:
            self.logger.info("Running scheduled LDAP user sync")
            success, message = self.ldap_manager.sync_users_from_ldap()
            
            if success:
                self.logger.info(f"Scheduled LDAP sync completed: {message}")
            else:
                self.logger.error(f"Scheduled LDAP sync failed: {message}")

if __name__ == "__main__":
    ldap_manager = LDAPManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test-connection":
            success, message = ldap_manager.test_ldap_connection()
            print(f"LDAP Connection Test: {'SUCCESS' if success else 'FAILED'}")
            print(f"Message: {message}")
        
        elif command == "sync-users":
            success, message = ldap_manager.sync_users_from_ldap()
            print(f"LDAP User Sync: {'SUCCESS' if success else 'FAILED'}")
            print(f"Message: {message}")
        
        elif command == "test-auth" and len(sys.argv) == 4:
            username = sys.argv[2]
            password = sys.argv[3]
            success, result = ldap_manager.authenticate_user(username, password)
            print(f"Authentication: {'SUCCESS' if success else 'FAILED'}")
            print(f"Result: {result}")
        
        else:
            print("Usage:")
            print("  python ldap_manager.py test-connection")
            print("  python ldap_manager.py sync-users")
            print("  python ldap_manager.py test-auth <username> <password>")
    else:
        print("LDAP Manager - Available commands:")
        print("  test-connection - Test LDAP connection")
        print("  sync-users     - Sync users from LDAP")
        print("  test-auth      - Test user authentication")