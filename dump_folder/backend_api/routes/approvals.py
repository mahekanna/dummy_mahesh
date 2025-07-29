"""
Approval Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid

approvals_bp = Blueprint('approvals', __name__)

# Mock approval data storage
approvals_data = {}

@approvals_bp.route('', methods=['GET'])
@jwt_required()
def get_approval_requests():
    """Get approval requests"""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        
        # Get all approvals
        approvals = list(approvals_data.values())
        
        # Sort by request date (newest first)
        approvals.sort(key=lambda x: x.get('requestDate', ''), reverse=True)
        
        # Basic pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_approvals = approvals[start:end]
        
        return jsonify({
            'success': True,
            'data': {
                'items': paginated_approvals,
                'total': len(approvals),
                'page': page,
                'pageSize': page_size,
                'totalPages': (len(approvals) + page_size - 1) // page_size,
                'hasNext': end < len(approvals),
                'hasPrevious': page > 1
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get approval requests: {str(e)}'
        }), 500

@approvals_bp.route('', methods=['POST'])
@jwt_required()
def create_approval_request():
    """Create approval request"""
    try:
        data = request.get_json()
        identity = get_jwt_identity()
        
        # Create new approval request
        approval_id = str(uuid.uuid4())
        approval = {
            'id': approval_id,
            'serverId': data.get('serverId'),
            'serverName': data.get('serverName'),
            'quarter': data.get('quarter'),
            'requestedBy': identity,
            'requestDate': datetime.utcnow().isoformat(),
            'status': 'pending',
            'approvalType': 'individual',
            'businessJustification': data.get('businessJustification'),
            'riskAssessment': data.get('riskAssessment'),
            'rollbackPlan': data.get('rollbackPlan'),
            'notificationList': data.get('notificationList', []),
            'emergencyContact': data.get('emergencyContact'),
            'maintenanceWindow': data.get('maintenanceWindow'),
            'dependencies': data.get('dependencies', []),
            'testingRequired': data.get('testingRequired', False),
            'backupRequired': data.get('backupRequired', False),
            'changeRequestId': data.get('changeRequestId'),
            'comments': data.get('comments'),
            'autoApproved': False,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Store approval
        approvals_data[approval_id] = approval
        
        return jsonify({
            'success': True,
            'data': approval,
            'message': 'Approval request created successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to create approval request: {str(e)}'
        }), 500

@approvals_bp.route('/approve', methods=['POST'])
@jwt_required()
def approve_servers():
    """Approve servers"""
    try:
        data = request.get_json()
        identity = get_jwt_identity()
        
        approval_ids = data.get('approval_ids', [])
        comment = data.get('comment', '')
        
        updated_approvals = []
        
        for approval_id in approval_ids:
            if approval_id in approvals_data:
                approval = approvals_data[approval_id]
                approval['status'] = 'approved'
                approval['approver'] = identity
                approval['approvalDate'] = datetime.utcnow().isoformat()
                approval['comments'] = comment
                approval['updatedAt'] = datetime.utcnow().isoformat()
                updated_approvals.append(approval)
        
        return jsonify({
            'success': True,
            'data': updated_approvals,
            'message': f'Approved {len(updated_approvals)} servers',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to approve servers: {str(e)}'
        }), 500

@approvals_bp.route('/reject', methods=['POST'])
@jwt_required()
def reject_servers():
    """Reject servers"""
    try:
        data = request.get_json()
        identity = get_jwt_identity()
        
        approval_ids = data.get('approval_ids', [])
        reason = data.get('reason', '')
        
        updated_approvals = []
        
        for approval_id in approval_ids:
            if approval_id in approvals_data:
                approval = approvals_data[approval_id]
                approval['status'] = 'rejected'
                approval['approver'] = identity
                approval['approvalDate'] = datetime.utcnow().isoformat()
                approval['comments'] = reason
                approval['updatedAt'] = datetime.utcnow().isoformat()
                updated_approvals.append(approval)
        
        return jsonify({
            'success': True,
            'data': updated_approvals,
            'message': f'Rejected {len(updated_approvals)} servers',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to reject servers: {str(e)}'
        }), 500