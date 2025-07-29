#!/usr/bin/env python3
"""
React Patching System - API Backend
Converted from Flask web portal to REST API for React frontend
"""

import os
import sys
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
from functools import wraps

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import existing utilities
from utils.csv_handler import CSVHandler
from utils.timezone_handler import TimezoneHandler
from utils.email_sender import EmailSender
from config.settings import Config
from config.users import UserManager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)

# Initialize handlers
csv_handler = CSVHandler()
timezone_handler = TimezoneHandler()
email_sender = EmailSender()
user_manager = UserManager()

# JWT Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'success': False, 'message': 'Token format invalid'}), 401
        
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = user_manager.get_user_info(data['email'])
            if not current_user:
                return jsonify({'success': False, 'message': 'Token is invalid'}), 401
        except Exception as e:
            return jsonify({'success': False, 'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    
    return decorated

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    """User authentication"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        # Use existing authentication from Flask app
        user_data = user_manager.authenticate_user(username, password)
        
        if user_data:
            token = jwt.encode({
                'email': user_data['email'],
                'exp': datetime.utcnow() + timedelta(hours=8)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'permissions': user_data['permissions'],
                    'auth_method': user_data.get('auth_method', 'local')
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Authentication error: {str(e)}'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get user profile"""
    return jsonify({
        'success': True,
        'user': {
            'email': current_user['email'],
            'name': current_user['name'],
            'role': current_user['role'],
            'permissions': current_user['permissions'],
            'auth_method': current_user.get('auth_method', 'local'),
            'department': current_user.get('department', ''),
            'title': current_user.get('title', '')
        }
    })

# Server management endpoints
@app.route('/api/servers', methods=['GET'])
@token_required
def get_servers(current_user):
    """Get servers list based on user permissions"""
    try:
        # Get servers based on user role
        if current_user['role'] == 'admin':
            servers = csv_handler.read_servers(normalize_fields=True)
        else:
            # Filter servers for non-admin users
            all_servers = csv_handler.read_servers(normalize_fields=True)
            servers = []
            for server in all_servers:
                if (server.get('primary_owner') == current_user['email'] or 
                    server.get('secondary_owner') == current_user['email']):
                    servers.append(server)
        
        # Convert to React-friendly format
        formatted_servers = []
        for server in servers:
            formatted_server = {
                'id': server.get('server_name', ''),
                'serverName': server.get('server_name', ''),
                'hostGroup': server.get('host_group', ''),
                'environment': server.get('environment', ''),
                'primaryOwner': server.get('primary_owner', ''),
                'secondaryOwner': server.get('secondary_owner', ''),
                'location': server.get('location', ''),
                'incidentTicket': server.get('incident_ticket', ''),
                'patcherEmail': server.get('patcher_email', ''),
                'serverTimezone': server.get('server_timezone', ''),
                'operatingSystem': server.get('operating_system', ''),
                'q1PatchDate': server.get('q1_patch_date', ''),
                'q1PatchTime': server.get('q1_patch_time', ''),
                'q1ApprovalStatus': server.get('q1_approval_status', 'Pending'),
                'q2PatchDate': server.get('q2_patch_date', ''),
                'q2PatchTime': server.get('q2_patch_time', ''),
                'q2ApprovalStatus': server.get('q2_approval_status', 'Pending'),
                'q3PatchDate': server.get('q3_patch_date', ''),
                'q3PatchTime': server.get('q3_patch_time', ''),
                'q3ApprovalStatus': server.get('q3_approval_status', 'Pending'),
                'q4PatchDate': server.get('q4_patch_date', ''),
                'q4PatchTime': server.get('q4_patch_time', ''),
                'q4ApprovalStatus': server.get('q4_approval_status', 'Pending'),
                'currentQuarterStatus': server.get('current_quarter_status', 'Pending')
            }
            formatted_servers.append(formatted_server)
        
        return jsonify({
            'success': True,
            'data': formatted_servers,
            'total': len(formatted_servers),
            'currentQuarter': Config.get_current_quarter()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error retrieving servers: {str(e)}'}), 500

@app.route('/api/servers/<server_name>', methods=['GET'])
@token_required
def get_server(current_user, server_name):
    """Get individual server details"""
    try:
        servers = csv_handler.read_servers(normalize_fields=True)
        server = None
        
        for s in servers:
            if s.get('server_name') == server_name:
                # Check permissions
                if (current_user['role'] == 'admin' or 
                    s.get('primary_owner') == current_user['email'] or 
                    s.get('secondary_owner') == current_user['email']):
                    server = s
                    break
        
        if not server:
            return jsonify({'success': False, 'message': 'Server not found or access denied'}), 404
        
        # Format server data
        formatted_server = {
            'id': server.get('server_name', ''),
            'serverName': server.get('server_name', ''),
            'hostGroup': server.get('host_group', ''),
            'environment': server.get('environment', ''),
            'primaryOwner': server.get('primary_owner', ''),
            'secondaryOwner': server.get('secondary_owner', ''),
            'location': server.get('location', ''),
            'incidentTicket': server.get('incident_ticket', ''),
            'patcherEmail': server.get('patcher_email', ''),
            'serverTimezone': server.get('server_timezone', ''),
            'operatingSystem': server.get('operating_system', ''),
            'q1PatchDate': server.get('q1_patch_date', ''),
            'q1PatchTime': server.get('q1_patch_time', ''),
            'q1ApprovalStatus': server.get('q1_approval_status', 'Pending'),
            'q2PatchDate': server.get('q2_patch_date', ''),
            'q2PatchTime': server.get('q2_patch_time', ''),
            'q2ApprovalStatus': server.get('q2_approval_status', 'Pending'),
            'q3PatchDate': server.get('q3_patch_date', ''),
            'q3PatchTime': server.get('q3_patch_time', ''),
            'q3ApprovalStatus': server.get('q3_approval_status', 'Pending'),
            'q4PatchDate': server.get('q4_patch_date', ''),
            'q4PatchTime': server.get('q4_patch_time', ''),
            'q4ApprovalStatus': server.get('q4_approval_status', 'Pending'),
            'currentQuarterStatus': server.get('current_quarter_status', 'Pending')
        }
        
        return jsonify({
            'success': True,
            'data': formatted_server,
            'currentQuarter': Config.get_current_quarter(),
            'quarters': Config.QUARTERS
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error retrieving server: {str(e)}'}), 500

@app.route('/api/servers/<server_name>/schedule', methods=['PUT'])
@token_required
def update_server_schedule(current_user, server_name):
    """Update server patching schedule"""
    try:
        data = request.get_json()
        quarter = data.get('quarter')
        patch_date = data.get('patchDate')
        patch_time = data.get('patchTime')
        
        if not all([quarter, patch_date, patch_time]):
            return jsonify({'success': False, 'message': 'Quarter, patch date, and time required'}), 400
        
        # Check freeze period (reusing Flask logic)
        if is_freeze_period(patch_date):
            return jsonify({
                'success': False, 
                'message': 'Cannot modify schedule for current week (Thursday to Tuesday). You can only modify schedules for next week onwards.'
            }), 400
        
        # Update CSV
        servers = csv_handler.read_servers(normalize_fields=True)
        updated = False
        
        for server in servers:
            if server.get('server_name') == server_name:
                # Check permission
                can_modify = (current_user['role'] == 'admin' or 
                             server.get('primary_owner') == current_user['email'] or 
                             server.get('secondary_owner') == current_user['email'])
                
                if can_modify:
                    server[f'q{quarter}_patch_date'] = patch_date
                    server[f'q{quarter}_patch_time'] = patch_time
                    
                    # If updating current quarter, update status
                    if quarter == Config.get_current_quarter():
                        server['current_quarter_status'] = 'Scheduled'
                    
                    updated = True
                    break
        
        if updated:
            csv_handler.write_servers(servers)
            return jsonify({'success': True, 'message': 'Schedule updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update schedule - access denied'}), 403
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating schedule: {str(e)}'}), 500

@app.route('/api/servers/<server_name>/approve', methods=['POST'])
@token_required
def approve_server_schedule(current_user, server_name):
    """Approve server patching schedule"""
    try:
        data = request.get_json()
        quarter = data.get('quarter', Config.get_current_quarter())
        
        # Update CSV
        servers = csv_handler.read_servers(normalize_fields=True)
        updated = False
        
        for server in servers:
            if server.get('server_name') == server_name:
                # Check permission
                can_approve = (current_user['role'] == 'admin' or 
                              server.get('primary_owner') == current_user['email'] or 
                              server.get('secondary_owner') == current_user['email'])
                
                if can_approve:
                    server[f'q{quarter}_approval_status'] = 'Approved'
                    
                    # Update patching status if current quarter
                    if quarter == Config.get_current_quarter():
                        server['current_quarter_status'] = 'Approved'
                    
                    updated = True
                    break
        
        if updated:
            csv_handler.write_servers(servers)
            
            # Send approval confirmation email (reusing Flask logic)
            try:
                send_approval_confirmation(server, quarter)
            except Exception as email_error:
                print(f"Warning: Failed to send approval confirmation email: {email_error}")
            
            return jsonify({'success': True, 'message': f'Schedule approved successfully for Q{quarter}'})
        else:
            return jsonify({'success': False, 'message': 'Failed to approve schedule - access denied'}), 403
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error approving schedule: {str(e)}'}), 500

@app.route('/api/servers/<server_name>/info', methods=['PUT'])
@token_required
def update_server_info(current_user, server_name):
    """Update server incident ticket and patcher email (admin only)"""
    try:
        data = request.get_json()
        incident_ticket = data.get('incidentTicket', '').strip()
        patcher_email = data.get('patcherEmail', '').strip()
        
        # Check permissions for incident tickets and patcher emails
        if incident_ticket and not user_manager.user_has_permission(current_user['email'], 'update_incident_tickets'):
            return jsonify({'success': False, 'message': 'Only administrators can modify incident tickets'}), 403
        
        if patcher_email and not user_manager.user_has_permission(current_user['email'], 'update_patcher_emails'):
            return jsonify({'success': False, 'message': 'Only administrators can modify patcher emails'}), 403
        
        # Update CSV
        servers = csv_handler.read_servers(normalize_fields=True)
        updated = False
        
        for server in servers:
            if server.get('server_name') == server_name:
                # Check if user can access this server
                can_access = (current_user['role'] == 'admin' or 
                             server.get('primary_owner') == current_user['email'] or 
                             server.get('secondary_owner') == current_user['email'])
                
                if can_access:
                    if incident_ticket and user_manager.user_has_permission(current_user['email'], 'update_incident_tickets'):
                        server['incident_ticket'] = incident_ticket
                    if patcher_email and user_manager.user_has_permission(current_user['email'], 'update_patcher_emails'):
                        server['patcher_email'] = patcher_email
                    
                    updated = True
                    break
        
        if updated:
            csv_handler.write_servers(servers)
            return jsonify({'success': True, 'message': 'Server information updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update server information'}), 403
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating server information: {str(e)}'}), 500

# Helper functions (reused from Flask app)
def is_freeze_period(patch_date=None):
    """Check if we're in the freeze period for a given patch date"""
    today = datetime.now().date()
    current_weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    # If no specific patch date provided, use general freeze logic
    if patch_date is None:
        # Current week freeze: Thursday (3) through Tuesday (1) of next week
        return current_weekday in [3, 4, 5, 6, 0, 1]
    
    # Convert patch_date to date object if it's a string
    if isinstance(patch_date, str):
        try:
            patch_date = datetime.strptime(patch_date, '%Y-%m-%d').date()
        except:
            return True  # If invalid date, err on side of caution
    
    # Calculate which week the patch date is in
    days_until_patch = (patch_date - today).days
    
    # If patch is in the current week (this week's Thursday onwards), freeze it
    if days_until_patch < 0:
        return True  # Past dates are frozen
    
    # Find next Thursday from today
    days_until_next_thursday = (3 - current_weekday) % 7
    if days_until_next_thursday == 0 and current_weekday >= 3:
        days_until_next_thursday = 7  # If today is Thursday or later, next Thursday is next week
    
    next_thursday = today + timedelta(days=days_until_next_thursday)
    
    # If patch date is before next Thursday, it's in current week - freeze it
    if patch_date < next_thursday:
        return True
    
    # If patch date is in next week or later, allow changes
    return False

def send_approval_confirmation(server, quarter):
    """Send approval confirmation email (reused from Flask app)"""
    try:
        # Load the approval confirmation template
        template_path = f'{Config.TEMPLATES_DIR}/approval_confirmation.html'
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Get quarter information
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        quarter_description = quarter_descriptions.get(quarter, 'Unknown')
        
        # Generate server table for the approved server
        server_table = generate_approval_confirmation_table([server], quarter)
        
        # Get current date for approval timestamp
        approval_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare email data
        email_data = {
            'quarter': quarter_name,
            'quarter_description': quarter_description,
            'server_table': server_table,
            'incident_ticket': server.get('incident_ticket', 'Not set'),
            'patcher_email': server.get('patcher_email', 'Not set'),
            'approval_date': approval_date
        }
        
        # Send to primary owner
        primary_owner = server.get('primary_owner')
        if primary_owner:
            email_content = template.format(owner_email=primary_owner, **email_data)
            subject = f"✅ APPROVED: {quarter_name} Patching Schedule Confirmed - {server['server_name']}"
            email_sender.send_email(primary_owner, subject, email_content, is_html=True)
        
        # Send to secondary owner if exists
        secondary_owner = server.get('secondary_owner')
        if secondary_owner and secondary_owner != primary_owner:
            email_content = template.format(owner_email=secondary_owner, **email_data)
            subject = f"✅ APPROVED: {quarter_name} Patching Schedule Confirmed - {server['server_name']}"
            email_sender.send_email(secondary_owner, subject, email_content, is_html=True)
            
    except Exception as e:
        print(f"Error sending approval confirmation: {e}")
        raise

def generate_approval_confirmation_table(servers_list, quarter):
    """Generate HTML table for approval confirmation"""
    table_rows = ""
    for server in servers_list:
        # Get patch date and time for the specified quarter
        patch_date = server.get(f'q{quarter}_patch_date', 'Not Set')
        patch_time = server.get(f'q{quarter}_patch_time', 'Not Set')
        approval_status = server.get(f'q{quarter}_approval_status', 'Approved')
        
        table_rows += f"""
        <tr>
            <td>{server['server_name']}</td>
            <td>{patch_date}</td>
            <td>{patch_time}</td>
            <td>{server['server_timezone']}</td>
            <td><span style="color: #28a745; font-weight: bold;">{approval_status}</span></td>
            <td><span style="color: #0056b3; font-weight: bold;">{server.get('primary_owner', 'Not Set')}</span></td>
            <td>{server.get('secondary_owner', 'Not Set') if server.get('secondary_owner') else '<em>Not Set</em>'}</td>
            <td>{server.get('incident_ticket', 'Not Set')}</td>
            <td>{server.get('location', '')}</td>
        </tr>
        """
    
    return f"""
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f2f2f2;">
            <th>Server Name</th>
            <th>Patch Date</th>
            <th>Patch Time</th>
            <th>Timezone</th>
            <th>Approval Status</th>
            <th>Primary Owner</th>
            <th>Secondary Owner</th>
            <th>Incident Ticket</th>
            <th>Location</th>
        </tr>
        {table_rows}
    </table>
    """

# Import and register blueprints
from routes.admin import admin_bp
from routes.reports import reports_bp
from routes.utils import utils_bp

# Register blueprints with token_required decorator applied
from functools import wraps

def apply_token_required_to_blueprint(blueprint):
    """Apply token_required decorator to all routes in a blueprint"""
    for endpoint, view_func in blueprint.view_functions.items():
        if not getattr(view_func, '_token_required_applied', False):
            # Apply token_required and admin_required if needed
            if 'admin' in endpoint:
                decorated_func = token_required(admin_required(view_func))
            else:
                decorated_func = token_required(view_func)
            decorated_func._token_required_applied = True
            blueprint.view_functions[endpoint] = decorated_func

# Apply decorators to blueprints
apply_token_required_to_blueprint(admin_bp)
apply_token_required_to_blueprint(reports_bp)
apply_token_required_to_blueprint(utils_bp)

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(utils_bp)

# Health check endpoint (no auth required)
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'React Patching System API'
    })

# CORS preflight handler
@app.before_request
def handle_preflight():
    from flask import request
    if request.method == "OPTIONS":
        response = jsonify({'status': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

if __name__ == '__main__':
    print("Starting React Patching System API Backend...")
    print("Available endpoints:")
    print("- Authentication: /api/auth/login, /api/auth/profile")
    print("- Servers: /api/servers, /api/servers/<name>, /api/servers/<name>/schedule")
    print("- Admin: /api/admin/* (admin only)")
    print("- Reports: /api/reports/* (various reporting endpoints)")
    print("- Utils: /api/utils/* (timezone, AI recommendations, system health)")
    print("- Health: /api/health")
    print(f"Server starting on port 8002...")
    app.run(host='0.0.0.0', port=8002, debug=False)