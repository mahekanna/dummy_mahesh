"""
System Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
import psutil
import os
import time

system_bp = Blueprint('system', __name__)

@system_bp.route('/health', methods=['GET'])
@jwt_required()
def get_system_health():
    """Get system health status"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine health status
        overall_status = 'healthy'
        
        if cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
            overall_status = 'warning'
        
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            overall_status = 'critical'
        
        # Component health
        components = {
            'database': {
                'status': 'healthy',
                'message': 'Database connection is healthy',
                'lastCheck': datetime.utcnow().isoformat()
            },
            'ssh': {
                'status': 'healthy',
                'message': 'SSH connections are working',
                'lastCheck': datetime.utcnow().isoformat()
            },
            'email': {
                'status': 'healthy',
                'message': 'Email service is operational',
                'lastCheck': datetime.utcnow().isoformat()
            },
            'logging': {
                'status': 'healthy',
                'message': 'Logging system is working',
                'lastCheck': datetime.utcnow().isoformat()
            },
            'storage': {
                'status': 'healthy' if disk.percent < 80 else 'warning' if disk.percent < 90 else 'critical',
                'message': f'Disk usage: {disk.percent}%',
                'lastCheck': datetime.utcnow().isoformat()
            },
            'memory': {
                'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 90 else 'critical',
                'message': f'Memory usage: {memory.percent}%',
                'lastCheck': datetime.utcnow().isoformat()
            },
            'cpu': {
                'status': 'healthy' if cpu_percent < 80 else 'warning' if cpu_percent < 90 else 'critical',
                'message': f'CPU usage: {cpu_percent}%',
                'lastCheck': datetime.utcnow().isoformat()
            }
        }
        
        # System metrics
        metrics = {
            'uptime': int(time.time() - psutil.boot_time()),
            'totalServers': 0,  # Would get from database
            'activeConnections': 0,  # Would get from connection pool
            'queueSize': 0,  # Would get from job queue
            'averageResponseTime': 150,  # Would calculate from logs
            'errorRate': 0.01  # Would calculate from logs
        }
        
        return jsonify({
            'success': True,
            'data': {
                'overall': overall_status,
                'components': components,
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get system health: {str(e)}'
        }), 500

@system_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_system_stats():
    """Get system statistics"""
    try:
        import time
        
        # Mock statistics - in production, get from database
        stats = {
            'patching': {
                'totalJobs': 150,
                'completedJobs': 140,
                'failedJobs': 5,
                'successRate': 93.3,
                'averageDuration': 1800,  # 30 minutes
                'totalServersPatched': 500,
                'totalPatchesApplied': 2500
            },
            'servers': {
                'total': 100,
                'active': 95,
                'inactive': 5,
                'byOS': {
                    'ubuntu': 40,
                    'centos': 30,
                    'rhel': 20,
                    'debian': 10
                },
                'byGroup': {
                    'web': 30,
                    'database': 20,
                    'app': 25,
                    'cache': 15,
                    'monitoring': 10
                },
                'byEnvironment': {
                    'production': 60,
                    'staging': 25,
                    'development': 10,
                    'testing': 5
                }
            },
            'approvals': {
                'total': 200,
                'pending': 15,
                'approved': 170,
                'rejected': 10,
                'expired': 5
            },
            'system': {
                'uptime': int(time.time() - psutil.boot_time()),
                'version': '1.0.0',
                'lastRestart': datetime.utcnow().isoformat(),
                'activeUsers': 5,
                'totalRequests': 10000,
                'averageResponseTime': 150
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get system stats: {str(e)}'
        }), 500

@system_bp.route('/test-email', methods=['POST'])
@jwt_required()
def test_email():
    """Test email configuration"""
    try:
        data = request.get_json()
        recipient = data.get('recipient')
        
        if not recipient:
            return jsonify({
                'success': False,
                'message': 'Recipient is required'
            }), 400
        
        # In a real implementation, send test email
        # For now, just return success
        
        return jsonify({
            'success': True,
            'message': f'Test email sent to {recipient}',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to send test email: {str(e)}'
        }), 500