#!/bin/bash

# Deploy React + Flask Integration
# This script builds React app and integrates it with Flask

set -e

BASE_DIR="/home/vijji/linux_patching_automation"
REACT_DIR="${BASE_DIR}/react_patching_system/frontend"
FLASK_DIR="${BASE_DIR}/web_portal"

echo "🚀 Starting React + Flask deployment..."

# Check if directories exist
if [ ! -d "$REACT_DIR" ]; then
    echo "❌ React directory not found: $REACT_DIR"
    exit 1
fi

if [ ! -d "$FLASK_DIR" ]; then
    echo "❌ Flask directory not found: $FLASK_DIR"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js first."
    exit 1
fi

echo "📍 Current directory: $(pwd)"
echo "📁 React directory: $REACT_DIR"
echo "📁 Flask directory: $FLASK_DIR"

# Change to React directory
cd "$REACT_DIR"

# Install React dependencies
echo "📦 Installing React dependencies..."
npm install

# Build React app
echo "🔨 Building React app for production..."
npm run build

# Check if build succeeded
if [ ! -d "build" ]; then
    echo "❌ React build failed - build directory not found"
    exit 1
fi

echo "✅ React app built successfully"

# Create Flask static directory
echo "📁 Setting up Flask directories..."
mkdir -p "$FLASK_DIR/static"
mkdir -p "$FLASK_DIR/templates"

# Copy React build to Flask
echo "📋 Copying React build to Flask..."
cp -r build/static/* "$FLASK_DIR/static/"
cp build/index.html "$FLASK_DIR/templates/react_app.html"

# Modify the HTML template to work with Flask
echo "🔧 Modifying HTML template for Flask..."
sed -i 's|href="/static/|href="{{ url_for('\''static'\'', filename='\''|g' "$FLASK_DIR/templates/react_app.html"
sed -i 's|src="/static/|src="{{ url_for('\''static'\'', filename='\''|g' "$FLASK_DIR/templates/react_app.html"
sed -i 's|\.css"|.css'\'')|g' "$FLASK_DIR/templates/react_app.html"
sed -i 's|\.js"|.js'\'')|g' "$FLASK_DIR/templates/react_app.html"

# Create Flask integration code
echo "🔧 Creating Flask integration..."
cat > "$FLASK_DIR/react_routes.py" << 'EOF'
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
EOF

# Create startup script
echo "📝 Creating startup script..."
cat > "$BASE_DIR/start_flask_react.sh" << 'EOF'
#!/bin/bash

# Start Flask app with React integration
cd /home/vijji/linux_patching_automation/web_portal

echo "🚀 Starting Flask + React application..."
echo "📊 Access URL: http://localhost:5000"
echo "👤 Login with your existing credentials"
echo ""

# Set Flask environment
export FLASK_APP=app.py
export FLASK_ENV=development

# Start Flask
python3 app.py
EOF

chmod +x "$BASE_DIR/start_flask_react.sh"

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 What was done:"
echo "   ✅ React app built to static files"
echo "   ✅ Static files copied to Flask"
echo "   ✅ HTML template created for Flask"
echo "   ✅ API routes created for React integration"
echo "   ✅ Startup script created"
echo ""
echo "📋 Next steps:"
echo "   1. Add the routes from react_routes.py to your Flask app.py"
echo "   2. Run: $BASE_DIR/start_flask_react.sh"
echo "   3. Access http://localhost:5000 for the React UI"
echo ""
echo "📁 Files created:"
echo "   - $FLASK_DIR/static/ (React build files)"
echo "   - $FLASK_DIR/templates/react_app.html (React template)"
echo "   - $FLASK_DIR/react_routes.py (Flask API routes)"
echo "   - $BASE_DIR/start_flask_react.sh (Startup script)"
echo ""
echo "🎉 Ready to use!"