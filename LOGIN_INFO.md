# Web UI Login Information

## Current Login Credentials

### For Initial Setup (Demo Mode)

Since LDAP is not yet configured, use these demo accounts:

#### Primary Admin Login:
- **Username**: `patchadmin`
- **Password**: `admin123`
- **Role**: Full Administrator
- **Access**: All system features and configuration

#### Alternative Admin Login:
- **Username**: `admin`  
- **Password**: `admin`
- **Role**: Full Administrator
- **Access**: All system features and configuration

## How to Login

1. **Open your browser** and go to: `http://your-server:5001`
2. **Enter credentials**:
   - Username: `patchadmin`
   - Password: `admin123`
3. **Click Login**

## After LDAP Configuration

Once LDAP is properly configured:

- **Username**: Your Linux username (not email)
- **Password**: Your Linux/LDAP password
- **Admin Access**: Based on netgroup membership (`patching_admins`)

## Important Notes

- These demo accounts are **for initial setup only**
- In production, **disable fallback authentication** after LDAP is working
- The `patchadmin` system user password is separate from web login
- Web authentication will use LDAP in production

## Troubleshooting Login Issues

### "Invalid username/password"
1. Make sure you're using `patchadmin` (not admin)
2. Make sure password is `admin123` (not admin)
3. Clear browser cache/cookies
4. Check if service is running: `ps aux | grep app.py`

### LDAP Issues (future)
1. Verify nslcd service: `systemctl status nslcd`
2. Test user exists: `id username`
3. Check netgroup membership: `getent netgroup patching_admins`

## Security Reminder

**Change these default passwords** once you have LDAP configured and working!