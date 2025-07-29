"""
Audit logging utilities
"""

import json
from datetime import datetime
from flask import request, g
import uuid
import os

# Simple file-based audit logging (in production, use database)
AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), '../../logs/audit.log')

def log_audit_event(action, resource, user_id=None, resource_id=None, details=None):
    """
    Log an audit event
    
    Args:
        action: Action performed (e.g., 'login', 'server_created')
        resource: Resource type (e.g., 'auth', 'servers')
        user_id: User who performed the action
        resource_id: ID of the resource affected
        details: Additional details (dict)
    """
    try:
        # Get request info if available
        ip_address = '127.0.0.1'
        user_agent = ''
        
        if request:
            ip_address = request.remote_addr or '127.0.0.1'
            user_agent = request.headers.get('User-Agent', '')
        
        # Create audit log entry
        audit_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'resource': resource,
            'resourceId': resource_id,
            'userId': user_id,
            'ipAddress': ip_address,
            'userAgent': user_agent,
            'details': details or {},
            'result': 'success'  # Assume success unless specified otherwise
        }
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        
        # Write to log file
        with open(AUDIT_LOG_FILE, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')
            
    except Exception as e:
        # Don't fail the main operation if audit logging fails
        print(f"Failed to log audit event: {e}")

def get_audit_logs(page=1, page_size=20, filters=None):
    """
    Get audit logs with pagination
    
    Args:
        page: Page number
        page_size: Items per page
        filters: Dict of filters (action, resource, user_id, etc.)
    
    Returns:
        dict: Paginated audit logs
    """
    try:
        logs = []
        
        if os.path.exists(AUDIT_LOG_FILE):
            with open(AUDIT_LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Apply filters
                        if filters:
                            if filters.get('action') and log_entry.get('action') != filters['action']:
                                continue
                            if filters.get('resource') and log_entry.get('resource') != filters['resource']:
                                continue
                            if filters.get('user_id') and log_entry.get('userId') != filters['user_id']:
                                continue
                            if filters.get('start_date'):
                                if log_entry.get('timestamp', '') < filters['start_date']:
                                    continue
                            if filters.get('end_date'):
                                if log_entry.get('timestamp', '') > filters['end_date']:
                                    continue
                        
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Paginate
        from .pagination import paginate_results
        return paginate_results(logs, page, page_size)
        
    except Exception as e:
        print(f"Failed to get audit logs: {e}")
        return {
            'items': [],
            'total': 0,
            'page': page,
            'page_size': page_size,
            'total_pages': 0,
            'has_next': False,
            'has_previous': False
        }