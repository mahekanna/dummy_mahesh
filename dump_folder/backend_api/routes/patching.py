"""
Patching Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
import os
from datetime import datetime
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.csv_handler import CSVHandler
from config.settings import Config
from backend_api.utils.pagination import paginate_results
from backend_api.utils.audit import log_audit_event
from backend_api.decorators import require_permission

patching_bp = Blueprint('patching', __name__)
csv_handler = CSVHandler()

# In-memory job storage (in production, use Redis or database)
patching_jobs = {}

@patching_bp.route('/status', methods=['GET'])
@jwt_required()
@require_permission('patching.view')
def get_patching_status():
    """Get overall patching status"""
    try:
        quarter = request.args.get('quarter', Config.get_current_quarter())
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Calculate statistics
        total_servers = len(servers)
        pending_approval = 0
        approved = 0
        scheduled = 0
        in_progress = 0
        completed = 0
        failed = 0
        rolled_back = 0
        
        quarterly_stats = {}
        group_stats = {}
        
        for server in servers:
            # Current quarter status
            status = server.get('current_quarter_status', 'pending')
            approval_status = server.get(f'q{quarter}_approval_status', 'pending')
            
            if approval_status == 'pending':
                pending_approval += 1
            elif approval_status in ['approved', 'auto_approved']:
                approved += 1
            
            if status == 'scheduled':
                scheduled += 1
            elif status == 'in_progress':
                in_progress += 1
            elif status == 'completed':
                completed += 1
            elif status == 'failed':
                failed += 1
            elif status == 'rolled_back':
                rolled_back += 1
            
            # Group statistics
            group = server.get('host_group', 'unknown')
            if group not in group_stats:
                group_stats[group] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'pending': 0,
                    'successRate': 0
                }
            
            group_stats[group]['total'] += 1
            if status == 'completed':
                group_stats[group]['completed'] += 1
            elif status == 'failed':
                group_stats[group]['failed'] += 1
            else:
                group_stats[group]['pending'] += 1
        
        # Calculate success rate
        success_rate = (completed / total_servers * 100) if total_servers > 0 else 0
        
        # Calculate group success rates
        for group in group_stats:
            stats = group_stats[group]
            if stats['total'] > 0:
                stats['successRate'] = (stats['completed'] / stats['total'] * 100)
        
        # Calculate quarterly statistics
        for q in ['1', '2', '3', '4']:
            quarterly_stats[q] = {
                'total': total_servers,
                'completed': 0,
                'failed': 0,
                'pending': 0,
                'successRate': 0
            }
            
            for server in servers:
                status = server.get(f'q{q}_approval_status', 'pending')
                if status == 'completed':
                    quarterly_stats[q]['completed'] += 1
                elif status == 'failed':
                    quarterly_stats[q]['failed'] += 1
                else:
                    quarterly_stats[q]['pending'] += 1
            
            if quarterly_stats[q]['total'] > 0:
                quarterly_stats[q]['successRate'] = (
                    quarterly_stats[q]['completed'] / quarterly_stats[q]['total'] * 100
                )
        
        return jsonify({
            'success': True,
            'data': {
                'currentQuarter': quarter,
                'totalServers': total_servers,
                'pendingApproval': pending_approval,
                'approved': approved,
                'scheduled': scheduled,
                'inProgress': in_progress,
                'completed': completed,
                'failed': failed,
                'rolledBack': rolled_back,
                'successRate': success_rate,
                'activeOperations': len([j for j in patching_jobs.values() if j['status'] == 'running']),
                'lastUpdated': datetime.utcnow().isoformat(),
                'quarterlyStats': quarterly_stats,
                'groupStats': group_stats
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get patching status: {str(e)}'
        }), 500

@patching_bp.route('/start', methods=['POST'])
@jwt_required()
@require_permission('patching.start')
def start_patching():
    """Start patching job"""
    try:
        data = request.get_json()
        identity = get_jwt_identity()
        
        # Validate input
        servers = data.get('servers', [])
        if not servers:
            return jsonify({
                'success': False,
                'message': 'No servers specified'
            }), 400
        
        # Create job
        job_id = str(uuid.uuid4())
        job = {
            'id': job_id,
            'name': data.get('name', f'Patching Job {datetime.now().strftime("%Y-%m-%d %H:%M")}'),
            'description': data.get('description'),
            'type': 'batch' if len(servers) > 1 else 'single',
            'status': 'pending',
            'progress': 0,
            'quarter': data.get('quarter', Config.get_current_quarter()),
            'servers': servers,
            'dryRun': data.get('dryRun', False),
            'force': data.get('force', False),
            'skipPrecheck': data.get('skipPrecheck', False),
            'skipPostcheck': data.get('skipPostcheck', False),
            'startedAt': datetime.utcnow().isoformat(),
            'operator': identity,
            'successCount': 0,
            'failureCount': 0,
            'totalCount': len(servers),
            'serverResults': [],
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            'logs': []
        }
        
        # Store job
        patching_jobs[job_id] = job
        
        # Log audit event
        log_audit_event(
            action='patching_started',
            resource='patching',
            resource_id=job_id,
            user_id=identity,
            details={
                'servers': servers,
                'dry_run': job['dryRun'],
                'force': job['force']
            }
        )
        
        # In a real implementation, you would start the actual patching process here
        # For now, we'll just return the job details
        
        return jsonify({
            'success': True,
            'data': transform_job_to_api(job),
            'message': 'Patching job started successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to start patching: {str(e)}'
        }), 500

@patching_bp.route('/jobs', methods=['GET'])
@jwt_required()
@require_permission('patching.view')
def get_patching_jobs():
    """Get all patching jobs"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        status = request.args.get('status')
        quarter = request.args.get('quarter')
        server = request.args.get('server')
        
        # Filter jobs
        jobs = list(patching_jobs.values())
        filtered_jobs = []
        
        for job in jobs:
            if status and job['status'] != status:
                continue
            if quarter and job.get('quarter') != quarter:
                continue
            if server and server not in job['servers']:
                continue
            
            filtered_jobs.append(job)
        
        # Sort by created date (newest first)
        filtered_jobs.sort(key=lambda x: x['createdAt'], reverse=True)
        
        # Paginate
        paginated = paginate_results(filtered_jobs, page, page_size)
        
        # Transform to API format
        items = [transform_job_to_api(job) for job in paginated['items']]
        
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
            'message': f'Failed to get patching jobs: {str(e)}'
        }), 500

@patching_bp.route('/jobs/<job_id>', methods=['GET'])
@jwt_required()
@require_permission('patching.view')
def get_patching_job(job_id):
    """Get patching job details"""
    try:
        job = patching_jobs.get(job_id)
        
        if not job:
            return jsonify({
                'success': False,
                'message': 'Job not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': transform_job_to_api(job),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get patching job: {str(e)}'
        }), 500

@patching_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
@jwt_required()
@require_permission('patching.cancel')
def cancel_patching_job(job_id):
    """Cancel patching job"""
    try:
        identity = get_jwt_identity()
        job = patching_jobs.get(job_id)
        
        if not job:
            return jsonify({
                'success': False,
                'message': 'Job not found'
            }), 404
        
        if job['status'] not in ['pending', 'running']:
            return jsonify({
                'success': False,
                'message': 'Job cannot be cancelled'
            }), 400
        
        # Cancel job
        job['status'] = 'cancelled'
        job['completedAt'] = datetime.utcnow().isoformat()
        job['updatedAt'] = datetime.utcnow().isoformat()
        
        # Log audit event
        log_audit_event(
            action='patching_cancelled',
            resource='patching',
            resource_id=job_id,
            user_id=identity
        )
        
        return jsonify({
            'success': True,
            'message': 'Job cancelled successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to cancel job: {str(e)}'
        }), 500

@patching_bp.route('/rollback', methods=['POST'])
@jwt_required()
@require_permission('patching.rollback')
def rollback_server():
    """Rollback server"""
    try:
        data = request.get_json()
        identity = get_jwt_identity()
        
        server_id = data.get('server_id')
        reason = data.get('reason')
        
        if not server_id or not reason:
            return jsonify({
                'success': False,
                'message': 'Server ID and reason are required'
            }), 400
        
        # Create rollback job
        job_id = str(uuid.uuid4())
        job = {
            'id': job_id,
            'name': f'Rollback {server_id}',
            'type': 'rollback',
            'status': 'pending',
            'progress': 0,
            'servers': [server_id],
            'operator': identity,
            'reason': reason,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        patching_jobs[job_id] = job
        
        # Log audit event
        log_audit_event(
            action='rollback_started',
            resource='patching',
            resource_id=job_id,
            user_id=identity,
            details={'server': server_id, 'reason': reason}
        )
        
        return jsonify({
            'success': True,
            'data': transform_job_to_api(job),
            'message': 'Rollback started successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to start rollback: {str(e)}'
        }), 500

def transform_job_to_api(job):
    """Transform job data to API format"""
    return {
        'id': job['id'],
        'name': job['name'],
        'description': job.get('description'),
        'type': job['type'],
        'status': job['status'],
        'progress': job['progress'],
        'quarter': job.get('quarter'),
        'servers': job['servers'],
        'dryRun': job.get('dryRun', False),
        'force': job.get('force', False),
        'skipPrecheck': job.get('skipPrecheck', False),
        'skipPostcheck': job.get('skipPostcheck', False),
        'startedAt': job.get('startedAt'),
        'completedAt': job.get('completedAt'),
        'duration': job.get('duration'),
        'operator': job['operator'],
        'successCount': job.get('successCount', 0),
        'failureCount': job.get('failureCount', 0),
        'totalCount': job.get('totalCount', 0),
        'serverResults': job.get('serverResults', []),
        'createdAt': job['createdAt'],
        'updatedAt': job['updatedAt'],
        'logs': job.get('logs', [])
    }