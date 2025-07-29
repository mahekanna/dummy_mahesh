"""
Error Handlers
"""

from flask import jsonify
from flask_jwt_extended.exceptions import JWTExtendedException
from werkzeug.exceptions import HTTPException
from datetime import datetime
import traceback

def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors"""
        return jsonify({
            'success': False,
            'message': 'Bad request',
            'error': {
                'code': 400,
                'type': 'BAD_REQUEST',
                'description': str(error.description) if hasattr(error, 'description') else 'Invalid request'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized errors"""
        return jsonify({
            'success': False,
            'message': 'Unauthorized',
            'error': {
                'code': 401,
                'type': 'UNAUTHORIZED',
                'description': 'Authentication required'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden errors"""
        return jsonify({
            'success': False,
            'message': 'Forbidden',
            'error': {
                'code': 403,
                'type': 'FORBIDDEN',
                'description': 'Insufficient permissions'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors"""
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error': {
                'code': 404,
                'type': 'NOT_FOUND',
                'description': 'The requested resource was not found'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle method not allowed errors"""
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'error': {
                'code': 405,
                'type': 'METHOD_NOT_ALLOWED',
                'description': 'The method is not allowed for this resource'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 405
    
    @app.errorhandler(409)
    def conflict(error):
        """Handle conflict errors"""
        return jsonify({
            'success': False,
            'message': 'Conflict',
            'error': {
                'code': 409,
                'type': 'CONFLICT',
                'description': 'The request conflicts with the current state'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle validation errors"""
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'error': {
                'code': 422,
                'type': 'VALIDATION_ERROR',
                'description': 'The request data failed validation'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 422
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """Handle rate limit errors"""
        return jsonify({
            'success': False,
            'message': 'Too many requests',
            'error': {
                'code': 429,
                'type': 'RATE_LIMIT_EXCEEDED',
                'description': 'Rate limit exceeded. Please try again later'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle internal server errors"""
        # Log the error
        app.logger.error(f"Internal server error: {str(error)}")
        if app.config.get('DEBUG'):
            app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': {
                'code': 500,
                'type': 'INTERNAL_SERVER_ERROR',
                'description': 'An internal server error occurred'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exceptions(error):
        """Handle JWT exceptions"""
        return jsonify({
            'success': False,
            'message': 'JWT error',
            'error': {
                'code': 401,
                'type': 'JWT_ERROR',
                'description': str(error)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 401
    
    @app.errorhandler(HTTPException)
    def handle_http_exceptions(error):
        """Handle generic HTTP exceptions"""
        return jsonify({
            'success': False,
            'message': error.name,
            'error': {
                'code': error.code,
                'type': error.name.upper().replace(' ', '_'),
                'description': error.description
            },
            'timestamp': datetime.utcnow().isoformat()
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exceptions(error):
        """Handle generic exceptions"""
        # Log the error
        app.logger.error(f"Unhandled exception: {str(error)}")
        if app.config.get('DEBUG'):
            app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred',
            'error': {
                'code': 500,
                'type': 'UNEXPECTED_ERROR',
                'description': 'An unexpected error occurred. Please try again later'
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500