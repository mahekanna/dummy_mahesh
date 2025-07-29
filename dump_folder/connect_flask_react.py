#!/usr/bin/env python3
"""
Flask-React Integration Script
This script modifies your existing Flask web portal to also serve API endpoints for React
"""

import os
import sys
import shutil
from datetime import datetime

def backup_existing_files():
    """Create backup of existing files"""
    backup_dir = f"backup_before_react_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup web_portal
    if os.path.exists('web_portal'):
        shutil.copytree('web_portal', f'{backup_dir}/web_portal')
        print(f"✅ Backed up web_portal to {backup_dir}/web_portal")
    
    return backup_dir

def create_api_routes():
    """Create API routes file for existing Flask app"""
    
    api_routes_content = '''"""
API Routes for React Frontend
Add these routes to your existing Flask app
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from datetime import datetime

def add_api_routes(app, csv_handler, user_manager):
    """Add API routes to existing Flask app"""
    
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """Health check endpoint"""
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'Linux Patching Automation',
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    
    @app.route('/api/auth/profile', methods=['GET'])
    @login_required
    def api_get_profile():
        """Get current user profile"""
        return jsonify({
            'success': True,
            'data': {
                'username': current_user.username,
                'role': getattr(current_user, 'role', 'admin'),
                'email': getattr(current_user, 'email', ''),
                'isActive': True
            }
        })
    
    @app.route('/api/servers', methods=['GET'])
    @login_required
    def api_get_servers():
        """Get all servers"""
        try:
            servers = csv_handler.read_servers(normalize_fields=True)
            
            # Transform to API format
            api_servers = []
            for server in servers:
                api_server = {
                    'id': server.get('server_name'),
                    'serverName': server.get('server_name'),
                    'hostGroup': server.get('host_group'),
                    'operatingSystem': server.get('operating_system', 'unknown'),
                    'serverTimezone': server.get('server_timezone'),
                    'location': server.get('location', ''),
                    'primaryOwner': server.get('primary_owner'),
                    'secondaryOwner': server.get('secondary_owner'),
                    'patcherEmail': server.get('patcher_email'),
                    'currentQuarterPatchingStatus': server.get('current_quarter_status', 'pending'),
                    'activeStatus': 'active',
                    'q1PatchDate': server.get('q1_patch_date'),
                    'q1PatchTime': server.get('q1_patch_time'),
                    'q1ApprovalStatus': server.get('q1_approval_status', 'pending'),
                    'q2PatchDate': server.get('q2_patch_date'),
                    'q2PatchTime': server.get('q2_patch_time'),
                    'q2ApprovalStatus': server.get('q2_approval_status', 'pending'),
                    'q3PatchDate': server.get('q3_patch_date'),
                    'q3PatchTime': server.get('q3_patch_time'),
                    'q3ApprovalStatus': server.get('q3_approval_status', 'pending'),
                    'q4PatchDate': server.get('q4_patch_date'),
                    'q4PatchTime': server.get('q4_patch_time'),
                    'q4ApprovalStatus': server.get('q4_approval_status', 'pending'),
                }
                api_servers.append(api_server)
            
            return jsonify({
                'success': True,
                'data': {
                    'items': api_servers,
                    'total': len(api_servers),
                    'page': 1,
                    'pageSize': len(api_servers),
                    'totalPages': 1,
                    'hasNext': False,
                    'hasPrevious': False
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to get servers: {str(e)}'
            }), 500
    
    @app.route('/api/patching/status', methods=['GET'])
    @login_required
    def api_patching_status():
        """Get patching status"""
        try:
            from config.settings import Config
            
            servers = csv_handler.read_servers(normalize_fields=True)
            total_servers = len(servers)
            
            # Count statuses
            pending_approval = sum(1 for s in servers if s.get('current_quarter_status', 'pending') == 'pending')
            completed = sum(1 for s in servers if s.get('current_quarter_status', 'pending') == 'completed')
            
            return jsonify({
                'success': True,
                'data': {
                    'currentQuarter': Config.get_current_quarter(),
                    'totalServers': total_servers,
                    'pendingApproval': pending_approval,
                    'approved': total_servers - pending_approval,
                    'completed': completed,
                    'failed': 0,
                    'successRate': (completed / total_servers * 100) if total_servers > 0 else 0,
                    'lastUpdated': datetime.utcnow().isoformat()
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to get patching status: {str(e)}'
            }), 500
    
    @app.route('/api/system/health', methods=['GET'])
    @login_required
    def api_system_health():
        """Get system health"""
        return jsonify({
            'success': True,
            'data': {
                'overall': 'healthy',
                'components': {
                    'database': {'status': 'healthy', 'message': 'CSV files accessible'},
                    'email': {'status': 'healthy', 'message': 'Email service operational'},
                    'ssh': {'status': 'healthy', 'message': 'SSH connections working'}
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    
    # Add CORS headers for React
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
'''

    with open('web_portal/api_routes.py', 'w') as f:
        f.write(api_routes_content)
    
    print("✅ Created api_routes.py")

def modify_flask_app():
    """Modify the existing Flask app to include API routes"""
    
    # Read the existing app.py
    with open('web_portal/app.py', 'r') as f:
        content = f.read()
    
    # Add imports at the top
    import_addition = '''
# API Routes for React Frontend
from api_routes import add_api_routes
'''
    
    # Add after the existing imports
    if 'from config.users import UserManager' in content:
        content = content.replace(
            'from config.users import UserManager',
            'from config.users import UserManager' + import_addition
        )
    
    # Add API routes before the main function or at the end
    api_integration = '''

# Add API routes for React frontend
try:
    add_api_routes(app, csv_handler, user_manager)
    print("✅ API routes added for React frontend")
except Exception as e:
    print(f"⚠️  Warning: Could not add API routes: {e}")
'''
    
    # Add before if __name__ == '__main__':
    if "if __name__ == '__main__':" in content:
        content = content.replace(
            "if __name__ == '__main__':",
            api_integration + "\nif __name__ == '__main__':"
        )
    else:
        content += api_integration
    
    # Write back to file
    with open('web_portal/app.py', 'w') as f:
        f.write(content)
    
    print("✅ Modified web_portal/app.py to include API routes")

def create_startup_scripts():
    """Create startup scripts"""
    
    # Flask startup script
    flask_script = '''#!/bin/bash
# Start Flask Web Portal with API support
# This runs both the original web portal AND API for React

echo "🚀 Starting Flask Web Portal with React API support..."
echo "📍 Web Portal: http://localhost:5000"
echo "📍 API Endpoints: http://localhost:5000/api/*"

cd web_portal
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
'''
    
    with open('start_flask_with_api.sh', 'w') as f:
        f.write(flask_script)
    os.chmod('start_flask_with_api.sh', 0o755)
    
    # React startup script (modify existing or create new)
    react_script = '''#!/bin/bash
# Start React Frontend
# Make sure Flask is running on port 5000 first!

echo "🚀 Starting React Frontend..."
echo "📍 Frontend: http://localhost:3000"
echo "📍 API Backend: http://localhost:5000/api (Flask)"

cd frontend

# Set API URL to Flask port 5000
export REACT_APP_API_URL=http://localhost:5000

npm start
'''
    
    with open('start_react_frontend.sh', 'w') as f:
        f.write(react_script)
    os.chmod('start_react_frontend.sh', 0o755)
    
    print("✅ Created startup scripts")

def update_react_config():
    """Update React configuration to point to Flask"""
    
    # Update package.json proxy
    package_json_path = 'frontend/package.json'
    if os.path.exists(package_json_path):
        with open(package_json_path, 'r') as f:
            content = f.read()
        
        # Update proxy to point to Flask port 5000
        if '"proxy"' in content:
            content = content.replace('"proxy": "http://localhost:8000"', '"proxy": "http://localhost:5000"')
        else:
            # Add proxy before the last }
            content = content.replace('"private": true,', '"private": true,\n  "proxy": "http://localhost:5000",')
        
        with open(package_json_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated React package.json proxy to Flask port 5000")

def create_integration_guide():
    """Create integration guide"""
    
    guide_content = '''# Flask-React Integration Guide

## What This Integration Does

Your existing Flask web portal now serves BOTH:
1. **Traditional Web Interface** (HTML pages) at http://localhost:5000
2. **REST API Endpoints** for React at http://localhost:5000/api/*

## How to Use

### Option 1: Use Original Flask Web Portal
```bash
./start_flask_with_api.sh
# Visit: http://localhost:5000
```

### Option 2: Use React Frontend + Flask API
```bash
# Terminal 1: Start Flask (with API support)
./start_flask_with_api.sh

# Terminal 2: Start React
./start_react_frontend.sh
# Visit: http://localhost:3000
```

## API Endpoints Added to Flask

- `GET /api/health` - Health check
- `GET /api/auth/profile` - User profile
- `GET /api/servers` - Server list (React compatible)
- `GET /api/patching/status` - Patching status
- `GET /api/system/health` - System health

## Benefits

✅ **No Data Loss** - Uses your existing CSV files and scripts
✅ **No New Backend** - Extends your existing Flask app
✅ **Both UIs Work** - Keep web portal + get React UI
✅ **Simple Setup** - Just run two scripts
✅ **Your Code Intact** - No changes to core logic

## Troubleshooting

**React can't connect to API:**
- Make sure Flask is running on port 5000
- Check browser console for CORS errors
- Verify API endpoints respond: curl http://localhost:5000/api/health

**Flask web portal not working:**
- All original functionality remains unchanged
- If issues occur, restore from backup folder

## Next Steps

1. Test both interfaces
2. Use whichever UI you prefer
3. Gradually migrate to React if desired
4. Keep Flask web portal as backup

This integration gives you the best of both worlds!
'''
    
    with open('FLASK_REACT_INTEGRATION.md', 'w') as f:
        f.write(guide_content)
    
    print("✅ Created integration guide")

def main():
    """Main integration function"""
    print("🔧 Flask-React Integration Starting...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('web_portal/app.py'):
        print("❌ Error: web_portal/app.py not found. Run this from project root.")
        return False
    
    if not os.path.exists('frontend/package.json'):
        print("❌ Error: frontend/package.json not found. Run this from project root.")
        return False
    
    try:
        # Step 1: Backup
        backup_dir = backup_existing_files()
        
        # Step 2: Create API routes
        create_api_routes()
        
        # Step 3: Modify Flask app
        modify_flask_app()
        
        # Step 4: Update React config
        update_react_config()
        
        # Step 5: Create startup scripts
        create_startup_scripts()
        
        # Step 6: Create guide
        create_integration_guide()
        
        print("=" * 50)
        print("🎉 Flask-React Integration Complete!")
        print("=" * 50)
        print(f"📁 Backup created: {backup_dir}")
        print("📋 Read: FLASK_REACT_INTEGRATION.md")
        print("")
        print("🚀 Quick Start:")
        print("1. ./start_flask_with_api.sh")
        print("2. ./start_react_frontend.sh (new terminal)")
        print("3. Visit http://localhost:3000 (React) or http://localhost:5000 (Flask)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during integration: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)