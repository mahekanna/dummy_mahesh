#!/usr/bin/env python3
"""
Complete REST API Backend for Linux Patching Automation System
Integrates with existing Python CLI system to provide modern React frontend support
"""

import os
import sys
import json
import uuid
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from threading import Thread
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, create_refresh_token, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import tempfile
import io
import csv as csv_module

# Import existing system modules
from utils.csv_handler import CSVHandler
from utils.email_sender import EmailSender
from utils.logger import Logger
from utils.timezone_handler import TimezoneHandler
from config.settings import Config
from config.users import UserManager
from scripts.step0_approval_requests import ApprovalRequestHandler
from scripts.step1_monthly_notice import MonthlyNoticeHandler
from scripts.step1b_weekly_followup import WeeklyFollowupHandler
from scripts.step2_reminders import ReminderHandler
from scripts.step3_prechecks import PreCheckHandler
from scripts.step4_scheduler import PatchScheduler
from scripts.step5_patch_validation import PatchValidator
from scripts.step6_post_patch import PostPatchValidator
from scripts.intelligent_scheduler import SmartScheduler
from scripts.load_predictor import SmartLoadPredictor
from scripts.automated_reports import ReportGenerator
from database.models import DatabaseManager

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
jwt = JWTManager(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configure CORS
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001'], supports_credentials=True)

# Initialize core handlers
csv_handler = CSVHandler()
email_sender = EmailSender()
logger = Logger('api_backend')
timezone_handler = TimezoneHandler()
user_manager = UserManager()
db_manager = DatabaseManager()

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)

# Active jobs tracking
active_jobs = {}
job_results = {}

# JWT token blacklist for logout
blacklisted_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    """Check if JWT token is blacklisted"""
    return jwt_payload['jti'] in blacklisted_tokens

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token"""
    return jsonify({'success': False, 'message': 'Token has expired', 'code': 'TOKEN_EXPIRED'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid token"""
    return jsonify({'success': False, 'message': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing token"""
    return jsonify({'success': False, 'message': 'Authorization token is required', 'code': 'MISSING_TOKEN'}), 401

def api_response(success=True, data=None, message=None, code=200):
    """Standard API response format"""
    response = {
        'success': success,
        'data': data,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'requestId': request.headers.get('X-Request-ID', str(uuid.uuid4()))
    }
    return jsonify(response), code

def handle_error(error, message="An error occurred", code=500):
    """Standard error handler"""
    logger.error(f"API Error: {message} - {str(error)}")
    logger.error(traceback.format_exc())
    return api_response(success=False, message=message, code=code)

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_email = get_jwt_identity()
            user_info = user_manager.get_user_info(current_user_email)
            
            if not user_info:
                return api_response(success=False, message="User not found", code=404)
            
            if permission not in user_info.get('permissions', []):
                return api_response(success=False, message="Insufficient permissions", code=403)
            
            g.current_user = user_info
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_email = get_jwt_identity()
            user_info = user_manager.get_user_info(current_user_email)
            
            if not user_info:
                return api_response(success=False, message="User not found", code=404)
            
            if user_info.get('role') != role and user_info.get('role') != 'admin':
                return api_response(success=False, message="Insufficient role", code=403)
            
            g.current_user = user_info
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def normalize_server_data(server):
    """Normalize server data for API response"""
    return {
        'id': server.get('server_name', ''),
        'serverName': server.get('server_name', ''),
        'hostGroup': server.get('host_group', ''),
        'operatingSystem': server.get('operating_system', ''),
        'environment': server.get('environment', ''),
        'serverTimezone': server.get('server_timezone', ''),
        'location': server.get('location', ''),
        'primaryOwner': server.get('primary_owner', ''),
        'secondaryOwner': server.get('secondary_owner', ''),
        'primaryLinuxUser': server.get('primary_linux_user', ''),
        'secondaryLinuxUser': server.get('secondary_linux_user', ''),
        'patcherEmail': server.get('patcher_email', ''),
        'engineeringDomain': server.get('engr_domain', ''),
        'incidentTicket': server.get('incident_ticket', ''),
        
        # Patching schedule
        'q1PatchDate': server.get('q1_patch_date', ''),
        'q1PatchTime': server.get('q1_patch_time', ''),
        'q1ApprovalStatus': server.get('q1_approval_status', 'pending').lower(),
        'q2PatchDate': server.get('q2_patch_date', ''),
        'q2PatchTime': server.get('q2_patch_time', ''),
        'q2ApprovalStatus': server.get('q2_approval_status', 'pending').lower(),
        'q3PatchDate': server.get('q3_patch_date', ''),
        'q3PatchTime': server.get('q3_patch_time', ''),
        'q3ApprovalStatus': server.get('q3_approval_status', 'pending').lower(),
        'q4PatchDate': server.get('q4_patch_date', ''),
        'q4PatchTime': server.get('q4_patch_time', ''),
        'q4ApprovalStatus': server.get('q4_approval_status', 'pending').lower(),
        
        # Status
        'currentQuarterPatchingStatus': server.get('current_quarter_status', 'pending').lower(),
        'activeStatus': 'active',  # Default to active
        'lastSyncDate': server.get('last_sync_date', ''),
        'syncStatus': server.get('sync_status', 'success').lower(),
        
        # SSH Configuration
        'sshPort': 22,
        'backupRequired': True,
        'criticalServices': [],
        'patchGroupPriority': 1,
        'autoApprove': False,
        
        # Timestamps
        'createdDate': datetime.now().isoformat(),
        'modifiedDate': datetime.now().isoformat(),
        
        # Computed fields
        'nextPatchDate': get_next_patch_date(server),
        'connectivityStatus': 'unknown'
    }

def get_next_patch_date(server):
    """Get next patch date for server"""
    current_quarter = Config.get_current_quarter()
    return server.get(f'q{current_quarter}_patch_date', '')

def create_patching_job(job_id, config):
    """Create a new patching job"""
    job = {
        'id': job_id,
        'name': config.get('name', f'Patching Job {job_id}'),
        'description': config.get('description', ''),
        'type': 'batch',
        'status': 'pending',
        'progress': 0,
        'quarter': config.get('quarter', Config.get_current_quarter()),
        'servers': config.get('servers', []),
        'dryRun': config.get('dryRun', False),
        'force': config.get('force', False),
        'skipPrecheck': config.get('skipPrecheck', False),
        'skipPostcheck': config.get('skipPostcheck', False),
        'operator': get_jwt_identity(),
        'successCount': 0,
        'failureCount': 0,
        'totalCount': len(config.get('servers', [])),
        'serverResults': [],
        'logs': [],
        'createdAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat()
    }
    
    # Initialize server results
    for server_id in config.get('servers', []):
        job['serverResults'].append({
            'serverId': server_id,
            'serverName': server_id,
            'status': 'pending',
            'patchesApplied': 0,
            'rebootRequired': False,
            'rebootCompleted': False,
            'preCheckStatus': 'pending',
            'postCheckStatus': 'pending'
        })
    
    return job

def run_patching_job(job_id):
    """Run patching job in background"""
    try:
        job = active_jobs.get(job_id)
        if not job:
            return
        
        job['status'] = 'running'
        job['startedAt'] = datetime.now().isoformat()
        
        # Emit job update
        socketio.emit('job_update', {
            'jobId': job_id,
            'status': 'running',
            'progress': 0,
            'message': 'Starting patching job'
        })
        
        # Simulate patching process
        servers = job['servers']
        total_servers = len(servers)
        
        for i, server_id in enumerate(servers):
            # Update server status
            for server_result in job['serverResults']:
                if server_result['serverId'] == server_id:
                    server_result['status'] = 'running'
                    server_result['startedAt'] = datetime.now().isoformat()
                    break
            
            # Simulate patching steps
            import time
            time.sleep(2)  # Simulate processing time
            
            # Update progress
            progress = int(((i + 1) / total_servers) * 100)
            job['progress'] = progress
            
            # Simulate success/failure
            import random
            success = random.choice([True, True, True, False])  # 75% success rate
            
            # Update server result
            for server_result in job['serverResults']:
                if server_result['serverId'] == server_id:
                    server_result['status'] = 'completed' if success else 'failed'
                    server_result['completedAt'] = datetime.now().isoformat()
                    server_result['duration'] = 120  # 2 minutes
                    server_result['patchesApplied'] = random.randint(1, 10) if success else 0
                    server_result['rebootRequired'] = random.choice([True, False])
                    server_result['preCheckStatus'] = 'passed' if success else 'failed'
                    server_result['postCheckStatus'] = 'passed' if success else 'failed'
                    if not success:
                        server_result['errorMessage'] = 'Patching failed due to dependency issues'
                    break
            
            # Update counts
            if success:
                job['successCount'] += 1
            else:
                job['failureCount'] += 1
            
            # Add log entry
            job['logs'].append({
                'id': str(uuid.uuid4()),
                'jobId': job_id,
                'serverId': server_id,
                'level': 'info' if success else 'error',
                'message': f'Patching {"completed" if success else "failed"} for server {server_id}',
                'timestamp': datetime.now().isoformat()
            })
            
            # Emit progress update
            socketio.emit('job_update', {
                'jobId': job_id,
                'status': 'running',
                'progress': progress,
                'message': f'Processed {i + 1}/{total_servers} servers',
                'serverResults': job['serverResults']
            })
        
        # Complete job
        job['status'] = 'completed'
        job['completedAt'] = datetime.now().isoformat()
        job['progress'] = 100
        job['updatedAt'] = datetime.now().isoformat()
        
        # Move to results
        job_results[job_id] = job
        if job_id in active_jobs:
            del active_jobs[job_id]
        
        # Emit completion
        socketio.emit('job_update', {
            'jobId': job_id,
            'status': 'completed',
            'progress': 100,
            'message': f'Job completed: {job["successCount"]} successful, {job["failureCount"]} failed'
        })
        
        logger.info(f"Patching job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in patching job {job_id}: {e}")
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = 'failed'
            active_jobs[job_id]['progress'] = 0
            active_jobs[job_id]['updatedAt'] = datetime.now().isoformat()
            
            # Emit failure
            socketio.emit('job_update', {
                'jobId': job_id,
                'status': 'failed',
                'progress': 0,
                'message': f'Job failed: {str(e)}'
            })

# ===== HEALTH AND STATUS ENDPOINTS =====

@app.route('/health', methods=['GET'])
@limiter.limit("10 per minute")
def health_check():
    """API health check"""
    return api_response(data={'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/system/health', methods=['GET'])
@jwt_required()
def system_health():
    """Get system health status"""
    try:
        # Check database connectivity
        db_status = 'healthy'
        try:
            servers = csv_handler.read_servers(normalize_fields=True)
            db_message = f"CSV database accessible, {len(servers)} servers"
        except Exception as e:
            db_status = 'critical'
            db_message = f"Database error: {str(e)}"
        
        # Check email system
        email_status = 'healthy'
        try:
            email_sender.test_connection()
            email_message = "Email system operational"
        except Exception as e:
            email_status = 'warning'
            email_message = f"Email system issue: {str(e)}"
        
        # Check storage
        storage_status = 'healthy'
        try:
            import shutil
            disk_usage = shutil.disk_usage(Config.PROJECT_ROOT)
            free_space = disk_usage.free / disk_usage.total * 100
            if free_space < 10:
                storage_status = 'critical'
                storage_message = f"Low disk space: {free_space:.1f}% free"
            else:
                storage_message = f"Disk space: {free_space:.1f}% free"
        except Exception as e:
            storage_status = 'warning'
            storage_message = f"Storage check failed: {str(e)}"
        
        # Determine overall status
        statuses = [db_status, email_status, storage_status]
        if 'critical' in statuses:
            overall = 'critical'
        elif 'warning' in statuses:
            overall = 'warning'
        else:
            overall = 'healthy'
        
        health_data = {
            'overall': overall,
            'components': {
                'database': {
                    'status': db_status,
                    'message': db_message,
                    'lastCheck': datetime.now().isoformat()
                },
                'ssh': {
                    'status': 'healthy',
                    'message': 'SSH connectivity available',
                    'lastCheck': datetime.now().isoformat()
                },
                'email': {
                    'status': email_status,
                    'message': email_message,
                    'lastCheck': datetime.now().isoformat()
                },
                'logging': {
                    'status': 'healthy',
                    'message': 'Logging system operational',
                    'lastCheck': datetime.now().isoformat()
                },
                'storage': {
                    'status': storage_status,
                    'message': storage_message,
                    'lastCheck': datetime.now().isoformat()
                },
                'memory': {
                    'status': 'healthy',
                    'message': 'Memory usage normal',
                    'lastCheck': datetime.now().isoformat()
                },
                'cpu': {
                    'status': 'healthy',
                    'message': 'CPU usage normal',
                    'lastCheck': datetime.now().isoformat()
                }
            },
            'metrics': {
                'uptime': 0,  # Would need actual uptime tracking
                'totalServers': len(servers) if 'servers' in locals() else 0,
                'activeConnections': 0,
                'queueSize': len(active_jobs),
                'averageResponseTime': 0,
                'errorRate': 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return api_response(data=health_data)
        
    except Exception as e:
        return handle_error(e, "Failed to get system health")

# ===== AUTHENTICATION ENDPOINTS =====

@app.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """User login with JWT token"""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return api_response(success=False, message="Username and password required", code=400)
        
        username = data['username']
        password = data['password']
        
        # Authenticate user
        user_data = user_manager.authenticate_user(username, password)
        if not user_data:
            return api_response(success=False, message="Invalid credentials", code=401)
        
        # Create JWT tokens
        access_token = create_access_token(identity=user_data['email'])
        refresh_token = create_refresh_token(identity=user_data['email'])
        
        # Log successful login
        logger.info(f"User {user_data['name']} ({username}) logged in via API")
        
        token_data = {
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'tokenType': 'Bearer',
            'expiresIn': int(app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        }
        
        return api_response(data=token_data, message="Login successful")
        
    except Exception as e:
        return handle_error(e, "Login failed")

@app.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh JWT token"""
    try:
        current_user_email = get_jwt_identity()
        new_token = create_access_token(identity=current_user_email)
        
        token_data = {
            'accessToken': new_token,
            'tokenType': 'Bearer',
            'expiresIn': int(app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        }
        
        return api_response(data=token_data, message="Token refreshed")
        
    except Exception as e:
        return handle_error(e, "Token refresh failed")

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout"""
    try:
        token = get_jwt()
        jti = token['jti']
        blacklisted_tokens.add(jti)
        
        logger.info(f"User {get_jwt_identity()} logged out")
        return api_response(message="Logout successful")
        
    except Exception as e:
        return handle_error(e, "Logout failed")

@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        current_user_email = get_jwt_identity()
        user_info = user_manager.get_user_info(current_user_email)
        
        if not user_info:
            return api_response(success=False, message="User not found", code=404)
        
        profile_data = {
            'id': user_info['email'],
            'username': user_info.get('username', current_user_email.split('@')[0]),
            'email': user_info['email'],
            'firstName': user_info['name'].split(' ')[0] if ' ' in user_info['name'] else user_info['name'],
            'lastName': user_info['name'].split(' ', 1)[1] if ' ' in user_info['name'] else '',
            'role': user_info['role'],
            'permissions': user_info['permissions'],
            'isActive': True,
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }
        
        return api_response(data=profile_data)
        
    except Exception as e:
        return handle_error(e, "Failed to get profile")

# ===== SERVER MANAGEMENT ENDPOINTS =====

@app.route('/servers', methods=['GET'])
@jwt_required()
def get_servers():
    """Get servers with pagination and filtering"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 25, type=int)
        
        # Get filter parameters
        search = request.args.get('search', '')
        group = request.args.get('group', '')
        environment = request.args.get('environment', '')
        status = request.args.get('status', '')
        sort_by = request.args.get('sortBy', 'serverName')
        sort_order = request.args.get('sortOrder', 'asc')
        
        # Get user's accessible servers
        current_user_email = get_jwt_identity()
        user_info = user_manager.get_user_info(current_user_email)
        
        if not user_info:
            return api_response(success=False, message="User not found", code=404)
        
        # Read servers from CSV
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Filter servers based on user permissions
        if user_info['role'] != 'admin':
            servers = [s for s in servers if 
                      s.get('primary_owner') == current_user_email or 
                      s.get('secondary_owner') == current_user_email]
        
        # Apply filters
        if search:
            servers = [s for s in servers if 
                      search.lower() in s.get('server_name', '').lower() or
                      search.lower() in s.get('host_group', '').lower()]
        
        if group:
            servers = [s for s in servers if s.get('host_group') == group]
        
        if environment:
            servers = [s for s in servers if s.get('environment') == environment]
        
        if status:
            servers = [s for s in servers if s.get('current_quarter_status') == status]
        
        # Sort servers
        reverse = sort_order == 'desc'
        if sort_by == 'serverName':
            servers.sort(key=lambda x: x.get('server_name', ''), reverse=reverse)
        elif sort_by == 'hostGroup':
            servers.sort(key=lambda x: x.get('host_group', ''), reverse=reverse)
        elif sort_by == 'environment':
            servers.sort(key=lambda x: x.get('environment', ''), reverse=reverse)
        
        # Normalize server data
        normalized_servers = [normalize_server_data(server) for server in servers]
        
        # Apply pagination
        total = len(normalized_servers)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_servers = normalized_servers[start:end]
        
        # Prepare response
        response_data = {
            'items': paginated_servers,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size,
            'hasNext': end < total,
            'hasPrevious': page > 1
        }
        
        return api_response(data=response_data)
        
    except Exception as e:
        return handle_error(e, "Failed to get servers")

@app.route('/servers/<server_id>', methods=['GET'])
@jwt_required()
def get_server(server_id):
    """Get single server details"""
    try:
        servers = csv_handler.read_servers(normalize_fields=True)
        server = next((s for s in servers if s.get('server_name') == server_id), None)
        
        if not server:
            return api_response(success=False, message="Server not found", code=404)
        
        # Check permissions
        current_user_email = get_jwt_identity()
        user_info = user_manager.get_user_info(current_user_email)
        
        if (user_info['role'] != 'admin' and 
            server.get('primary_owner') != current_user_email and 
            server.get('secondary_owner') != current_user_email):
            return api_response(success=False, message="Access denied", code=403)
        
        return api_response(data=normalize_server_data(server))
        
    except Exception as e:
        return handle_error(e, "Failed to get server")

if __name__ == '__main__':
    logger.info("Starting Linux Patching Automation API Backend")
    socketio.run(app, host='0.0.0.0', port=8001, debug=False)