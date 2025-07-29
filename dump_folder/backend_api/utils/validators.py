"""
Data validation utilities
"""

import re
from typing import Dict, Tuple, List, Any

def validate_login_data(data: Dict) -> Tuple[bool, List[str]]:
    """Validate login data"""
    errors = []
    
    if not data:
        errors.append("Request body is required")
        return False, errors
    
    username = data.get('username')
    password = data.get('password')
    
    if not username:
        errors.append("Username is required")
    elif len(username) < 3:
        errors.append("Username must be at least 3 characters")
    
    if not password:
        errors.append("Password is required")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters")
    
    return len(errors) == 0, errors

def validate_server_data(data: Dict) -> Tuple[bool, List[str]]:
    """Validate server data"""
    errors = []
    
    if not data:
        errors.append("Request body is required")
        return False, errors
    
    # Required fields
    required_fields = [
        'serverName',
        'hostGroup',
        'operatingSystem',
        'serverTimezone',
        'primaryOwner',
        'patcherEmail'
    ]
    
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
    
    # Validate server name format
    server_name = data.get('serverName')
    if server_name:
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', server_name):
            errors.append("Server name can only contain letters, numbers, hyphens, dots, and underscores")
        if len(server_name) > 255:
            errors.append("Server name must be less than 255 characters")
    
    # Validate email format
    email_fields = ['patcherEmail', 'notificationEmail']
    for field in email_fields:
        email = data.get(field)
        if email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append(f"{field} must be a valid email address")
    
    # Validate operating system
    valid_os = ['ubuntu', 'debian', 'centos', 'rhel', 'fedora']
    if data.get('operatingSystem') not in valid_os:
        errors.append(f"Operating system must be one of: {', '.join(valid_os)}")
    
    # Validate environment
    valid_environments = ['production', 'staging', 'development', 'testing']
    if data.get('environment') and data.get('environment') not in valid_environments:
        errors.append(f"Environment must be one of: {', '.join(valid_environments)}")
    
    # Validate SSH port
    ssh_port = data.get('sshPort')
    if ssh_port:
        try:
            port = int(ssh_port)
            if port < 1 or port > 65535:
                errors.append("SSH port must be between 1 and 65535")
        except (ValueError, TypeError):
            errors.append("SSH port must be a valid number")
    
    # Validate timezone
    timezone = data.get('serverTimezone')
    if timezone:
        valid_timezones = [
            'UTC', 'America/New_York', 'America/Chicago', 'America/Denver',
            'America/Los_Angeles', 'Europe/London', 'Europe/Paris',
            'Europe/Berlin', 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata',
            'Australia/Sydney'
        ]
        if timezone not in valid_timezones:
            errors.append(f"Timezone must be one of: {', '.join(valid_timezones)}")
    
    # Validate patch group priority
    priority = data.get('patchGroupPriority')
    if priority:
        try:
            p = int(priority)
            if p < 1 or p > 10:
                errors.append("Patch group priority must be between 1 and 10")
        except (ValueError, TypeError):
            errors.append("Patch group priority must be a valid number")
    
    return len(errors) == 0, errors

def validate_patching_job_data(data: Dict) -> Tuple[bool, List[str]]:
    """Validate patching job data"""
    errors = []
    
    if not data:
        errors.append("Request body is required")
        return False, errors
    
    # Required fields
    if not data.get('servers'):
        errors.append("Servers list is required")
    elif not isinstance(data.get('servers'), list):
        errors.append("Servers must be a list")
    elif len(data.get('servers')) == 0:
        errors.append("At least one server is required")
    
    # Validate job name
    name = data.get('name')
    if name and len(name) > 255:
        errors.append("Job name must be less than 255 characters")
    
    # Validate quarter
    quarter = data.get('quarter')
    if quarter and quarter not in ['Q1', 'Q2', 'Q3', 'Q4']:
        errors.append("Quarter must be one of: Q1, Q2, Q3, Q4")
    
    # Validate boolean fields
    boolean_fields = ['dryRun', 'force', 'skipPrecheck', 'skipPostcheck']
    for field in boolean_fields:
        value = data.get(field)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field} must be a boolean")
    
    return len(errors) == 0, errors

def validate_approval_data(data: Dict) -> Tuple[bool, List[str]]:
    """Validate approval request data"""
    errors = []
    
    if not data:
        errors.append("Request body is required")
        return False, errors
    
    # Required fields
    required_fields = [
        'serverId',
        'quarter',
        'businessJustification',
        'riskAssessment',
        'rollbackPlan',
        'emergencyContact',
        'maintenanceWindow'
    ]
    
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field} is required")
    
    # Validate quarter
    quarter = data.get('quarter')
    if quarter and quarter not in ['Q1', 'Q2', 'Q3', 'Q4']:
        errors.append("Quarter must be one of: Q1, Q2, Q3, Q4")
    
    # Validate emergency contact (should be email)
    emergency_contact = data.get('emergencyContact')
    if emergency_contact and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', emergency_contact):
        errors.append("Emergency contact must be a valid email address")
    
    # Validate dependencies (should be list)
    dependencies = data.get('dependencies')
    if dependencies and not isinstance(dependencies, list):
        errors.append("Dependencies must be a list")
    
    # Validate boolean fields
    boolean_fields = ['testingRequired', 'backupRequired']
    for field in boolean_fields:
        value = data.get(field)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field} must be a boolean")
    
    return len(errors) == 0, errors

def validate_report_config(data: Dict) -> Tuple[bool, List[str]]:
    """Validate report configuration data"""
    errors = []
    
    if not data:
        errors.append("Request body is required")
        return False, errors
    
    # Required fields
    if not data.get('type'):
        errors.append("Report type is required")
    
    if not data.get('format'):
        errors.append("Report format is required")
    
    # Validate type
    valid_types = ['summary', 'detailed', 'quarterly', 'daily', 'custom']
    if data.get('type') not in valid_types:
        errors.append(f"Report type must be one of: {', '.join(valid_types)}")
    
    # Validate format
    valid_formats = ['pdf', 'csv', 'json', 'html']
    if data.get('format') not in valid_formats:
        errors.append(f"Report format must be one of: {', '.join(valid_formats)}")
    
    # Validate quarter
    quarter = data.get('quarter')
    if quarter and quarter not in ['Q1', 'Q2', 'Q3', 'Q4']:
        errors.append("Quarter must be one of: Q1, Q2, Q3, Q4")
    
    # Validate date range
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    if start_date and end_date:
        try:
            from datetime import datetime
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            if start >= end:
                errors.append("Start date must be before end date")
        except ValueError:
            errors.append("Invalid date format")
    
    # Validate lists
    list_fields = ['servers', 'groups', 'environments', 'recipients']
    for field in list_fields:
        value = data.get(field)
        if value and not isinstance(value, list):
            errors.append(f"{field} must be a list")
    
    # Validate boolean fields
    boolean_fields = ['includeDetails', 'includeCharts', 'includeAuditTrail']
    for field in boolean_fields:
        value = data.get(field)
        if value is not None and not isinstance(value, bool):
            errors.append(f"{field} must be a boolean")
    
    return len(errors) == 0, errors