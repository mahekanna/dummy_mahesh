"""
Server Management Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.csv_handler import CSVHandler
from utils.ssh_manager import SSHManager
from backend_api.utils.pagination import paginate_results
from backend_api.utils.audit import log_audit_event
from backend_api.utils.validators import validate_server_data
from backend_api.decorators import require_permission

servers_bp = Blueprint('servers', __name__)
csv_handler = CSVHandler()
ssh_manager = SSHManager()

@servers_bp.route('', methods=['GET'])
@jwt_required()
@require_permission('servers.view')
def get_servers():
    """Get all servers with pagination and filtering"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        search = request.args.get('search', '')
        group = request.args.get('group')
        environment = request.args.get('environment')
        status = request.args.get('status')
        sort_by = request.args.get('sortBy', 'server_name')
        sort_order = request.args.get('sortOrder', 'asc')
        
        # Read all servers
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Apply filters
        filtered_servers = []
        for server in servers:
            # Search filter
            if search:
                search_lower = search.lower()
                if not any(search_lower in str(v).lower() for v in server.values()):
                    continue
            
            # Group filter
            if group and server.get('host_group') != group:
                continue
            
            # Environment filter (map from data if available)
            if environment:
                # You might need to add environment field to CSV
                pass
            
            # Status filter
            if status and server.get('active_status') != status:
                continue
            
            filtered_servers.append(server)
        
        # Sort servers
        reverse = sort_order == 'desc'
        filtered_servers.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
        
        # Paginate results
        paginated = paginate_results(filtered_servers, page, page_size)
        
        # Transform to API format
        items = []
        for server in paginated['items']:
            items.append(transform_server_to_api(server))
        
        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'total': paginated['total'],
                'page': paginated['page'],
                'pageSize': paginated['page_size'],
                'totalPages': paginated['total_pages'],
                'hasNext': paginated['has_next'],
                'hasPrevious': paginated['has_previous']
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get servers: {str(e)}'
        }), 500

@servers_bp.route('/<server_id>', methods=['GET'])
@jwt_required()
@require_permission('servers.view')
def get_server(server_id):
    """Get server by ID (server name)"""
    try:
        servers = csv_handler.read_servers(normalize_fields=True)
        
        server = None
        for s in servers:
            if s.get('server_name') == server_id:
                server = s
                break
        
        if not server:
            return jsonify({
                'success': False,
                'message': 'Server not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': transform_server_to_api(server),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get server: {str(e)}'
        }), 500

@servers_bp.route('', methods=['POST'])
@jwt_required()
@require_permission('servers.create')
def create_server():
    """Create new server"""
    try:
        data = request.get_json()
        identity = get_jwt_identity()
        
        # Validate input
        is_valid, errors = validate_server_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Check if server already exists
        servers = csv_handler.read_servers(normalize_fields=True)
        if any(s.get('server_name') == data.get('serverName') for s in servers):
            return jsonify({
                'success': False,
                'message': 'Server already exists'
            }), 409
        
        # Create new server entry
        new_server = transform_api_to_server(data)
        new_server['created_date'] = datetime.utcnow().isoformat()
        new_server['modified_date'] = datetime.utcnow().isoformat()
        
        # Add to servers list
        servers.append(new_server)
        csv_handler.write_servers(servers)
        
        # Log audit event
        log_audit_event(
            action='server_created',
            resource='servers',
            resource_id=new_server['server_name'],
            user_id=identity,
            details={'server': new_server['server_name']}
        )
        
        return jsonify({
            'success': True,
            'data': transform_server_to_api(new_server),
            'message': 'Server created successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to create server: {str(e)}'
        }), 500

@servers_bp.route('/<server_id>', methods=['PUT'])
@jwt_required()
@require_permission('servers.update')
def update_server(server_id):
    """Update server"""
    try:
        data = request.get_json()
        identity = get_jwt_identity()
        
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Find server
        server_index = None
        for i, s in enumerate(servers):
            if s.get('server_name') == server_id:
                server_index = i
                break
        
        if server_index is None:
            return jsonify({
                'success': False,
                'message': 'Server not found'
            }), 404
        
        # Update server
        update_data = transform_api_to_server(data)
        servers[server_index].update(update_data)
        servers[server_index]['modified_date'] = datetime.utcnow().isoformat()
        
        # Save changes
        csv_handler.write_servers(servers)
        
        # Log audit event
        log_audit_event(
            action='server_updated',
            resource='servers',
            resource_id=server_id,
            user_id=identity,
            details={'updates': list(update_data.keys())}
        )
        
        return jsonify({
            'success': True,
            'data': transform_server_to_api(servers[server_index]),
            'message': 'Server updated successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update server: {str(e)}'
        }), 500

@servers_bp.route('/<server_id>', methods=['DELETE'])
@jwt_required()
@require_permission('servers.delete')
def delete_server(server_id):
    """Delete server"""
    try:
        identity = get_jwt_identity()
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Filter out the server to delete
        original_count = len(servers)
        servers = [s for s in servers if s.get('server_name') != server_id]
        
        if len(servers) == original_count:
            return jsonify({
                'success': False,
                'message': 'Server not found'
            }), 404
        
        # Save changes
        csv_handler.write_servers(servers)
        
        # Log audit event
        log_audit_event(
            action='server_deleted',
            resource='servers',
            resource_id=server_id,
            user_id=identity
        )
        
        return jsonify({
            'success': True,
            'message': 'Server deleted successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to delete server: {str(e)}'
        }), 500

@servers_bp.route('/<server_id>/test', methods=['POST'])
@jwt_required()
@require_permission('servers.update')
def test_server_connectivity(server_id):
    """Test server connectivity"""
    try:
        import time
        start_time = time.time()
        
        # Test SSH connection
        connected = ssh_manager.test_connection(server_id)
        response_time = int((time.time() - start_time) * 1000)  # Convert to ms
        
        message = 'Connection successful' if connected else 'Connection failed'
        
        return jsonify({
            'success': True,
            'data': {
                'connected': connected,
                'message': message,
                'responseTime': response_time
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to test connectivity: {str(e)}'
        }), 500

def transform_server_to_api(server):
    """Transform CSV server data to API format"""
    return {
        'id': server.get('server_name'),
        'serverName': server.get('server_name'),
        'hostGroup': server.get('host_group'),
        'operatingSystem': server.get('operating_system', 'unknown'),
        'environment': server.get('environment', 'production'),
        'serverTimezone': server.get('server_timezone'),
        'location': server.get('location', ''),
        'primaryOwner': server.get('primary_owner'),
        'secondaryOwner': server.get('secondary_owner'),
        'primaryLinuxUser': server.get('primary_linux_user', 'root'),
        'secondaryLinuxUser': server.get('secondary_linux_user'),
        'patcherEmail': server.get('patcher_email'),
        'engineeringDomain': server.get('engineering_domain'),
        'incidentTicket': server.get('incident_ticket'),
        
        # Patching Schedule
        'q1PatchDate': server.get('q1_patch_date'),
        'q1PatchTime': server.get('q1_patch_time'),
        'q1ApprovalStatus': server.get('q1_approval_status', 'pending'),
        'q2PatchDate': server.get('q2_patch_date'),
        'q2PatchTime': server.get('q2_patch_time'),
        'q2ApprovalStatus': server.get('q2_approval_status', 'pending'),
        'q3PatchDate': server.get('q3_patch_date'),
        'q3PatchTime': server.get('q3_patch_time'),
        'q3ApprovalStatus': server.get('q3_approval_status', 'pending'),
        'q4PatchDate': server.get('q4_patch_date'),
        'q4PatchTime': server.get('q4_patch_time'),
        'q4ApprovalStatus': server.get('q4_approval_status', 'pending'),
        
        # Status
        'currentQuarterPatchingStatus': server.get('current_quarter_status', 'pending'),
        'activeStatus': server.get('active_status', 'active'),
        'lastSyncDate': server.get('last_sync_date'),
        'syncStatus': server.get('sync_status', 'success'),
        
        # SSH Configuration
        'sshPort': int(server.get('ssh_port', 22)),
        'sudoUser': server.get('sudo_user'),
        
        # Patching Configuration
        'backupRequired': server.get('backup_required', 'true').lower() == 'true',
        'rollbackPlan': server.get('rollback_plan'),
        'criticalServices': server.get('critical_services', '').split(',') if server.get('critical_services') else [],
        'maintenanceWindow': server.get('maintenance_window'),
        'patchGroupPriority': int(server.get('patch_group_priority', 1)),
        'autoApprove': server.get('auto_approve', 'false').lower() == 'true',
        'notificationEmail': server.get('notification_email'),
        
        # Timestamps
        'createdDate': server.get('created_date', ''),
        'modifiedDate': server.get('modified_date', '')
    }

def transform_api_to_server(data):
    """Transform API data to CSV server format"""
    return {
        'server_name': data.get('serverName'),
        'host_group': data.get('hostGroup'),
        'operating_system': data.get('operatingSystem'),
        'environment': data.get('environment'),
        'server_timezone': data.get('serverTimezone'),
        'location': data.get('location'),
        'primary_owner': data.get('primaryOwner'),
        'secondary_owner': data.get('secondaryOwner'),
        'primary_linux_user': data.get('primaryLinuxUser'),
        'secondary_linux_user': data.get('secondaryLinuxUser'),
        'patcher_email': data.get('patcherEmail'),
        'engineering_domain': data.get('engineeringDomain'),
        'incident_ticket': data.get('incidentTicket'),
        'ssh_port': str(data.get('sshPort', 22)),
        'sudo_user': data.get('sudoUser'),
        'backup_required': 'true' if data.get('backupRequired') else 'false',
        'rollback_plan': data.get('rollbackPlan'),
        'critical_services': ','.join(data.get('criticalServices', [])),
        'maintenance_window': data.get('maintenanceWindow'),
        'patch_group_priority': str(data.get('patchGroupPriority', 1)),
        'auto_approve': 'true' if data.get('autoApprove') else 'false',
        'notification_email': data.get('notificationEmail')
    }