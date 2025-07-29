"""
API Decorators
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.users import UserManager

user_manager = UserManager()

def require_permission(permission):
    """
    Decorator to require specific permission
    
    Args:
        permission: Permission string (e.g., 'servers.create')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get current user
                identity = get_jwt_identity()
                claims = get_jwt()
                
                user = user_manager.get_user(identity)
                if not user:
                    return jsonify({
                        'success': False,
                        'message': 'User not found'
                    }), 401
                
                # Check if user has required permission
                user_permissions = user.get('permissions', [])
                user_role = user.get('role', '')
                
                # Admin has all permissions
                if user_role == 'admin':
                    return f(*args, **kwargs)
                
                # Check specific permission
                if permission not in user_permissions:
                    return jsonify({
                        'success': False,
                        'message': 'Insufficient permissions'
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Permission check failed: {str(e)}'
                }), 500
        
        return decorated_function
    return decorator

def require_role(role):
    """
    Decorator to require specific role
    
    Args:
        role: Role string (e.g., 'admin', 'operator')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get current user
                identity = get_jwt_identity()
                user = user_manager.get_user(identity)
                
                if not user:
                    return jsonify({
                        'success': False,
                        'message': 'User not found'
                    }), 401
                
                # Check role
                if user.get('role') != role:
                    return jsonify({
                        'success': False,
                        'message': 'Insufficient role'
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Role check failed: {str(e)}'
                }), 500
        
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    return require_role('admin')(f)

def operator_required(f):
    """Decorator to require operator role or higher"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get current user
            identity = get_jwt_identity()
            user = user_manager.get_user(identity)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 401
            
            # Check role (admin or operator)
            user_role = user.get('role')
            if user_role not in ['admin', 'operator']:
                return jsonify({
                    'success': False,
                    'message': 'Insufficient role'
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Role check failed: {str(e)}'
            }), 500
    
    return decorated_function

def validate_json(f):
    """Decorator to validate JSON content type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Content-Type must be application/json'
                }), 400
            
            if not request.get_json():
                return jsonify({
                    'success': False,
                    'message': 'Request body must contain valid JSON'
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(max_requests=100, window=3600):
    """
    Simple rate limiting decorator
    
    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In production, implement proper rate limiting with Redis
            # For now, just pass through
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator