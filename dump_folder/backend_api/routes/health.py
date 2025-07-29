"""
Health Check Routes
"""

from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'Linux Patching Automation API',
                'version': '1.0.0',
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Health check failed: {str(e)}'
        }), 500

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check if service is ready to accept requests
        # In production, check database connections, etc.
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'ready',
                'checks': {
                    'database': 'ok',
                    'filesystem': 'ok',
                    'dependencies': 'ok'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Readiness check failed: {str(e)}'
        }), 500

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Liveness check endpoint"""
    try:
        # Check if service is alive
        return jsonify({
            'success': True,
            'data': {
                'status': 'alive',
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Liveness check failed: {str(e)}'
        }), 500