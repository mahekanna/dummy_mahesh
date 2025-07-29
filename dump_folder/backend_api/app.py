#!/usr/bin/env python3
"""
Flask REST API Backend for Linux Patching Automation
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import blueprints
from backend_api.routes import (
    auth_bp, servers_bp, patching_bp, approvals_bp, 
    reports_bp, system_bp, audit_bp, health_bp
)

# Import middleware and error handlers
from backend_api.middleware import setup_middleware
from backend_api.error_handlers import register_error_handlers

# Import config
from backend_api.config import Config

def create_app(config_class=Config):
    """Create Flask application with configuration"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # JWT Configuration
    jwt = JWTManager(app)
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(servers_bp, url_prefix='/api/servers')
    app.register_blueprint(patching_bp, url_prefix='/api/patching')
    app.register_blueprint(approvals_bp, url_prefix='/api/approvals')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(system_bp, url_prefix='/api/system')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    
    # Root endpoint
    @app.route('/api')
    def api_root():
        return jsonify({
            'success': True,
            'data': {
                'name': 'Linux Patching Automation API',
                'version': '1.0.0',
                'endpoints': {
                    'auth': '/api/auth',
                    'servers': '/api/servers',
                    'patching': '/api/patching',
                    'approvals': '/api/approvals',
                    'reports': '/api/reports',
                    'system': '/api/system',
                    'audit': '/api/audit',
                    'health': '/api/health'
                }
            }
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('API_PORT', 8000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )