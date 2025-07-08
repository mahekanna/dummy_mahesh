# Linux Patching Automation - Authentication Model

## Overview

This system uses a **dual authentication model**:

1. **System/SSH Access**: Uses the `patchadmin` system user account
2. **Web UI Access**: Uses LDAP/nslcd authentication with Linux netgroups

## Authentication Details

### 1. System User: `patchadmin`

**Purpose**: Running the application, SSH access to remote servers, system operations

**Password Required**: YES (set during deployment)

**Used For**:
- Running the Flask web application
- Running the monitoring service
- SSH connections to remote servers for patching
- System-level operations (file access, service management)

**NOT Used For**:
- Web UI login
- API access
- User authentication

### 2. Web UI Authentication: LDAP/nslcd

**Purpose**: User authentication for web portal access

**Password Required**: NO (uses existing LDAP/Linux credentials)

**Authentication Flow**:
1. User enters their Linux username (not email)
2. Password is validated against LDAP via nslcd
3. User's netgroup membership determines admin access
4. Server ownership (from CSV) determines which servers they can manage

**Admin Access**:
- Users must be members of the configured netgroup (default: `patching_admins`)
- Admin users can see and manage all servers
- Admin users can access system configuration

**Regular User Access**:
- Any valid LDAP user can log in
- Can only see/manage servers where they are listed as primary or secondary owner
- Limited to server scheduling and approval functions

## Configuration

### During Deployment

The deployment script will prompt for:

1. **patchadmin password** - System account password for SSH/sudo operations
2. **LDAP settings** (optional) - For web UI authentication
3. **Admin netgroup** - Linux netgroup for admin users (default: `patching_admins`)

### Post-Deployment

#### To Grant Admin Access:
```bash
# Add user to admin netgroup
sudo netgroup modify patching_admins add user=johndoe

# Or edit /etc/netgroup directly
patching_admins (,johndoe,) (,janedoe,)
```

#### To Enable LDAP Authentication:
1. Ensure nslcd is configured and running
2. Set LDAP_ENABLED=true in configuration
3. Configure admin netgroup name

## Authentication Scenarios

### Scenario 1: Production with LDAP
- **Web Login**: Users log in with their Linux username/password
- **Admin Access**: Based on netgroup membership
- **No local passwords**: All authentication via LDAP

### Scenario 2: Demo/Testing without LDAP
- **Web Login**: Use demo account `admin/admin`
- **Limited to testing**: Not for production use
- **Fallback only**: When LDAP is disabled

### Scenario 3: Emergency Access
- **SSH Access**: Use `patchadmin` system account
- **CLI Operations**: Run as `patchadmin` user
- **Bypass Web UI**: Direct database/file access if needed

## Security Best Practices

1. **Always enable LDAP** for production deployments
2. **Disable fallback auth** after LDAP is working:
   ```bash
   # In /opt/linux_patching_automation/.env
   ENABLE_FALLBACK_AUTH=false
   ```

3. **Secure the patchadmin account**:
   - Use strong password
   - Limit SSH access
   - Use SSH keys where possible

4. **Regular netgroup audits**:
   - Review admin netgroup membership
   - Remove users who no longer need access

5. **CSV ownership accuracy**:
   - Ensure primary/secondary owners use correct Linux usernames
   - Regular audits of server ownership

## Troubleshooting

### "Invalid username/password" at Web Login

1. **Check username format**: Use Linux username, not email
2. **Verify LDAP**: 
   ```bash
   id username
   getent passwd username
   ```
3. **Check nslcd**: 
   ```bash
   systemctl status nslcd
   ```
4. **Test authentication**:
   ```bash
   # As patchadmin user
   python3 -c "from utils.nslcd_ldap_auth import NSLCDLDAPAuthenticator; auth = NSLCDLDAPAuthenticator(); print(auth.authenticate_user('username', 'password'))"
   ```

### Cannot SSH as patchadmin

1. **Verify password was set**: During deployment
2. **Check account status**:
   ```bash
   id patchadmin
   grep patchadmin /etc/passwd
   ```
3. **Test local login**:
   ```bash
   su - patchadmin
   ```

## Summary

- **patchadmin password**: For system/SSH access only
- **Web UI login**: Uses LDAP/Linux credentials
- **No web passwords**: Authentication via nslcd/LDAP
- **Admin access**: Controlled by netgroup membership
- **User access**: Based on CSV server ownership