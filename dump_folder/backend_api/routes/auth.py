"""
Authentication Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.users import UserManager
from backend_api.utils.audit import log_audit_event
from backend_api.utils.validators import validate_login_data

auth_bp = Blueprint('auth', __name__)
user_manager = UserManager()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        
        # Validate input
        is_valid, errors = validate_login_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Authenticate user
        user = user_manager.authenticate(username, password)
        if not user:
            log_audit_event(
                action='login_failed',
                resource='auth',
                user_id=username,
                details={'reason': 'invalid_credentials'}
            )
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401
        
        # Create tokens
        access_token = create_access_token(
            identity=username,
            additional_claims={
                'role': user['role'],
                'email': user.get('email', ''),
                'permissions': user.get('permissions', [])
            }
        )
        refresh_token = create_refresh_token(identity=username)
        
        # Update last login
        user_manager.update_last_login(username)
        
        # Log successful login
        log_audit_event(
            action='login_success',
            resource='auth',
            user_id=username,
            details={'ip': request.remote_addr}
        )
        
        return jsonify({
            'success': True,
            'data': {
                'accessToken': access_token,
                'refreshToken': refresh_token,
                'tokenType': 'Bearer',
                'expiresIn': 86400,  # 24 hours in seconds
                'user': {
                    'username': user['username'],
                    'email': user.get('email', ''),
                    'role': user['role'],
                    'permissions': user.get('permissions', [])
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        identity = get_jwt_identity()
        user = user_manager.get_user(identity)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Create new access token
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                'role': user['role'],
                'email': user.get('email', ''),
                'permissions': user.get('permissions', [])
            }
        )
        
        return jsonify({
            'success': True,
            'data': {
                'accessToken': access_token,
                'tokenType': 'Bearer',
                'expiresIn': 86400
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Token refresh failed: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint"""
    try:
        identity = get_jwt_identity()
        
        # Log logout event
        log_audit_event(
            action='logout',
            resource='auth',
            user_id=identity
        )
        
        # In a production app, you might want to blacklist the token here
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout failed: {str(e)}'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        identity = get_jwt_identity()
        user = user_manager.get_user(identity)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': user['username'],  # Using username as ID
                'username': user['username'],
                'email': user.get('email', ''),
                'firstName': user.get('first_name', ''),
                'lastName': user.get('last_name', ''),
                'role': user['role'],
                'permissions': user.get('permissions', []),
                'isActive': user.get('active', True),
                'createdAt': user.get('created_at', ''),
                'updatedAt': user.get('updated_at', ''),
                'lastLogin': user.get('last_login', '')
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get profile: {str(e)}'
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        identity = get_jwt_identity()
        data = request.get_json()
        
        # Only allow updating certain fields
        allowed_fields = ['email', 'first_name', 'last_name']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        success = user_manager.update_user(identity, update_data)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Failed to update profile'
            }), 400
        
        # Log update event
        log_audit_event(
            action='profile_updated',
            resource='auth',
            user_id=identity,
            details={'fields': list(update_data.keys())}
        )
        
        # Return updated profile
        return get_profile()
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        identity = get_jwt_identity()
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Current and new passwords are required'
            }), 400
        
        # Verify current password
        user = user_manager.authenticate(identity, current_password)
        if not user:
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 401
        
        # Update password
        success = user_manager.change_password(identity, new_password)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Failed to change password'
            }), 400
        
        # Log password change
        log_audit_event(
            action='password_changed',
            resource='auth',
            user_id=identity
        )
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to change password: {str(e)}'
        }), 500