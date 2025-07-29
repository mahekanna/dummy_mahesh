"""
API Middleware
"""

from flask import request, g
from datetime import datetime
import uuid
import time

def setup_middleware(app):
    """Setup middleware for the Flask app"""
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        # Generate request ID
        g.request_id = str(uuid.uuid4())
        
        # Record start time
        g.start_time = time.time()
        
        # Log request (optional)
        if app.config.get('LOG_REQUESTS', False):
            app.logger.info(f"Request {g.request_id}: {request.method} {request.path}")
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        # Add request ID to response headers
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        
        # Add response time
        if hasattr(g, 'start_time'):
            response_time = int((time.time() - g.start_time) * 1000)
            response.headers['X-Response-Time'] = f"{response_time}ms"
        
        # Add timestamp
        response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
        
        # Add API version
        response.headers['X-API-Version'] = '1.0.0'
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Log response (optional)
        if app.config.get('LOG_RESPONSES', False):
            app.logger.info(f"Response {g.request_id}: {response.status_code}")
        
        return response
    
    @app.teardown_appcontext
    def teardown_appcontext(error):
        """Teardown context"""
        # Clean up any resources if needed
        pass