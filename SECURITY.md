# Security Configuration Guide

## ⚠️ IMPORTANT SECURITY NOTICE

This project contains **EXAMPLE CONFIGURATIONS ONLY**. Before deploying in production, you **MUST** configure proper security settings.

## 🔴 CRITICAL: Replace Before Production

### 1. User Authentication (`config/users.py`)
- **ALL passwords are set to `CHANGE_ME_IN_PRODUCTION`**
- **ALL email addresses use `@example.com` domain**

**Production Setup:**
```bash
# Set admin password via environment variable
export ADMIN_PASSWORD="your_secure_password_here"

# Or configure LDAP authentication in admin_config.json
```

### 2. Database Credentials (`config/settings.py`)
- **Database password:** `CHANGE_ME_IN_PRODUCTION`
- **SMTP password:** `CHANGE_ME_IN_PRODUCTION`

**Production Setup:**
```bash
export DB_PASSWORD="your_secure_db_password"
export SMTP_PASSWORD="your_smtp_password"
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
```

### 3. Flask Secret Key (`web_portal/app.py`)
- **Current key:** `CHANGE_ME_IN_PRODUCTION_USE_SECURE_RANDOM_KEY`

**Generate Secure Key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🛡️ Security Checklist

Before production deployment:

- [ ] Replace all `CHANGE_ME_IN_PRODUCTION` passwords
- [ ] Configure environment variables for all credentials
- [ ] Generate secure Flask secret key
- [ ] Set up proper SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable LDAP authentication (recommended)
- [ ] Review and test all authentication mechanisms
- [ ] Set up proper logging and monitoring
- [ ] Change all email addresses from `@example.com` to your domain

## 🔧 Environment Variables

Create a `.env` file (excluded from git) with:

```bash
# Database
DB_PASSWORD=your_secure_database_password
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user

# Email
SMTP_PASSWORD=your_smtp_password
SMTP_SERVER=your_smtp_server
SMTP_USERNAME=your_smtp_username

# Flask
FLASK_SECRET_KEY=your_32_character_hex_key

# Authentication (if not using LDAP)
ADMIN_PASSWORD=your_admin_password
```

## 📚 Additional Security Recommendations

1. **Use HTTPS only** in production
2. **Enable rate limiting** on authentication endpoints
3. **Set up proper logging** for security events
4. **Regular security audits** and updates
5. **Network segmentation** and firewalls
6. **Regular backups** with encryption
7. **Monitor for security vulnerabilities**

## 🚨 NEVER COMMIT REAL CREDENTIALS

- Always use environment variables for sensitive data
- Never commit `.env` files or production config files
- Use secrets management systems in enterprise environments
- Regularly rotate passwords and keys

---

**This is a demonstration/development project. Production deployment requires proper security configuration by qualified security professionals.**