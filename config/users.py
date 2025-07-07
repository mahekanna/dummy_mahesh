# config/users.py
"""
User management and role-based access control
"""

class UserManager:
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
                'system_admin'
            ]
        },
        'user': {
            'name': 'Regular User',
            'permissions': [
                'view_owned_servers',
                'modify_owned_schedules',
                'approve_owned_schedules'
            ]
        },
        'readonly': {
            'name': 'Read Only User',
            'permissions': [
                'view_owned_servers'
            ]
        }
    }
    
    # User database - in production this would be in a database/LDAP
    USERS = {
        # EXAMPLE USERS - REPLACE WITH PROPER AUTHENTICATION SYSTEM
        # WARNING: These are examples only. In production, use proper password hashing,
        # environment variables, LDAP, or database-based authentication
        'admin@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',  # Use environment variable: os.getenv('ADMIN_PASSWORD')
            'role': 'admin',
            'name': 'System Administrator',
            'active': True
        },
        'sysadmin@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',
            'role': 'admin',
            'name': 'System Admin',
            'active': True
        },
        
        # Regular users (server owners)
        'dba@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',
            'role': 'user',
            'name': 'Database Administrator',
            'active': True
        },
        'dev@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',
            'role': 'user',
            'name': 'Development Team',
            'active': True
        },
        'ops@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',
            'role': 'user',
            'name': 'Operations Team',
            'active': True
        },
        'backup@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',
            'role': 'user',
            'name': 'Backup Team',
            'active': True
        },
        
        # Test users
        'testuser@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',
            'role': 'user',
            'name': 'Test User',
            'active': True
        },
        'readonly@example.com': {
            'password': 'CHANGE_ME_IN_PRODUCTION',
            'role': 'readonly',
            'name': 'Read Only User',
            'active': True
        }
    }
    
    @classmethod
    def authenticate_user(cls, email, password):
        """Authenticate user credentials"""
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
    
    @classmethod
    def get_user_info(cls, email):
        """Get user information"""
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