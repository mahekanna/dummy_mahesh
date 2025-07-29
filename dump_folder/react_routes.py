# Flask routes for React integration
# Add these routes to your main Flask app

from flask import render_template, jsonify, request
from flask_login import login_required, current_user, login_user
from datetime import datetime

# React app routes
@app.route('/')
@app.route('/dashboard')
@app.route('/admin')
@app.route('/reports')
@app.route('/servers/<path:server_name>')
def react_app(server_name=None):
    """Serve React app for all frontend routes"""
    return render_template('react_app.html')

# API routes
@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Linux Patching System',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/servers')
@login_required
def api_servers():
    """Get all servers - convert existing dashboard logic"""
    try:
        servers = csv_handler.read_servers()
        current_quarter = get_current_quarter()
        
        # Filter servers based on user permissions
        filtered_servers = []
        for server in servers:
            if current_user.can_view_server(server):
                filtered_servers.append(server)
        
        return jsonify({
            'success': True,
            'data': filtered_servers,
            'total': len(filtered_servers),
            'currentQuarter': current_quarter
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user_manager = UserManager()
    user = user_manager.authenticate_user(username, password)
    
    if user:
        login_user(user)
        return jsonify({
            'success': True,
            'user': {
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'permissions': user.permissions
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid credentials'
        }), 401

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """API logout endpoint"""
    logout_user()
    return jsonify({'success': True})
