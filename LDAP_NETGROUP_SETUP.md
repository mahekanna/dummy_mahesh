# LDAP Authentication & Linux Netgroup Integration

## Overview

The Linux Patching Automation System now supports:

1. **LDAP Authentication** - Users authenticate via corporate LDAP
2. **Linux Netgroup Admin Control** - Admins controlled via system netgroups  
3. **Database-Driven Permissions** - User access based on server ownership in CSV/database
4. **Fallback Authentication** - Local authentication for demo/testing

## Architecture

### Authentication Flow
```
User Login → LDAP Authentication → Netgroup Check → Server Ownership → Role Assignment
     ↓               ↓                   ↓              ↓                ↓
   Username      Verify Creds      Check Admin     CSV/DB Query     Permissions
     &           via LDAP          Netgroup        for Owned        Based on Role
   Password        Server           Membership      Servers          & Ownership
```

### User Roles
- **Admin**: Members of Linux netgroup `patching_admins` (configurable)
- **User**: Server owners (primary/secondary in CSV database)
- **Readonly**: LDAP users with no server ownership

## Configuration

### Environment Variables
```bash
# LDAP Configuration
export LDAP_ENABLED=true
export LDAP_SERVER=ldap://ldap.company.com
export LDAP_BASE_DN=dc=company,dc=com
export LDAP_BIND_DN=cn=admin,dc=company,dc=com
export LDAP_BIND_PASSWORD=your-ldap-password

# Admin Control
export ADMIN_NETGROUP=patching_admins

# Fallback Authentication (for demo/testing)
export ENABLE_FALLBACK_AUTH=true
```

### Netgroup Setup

#### Option 1: Local /etc/netgroup
```bash
# /etc/netgroup
patching_admins (,john.doe,) (,jane.admin,) (,sysadmin,)
web_admins (,web.admin,) (,frontend.dev,)
db_admins (,dba.user,) (,database.admin,)
```

#### Option 2: NIS/LDAP Netgroups
```bash
# Test netgroup membership
getent netgroup patching_admins
innetgr patching_admins - username -
```

#### Option 3: LDAP-based Netgroups
Configure in your LDAP server with appropriate schema.

## User Access Control

### Admin Users
- **Detection**: Linux netgroup membership OR LDAP group membership
- **Permissions**: Full system access, all servers, all operations
- **Netgroup Check**: `innetgr patching_admins - username -`

### Regular Users  
- **Detection**: Server ownership in CSV/database
- **Permissions**: Only owned servers (primary_owner or secondary_owner)
- **Access**: View, modify, approve own servers only

### Server Ownership Examples
```csv
Server Name,primary_owner,secondary_owner,host_group
web01.company.com,john.doe@company.com,jane.backup@company.com,web_servers
db01.company.com,dba.admin@company.com,,db_servers
app01.company.com,dev.team@company.com,ops.team@company.com,app_servers
```

## Implementation Details

### LDAP Authentication (`utils/ldap_auth.py`)
```python
class LDAPAuthenticator:
    def authenticate_user(username, password):
        # 1. Connect to LDAP server
        # 2. Bind with user credentials  
        # 3. Get user information
        # 4. Check netgroup membership
        # 5. Determine role and permissions
        # 6. Return user data
```

### Netgroup Integration
```python
def _is_user_in_netgroup(username, netgroup):
    # Method 1: getent netgroup
    # Method 2: innetgr command
    # Method 3: /etc/netgroup file
    # Returns True if user is member
```

### User Management (`config/users.py`)
```python
class UserManager:
    def authenticate_user(username, password):
        # 1. Try LDAP authentication first
        # 2. Fallback to local authentication
        # 3. Return unified user data
        
    def get_user_servers(username, role):
        # Return servers based on ownership
        # Admin: all servers
        # User: owned servers only
```

## Web Portal Integration

### Updated Login Flow
1. User enters username/email and password
2. System tries LDAP authentication first
3. Falls back to local authentication if LDAP fails
4. Loads user permissions based on role and ownership
5. Dashboard shows only accessible servers

### Enhanced User Interface
- Displays authentication method (LDAP vs Local)
- Shows user department and title from LDAP
- Permission-based menu visibility
- Server access filtered by ownership

## Testing & Validation

### Test LDAP Integration
```bash
# Run comprehensive test suite
python3 test_ldap_auth.py

# Test specific components
python3 -c "from utils.ldap_auth import LDAPAuthenticator; auth = LDAPAuthenticator(); print(auth.validate_ldap_connection())"
```

### Test Netgroup Membership
```bash
# Check current user
getent netgroup patching_admins
innetgr patching_admins - $(whoami) -

# Manual test
python3 -c "
from utils.ldap_auth import LDAPAuthenticator
auth = LDAPAuthenticator()
print(auth._is_user_in_netgroup('$(whoami)', 'patching_admins'))
"
```

### Test Server Ownership
```bash
# Check user server access
python3 -c "
from config.users import UserManager
um = UserManager()
servers = um.get_user_servers('dba@company.com', 'user')
print(f'DBA has access to {len(servers)} servers')
"
```

## Production Deployment

### Prerequisites
```bash
# Install LDAP libraries
apt-get install python3-ldap python3-ldap3
# OR
pip3 install python-ldap ldap3

# Configure netgroups (choose one)
# 1. Local file: /etc/netgroup
# 2. NIS: /etc/nsswitch.conf
# 3. LDAP: LDAP server configuration
```

### Deployment Steps

1. **Configure LDAP**:
   ```bash
   export LDAP_ENABLED=true
   export LDAP_SERVER=ldaps://ldap.company.com:636
   export LDAP_BASE_DN=dc=company,dc=com
   export LDAP_BIND_DN=cn=patchservice,ou=service,dc=company,dc=com
   export LDAP_BIND_PASSWORD="$(cat /etc/ldap.secret)"
   ```

2. **Setup Netgroups**:
   ```bash
   # Add to /etc/netgroup or configure via NIS/LDAP
   echo "patching_admins (,admin1,) (,admin2,) (,sysadmin,)" >> /etc/netgroup
   ```

3. **Update Server Ownership**:
   ```bash
   # Ensure CSV has proper ownership data
   python3 main.py --import-csv /path/to/updated_servers.csv
   ```

4. **Test Authentication**:
   ```bash
   # Validate setup
   python3 test_ldap_auth.py
   ```

5. **Deploy Application**:
   ```bash
   # Full deployment with LDAP support
   sudo ./deploy_complete.sh
   ```

## Security Considerations

### LDAP Security
- Use LDAPS (SSL/TLS) for production
- Service account with minimal privileges
- Secure password storage (environment variables, key management)
- Connection timeouts and retry logic

### Netgroup Security
- Regular audit of netgroup membership
- Principle of least privilege
- Monitor netgroup changes
- Backup netgroup configurations

### Access Control
- Server ownership validation
- Permission-based UI restrictions
- Audit logging of all operations
- Regular access reviews

## Troubleshooting

### Common Issues

1. **LDAP Connection Failed**:
   ```bash
   # Test connectivity
   ldapsearch -H ldap://ldap.company.com -D "cn=admin,dc=company,dc=com" -W -b "dc=company,dc=com" "(uid=testuser)"
   ```

2. **Netgroup Not Working**:
   ```bash
   # Check nsswitch.conf
   grep netgroup /etc/nsswitch.conf
   # Should include: netgroup: nis files
   ```

3. **User Access Issues**:
   ```bash
   # Check server ownership
   grep "username@company.com" data/servers.csv
   ```

4. **Authentication Loop**:
   ```bash
   # Check fallback setting
   export ENABLE_FALLBACK_AUTH=true
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 web_portal/app.py
```

## Demo Mode

For demonstration without LDAP infrastructure:

```bash
# Disable LDAP, enable fallback
export LDAP_ENABLED=false
export ENABLE_FALLBACK_AUTH=true

# Use demo accounts
./demo_setup.sh
python3 web_portal/app.py
```

Demo accounts will use local authentication while maintaining the same interface and permissions structure.

---

## Summary

This implementation provides enterprise-grade authentication with:
- ✅ LDAP integration for corporate authentication
- ✅ Linux netgroup-based admin control
- ✅ Database-driven user permissions
- ✅ Graceful fallback for testing/demo
- ✅ Security-focused design
- ✅ Comprehensive testing suite