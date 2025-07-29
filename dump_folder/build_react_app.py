#!/usr/bin/env python3
"""
Build React App for Flask Integration
Builds React app to static files that can be served by Flask
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status"""
    try:
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(f"Success: {result.stdout}")
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    # Paths
    base_dir = Path(__file__).parent
    react_source = base_dir / "react_patching_system" / "frontend"
    flask_app = base_dir / "web_portal"
    static_dir = flask_app / "static"
    templates_dir = flask_app / "templates"
    
    print("🚀 Building React App for Flask Integration")
    print(f"React source: {react_source}")
    print(f"Flask app: {flask_app}")
    
    # Check if React app exists
    if not react_source.exists():
        print("❌ React app not found!")
        return False
    
    # Change to React directory
    os.chdir(react_source)
    
    # Install dependencies
    print("📦 Installing React dependencies...")
    if not run_command("npm install"):
        return False
    
    # Build React app
    print("🔨 Building React app...")
    if not run_command("npm run build"):
        return False
    
    # Check if build directory exists
    build_dir = react_source / "build"
    if not build_dir.exists():
        print("❌ Build directory not found!")
        return False
    
    # Clean Flask static directory
    print("🧹 Cleaning Flask static directory...")
    if static_dir.exists():
        shutil.rmtree(static_dir)
    static_dir.mkdir(parents=True)
    
    # Copy React build to Flask static
    print("📁 Copying React build to Flask static...")
    static_build = build_dir / "static"
    if static_build.exists():
        shutil.copytree(static_build, static_dir, dirs_exist_ok=True)
    
    # Copy index.html to Flask templates
    print("📄 Copying index.html to Flask templates...")
    if not templates_dir.exists():
        templates_dir.mkdir(parents=True)
    
    index_file = build_dir / "index.html"
    if index_file.exists():
        shutil.copy2(index_file, templates_dir / "react_app.html")
    
    # Create Flask route to serve React app
    print("🔧 Creating Flask integration...")
    
    flask_integration = '''
# Add this to your Flask app.py after existing routes

@app.route('/')
@app.route('/dashboard')
@app.route('/admin')
@app.route('/reports')
@app.route('/servers/<path:server_name>')
def react_app(server_name=None):
    """Serve React app for all frontend routes"""
    return render_template('react_app.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Linux Patching System',
        'timestamp': datetime.now().isoformat()
    })

# Convert existing routes to API endpoints
@app.route('/api/servers')
@login_required
def api_servers():
    """API endpoint for servers"""
    try:
        servers = csv_handler.read_servers()
        # Filter based on user permissions
        filtered_servers = []
        for server in servers:
            if current_user.can_view_server(server):
                filtered_servers.append(server)
        
        return jsonify({
            'success': True,
            'data': filtered_servers,
            'total': len(filtered_servers)
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
'''
    
    integration_file = flask_app / "react_integration.py"
    with open(integration_file, 'w') as f:
        f.write(flask_integration)
    
    print("✅ React app built and integrated successfully!")
    print(f"📁 Static files copied to: {static_dir}")
    print(f"📄 Template copied to: {templates_dir / 'react_app.html'}")
    print(f"🔧 Integration code saved to: {integration_file}")
    print("")
    print("📋 Next steps:")
    print("1. Add the routes from react_integration.py to your Flask app.py")
    print("2. Run your Flask app normally")
    print("3. Access the React UI at your Flask server URL")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)