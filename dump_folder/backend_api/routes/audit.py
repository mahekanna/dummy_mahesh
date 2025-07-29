"""
Audit Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        action = request.args.get('action')
        user = request.args.get('user')
        
        # Build filters
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if action:
            filters['action'] = action
        if user:
            filters['user_id'] = user
        
        # Get audit logs
        from backend_api.utils.audit import get_audit_logs
        result = get_audit_logs(page, page_size, filters)
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get audit logs: {str(e)}'
        }), 500