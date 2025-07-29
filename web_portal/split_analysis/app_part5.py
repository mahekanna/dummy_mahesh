        from database.models import DatabaseManager
        
        db = DatabaseManager()
        # Test database connection with provided settings
        result = db.test_connection(
            host=data['host'],
            port=data['port'],
            dbname=data['name'],
            user=data['user'],
            password=data['password']
        )
        
        return jsonify({'success': result, 'error': None if result else 'Database connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_patching_script', methods=['POST'])
@login_required
def test_patching_script():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        data = request.json
        script_path = data.get('script_path')
        validate_script = data.get('validate_script', True)
        
        if not script_path:
            return jsonify({'success': False, 'error': 'Script path is required'})
        
        # Get a random server from the CSV to test on
        from utils.csv_handler import CSVHandler
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers()
        
        if not servers:
            return jsonify({'success': False, 'error': 'No servers found in CSV'})
        
        import random
        test_server = random.choice(servers)
        server_name = test_server.get('server_name', test_server.get('Server Name', 'Unknown'))
        
        # Test SSH connection and script existence
        from utils.ssh_manager import SSHManager
        ssh_manager = SSHManager()
        
        try:
            # Test SSH connection
            result = ssh_manager.test_connection(server_name)
            if not result:
                return jsonify({'success': False, 'error': f'SSH connection failed to {server_name}'})
            
            # Test script existence if validation is enabled
            if validate_script:
                script_exists = ssh_manager.check_file_exists(server_name, script_path)
                if not script_exists:
                    return jsonify({'success': False, 'error': f'Script {script_path} not found on {server_name}'})
            
            # Test script is executable
            is_executable = ssh_manager.check_file_executable(server_name, script_path)
            if not is_executable:
                return jsonify({'success': False, 'error': f'Script {script_path} is not executable on {server_name}'})
            
            message = f'✅ Script test successful on {server_name}\n'
            message += f'• SSH connection: OK\n'
            if validate_script:
                message += f'• Script exists: OK\n'
            message += f'• Script executable: OK'
            
            return jsonify({'success': True, 'message': message})
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'Test failed on {server_name}: {str(e)}'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/control_patching', methods=['POST'])
@login_required
def control_patching():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        data = request.json
        action = data.get('action')
        
        if action == 'pause':
            set_patching_paused(True)
            app.logger.info(f"Patching paused by admin user: {current_user.name}")
        elif action == 'resume':
            set_patching_paused(False)
            app.logger.info(f"Patching resumed by admin user: {current_user.name}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/control_scheduling', methods=['POST'])
@login_required
def control_scheduling():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        data = request.json
        action = data.get('action')
        
        if action == 'freeze':
            set_schedule_frozen(True)
            app.logger.info(f"Scheduling frozen by admin user: {current_user.name}")
        elif action == 'unfreeze':
            set_schedule_frozen(False)
            app.logger.info(f"Scheduling unfrozen by admin user: {current_user.name}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/refresh_services', methods=['POST'])
@login_required
def refresh_services():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        # Refresh service status
        import subprocess
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        app.logger.info(f"Services refreshed by admin user: {current_user.name}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_cache', methods=['POST'])
@login_required
def clear_cache():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        # Clear application cache
        import os
        import shutil
        
        cache_dirs = ['/tmp/patching_cache', '/var/tmp/patching_cache']
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
        
        app.logger.info(f"Cache cleared by admin user: {current_user.name}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/view_logs')
@login_required
def view_logs():
    if not current_user.role == 'admin':
        flash('Admin access required')
        return redirect(url_for('dashboard'))
    
    try:
        # Read recent log entries
        log_entries = []
        log_files = [
            '/var/log/patching/patching.log',
            '/opt/linux_patching_automation/logs/patching.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    log_entries.extend(lines[-100:])  # Last 100 lines
                break
        
        return render_template('logs.html', log_entries=log_entries)
    except Exception as e:
        flash(f'Error reading logs: {str(e)}')
        return redirect(url_for('system_config'))

# Helper functions for system configuration
def save_config_to_env(config_updates):
    """Save configuration updates to environment file"""
    env_file = '/opt/linux_patching_automation/.env'
    
    # Read existing environment
    existing_env = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_env[key] = value
    
    # Update with new values
    existing_env.update(config_updates)
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.write("# Linux Patching Automation Configuration\n")
        f.write("# Generated automatically - do not edit manually\n\n")
        for key, value in existing_env.items():
            f.write(f"{key}={value}\n")

def check_ldap_status():
    """Check LDAP connection status"""
    try:
        if not Config.LDAP_ENABLED:
            return 'disabled', 'LDAP Disabled'
        
        from utils.nslcd_ldap_auth import NSLCDLDAPAuthenticator
        auth = NSLCDLDAPAuthenticator()
        if auth.test_ldap_connection():
            return 'connected', 'Connected'
        else:
            return 'error', 'Connection Error'
    except Exception:
        return 'error', 'Error'

def check_sendmail_status():
    """Check sendmail availability"""
    try:
        import subprocess
        result = subprocess.run(['which', 'sendmail'], capture_output=True, text=True)
        if result.returncode == 0:
            return 'available', 'Available'
        else:
            return 'unavailable', 'Not Available'
    except Exception:
        return 'unavailable', 'Error'

def is_patching_paused():
    """Check if patching is paused"""
    try:
        with open('/tmp/patching_paused', 'r') as f:
            return f.read().strip() == 'true'
    except FileNotFoundError:
        return False

def set_patching_paused(paused):
    """Set patching paused state"""
    with open('/tmp/patching_paused', 'w') as f:
        f.write('true' if paused else 'false')

def is_schedule_frozen():
    """Check if scheduling is frozen"""
    try:
        with open('/tmp/schedule_frozen', 'r') as f:
            return f.read().strip() == 'true'
    except FileNotFoundError:
        return False

def set_schedule_frozen(frozen):
    """Set schedule frozen state"""
    with open('/tmp/schedule_frozen', 'w') as f:
        f.write('true' if frozen else 'false')

def check_service_status():
    """Check service status"""
    try:
        import subprocess
        result = subprocess.run(['systemctl', 'is-active', 'patching-portal'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return 'running', 'Running'
        else:
            return 'stopped', 'Stopped'
    except Exception:
        return 'unknown', 'Unknown'

def check_system_health():
    """Check overall system health"""
    try:
        # Check disk space
        import shutil
        free_space = shutil.disk_usage('/').free / (1024**3)  # GB
        
        if free_space < 1:
            return 'critical', 'Low Disk Space'
        elif free_space < 5:
            return 'warning', 'Warning'
        else:
            return 'healthy', 'Healthy'
    except Exception:
        return 'unknown', 'Unknown'

# React app routes
@app.route('/react')
@app.route('/react/dashboard')
@app.route('/react/admin')
@app.route('/react/reports')
@app.route('/react/servers/<path:server_name>')
def react_app(server_name=None):
    """Serve React app for all frontend routes"""
    return render_template('react_app.html')

# API routes for React
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
