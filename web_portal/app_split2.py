# web_portal/app_split2.py - Part 2: API Routes, Admin Panel, and Advanced Features
# NOTE: This file contains the second part of the Flask application
# To use this file, it should be combined with app_split1.py imports and setup

# Additional utility functions (to be added after app_split1.py imports)
def is_freeze_period(patch_date=None):
    """Check if we're in the freeze period for a given patch date"""
    today = datetime.now().date()
    current_weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    # If no specific patch date provided, use general freeze logic
    if patch_date is None:
        # Current week freeze: Thursday (3) through Tuesday (1) of next week
        return current_weekday in [3, 4, 5, 6, 0, 1]
    
    # Convert patch_date to date object if it's a string
    if isinstance(patch_date, str):
        try:
            patch_date = datetime.strptime(patch_date, '%Y-%m-%d').date()
        except:
            return True  # If invalid date, err on side of caution
    
    # Calculate which week the patch date is in
    days_until_patch = (patch_date - today).days
    
    # If patch is in the current week (this week's Thursday onwards), freeze it
    if days_until_patch < 0:
        return True  # Past dates are frozen
    
    # Find next Thursday from today
    days_until_next_thursday = (3 - current_weekday) % 7
    if days_until_next_thursday == 0 and current_weekday >= 3:
        days_until_next_thursday = 7  # If today is Thursday or later, next Thursday is next week
    
    next_thursday = today + timedelta(days=days_until_next_thursday)
    
    # If patch date is before next Thursday, it's in current week - freeze it
    if patch_date < next_thursday:
        return True
    
    # If patch date is in next week or later, allow changes
    return False

# Continue with routes from app_split1.py...

@app.route('/update_schedule', methods=['POST'])
@login_required
def update_schedule():
    try:
        server_name = request.form['server_name']
        quarter = request.form['quarter']
        patch_date = request.form['patch_date']
        patch_time = request.form['patch_time']
        
        # Validate freeze period for the specific patch date
        if is_freeze_period(patch_date):
            flash('Cannot modify schedule for current week (Thursday to Tuesday). You can only modify schedules for next week onwards.')
            return redirect(url_for('server_detail', server_name=server_name))
        
        # Update CSV
        servers = csv_handler.read_servers()
        updated = False
        
        for server in servers:
            if server['Server Name'] == server_name:
                # Check permission to modify this server
                can_modify = (current_user.is_admin() or 
                             server.get('primary_owner') == current_user.email or 
                             server.get('secondary_owner') == current_user.email)
                
                if can_modify:
                    server[f'Q{quarter} Patch Date'] = patch_date
                    server[f'Q{quarter} Patch Time'] = patch_time
                    
                    # If updating current quarter, update status
                    if quarter == Config.get_current_quarter():
                        server['Current Quarter Patching Status'] = 'Scheduled'
                    
                    updated = True
                    break
        
        if updated:
            csv_handler.write_servers(servers)
            flash('Schedule updated successfully')
        else:
            flash('Failed to update schedule')
        
        return redirect(url_for('server_detail', server_name=server_name))
    
    except Exception as e:
        flash(f'Error updating schedule: {e}')
        return redirect(url_for('dashboard'))

@app.route('/api/available_dates/<quarter>')
@login_required
def api_available_dates(quarter):
    """API endpoint to get available patching dates"""
    try:
        # Generate available patching dates (Thursdays) for the quarter
        current_year = datetime.now().year
        quarter_months = Config.QUARTERS.get(quarter, {}).get('months', [])
        
        available_dates = []
        
        for month in quarter_months:
            # Adjust year for Q1 which spans two years
            year = current_year
            if quarter == '1' and month in [11, 12]:
                if datetime.now().month < 11:
                    year = current_year
                else:
                    year = current_year
            elif quarter == '1' and month == 1:
                if datetime.now().month < 11:
                    year = current_year + 1
                else:
                    year = current_year + 1
            
            # Find all Thursdays in the month
            cal = calendar.monthcalendar(year, month)
            thursdays = [
                datetime(year, month, week[calendar.THURSDAY]).strftime('%Y-%m-%d')
                for week in cal
                if week[calendar.THURSDAY] != 0
            ]
            
            available_dates.extend(thursdays)
        
        return jsonify(available_dates)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server_timezone/<server_name>')
@login_required
def api_server_timezone(server_name):
    """API endpoint to get server timezone information"""
    try:
        servers = csv_handler.read_servers()
        server = None
        
        for s in servers:
            if s['Server Name'] == server_name:
                server = s
                break
        
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        # Get timezone information
        server_timezone = server.get('Server Timezone', 'UTC')
        now = datetime.now()
        timezone_abbr = timezone_handler.get_timezone_abbreviation(server_timezone, now)
        
        # Get current time in server timezone
        server_time = timezone_handler.get_current_time_in_timezone(server_timezone)
        
        return jsonify({
            'timezone': server_timezone,
            'abbreviation': timezone_abbr,
            'current_time': server_time.strftime('%Y-%m-%d %H:%M:%S'),
            'offset': server_time.strftime('%z')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai_recommendation/<server_name>/<quarter>')
@login_required
def api_ai_recommendation(server_name, quarter):
    """API endpoint to get AI-powered scheduling recommendations"""
    try:
        from scripts.load_predictor import SmartLoadPredictor
        from scripts.intelligent_scheduler import SmartScheduler
        
        # Initialize predictors
        load_predictor = SmartLoadPredictor()
        intelligent_scheduler = SmartScheduler()
        
        # Get load-based recommendation
        load_recommendation = load_predictor.analyze_server_load_patterns(server_name)
        
        # Get intelligent scheduling recommendation
        available_thursdays = intelligent_scheduler.get_quarter_thursdays(quarter)
        
        if not available_thursdays:
            return jsonify({
                'success': False,
                'message': 'No available Thursday dates found for this quarter'
            })
        
        # Parse the recommended time from load predictor
        recommended_time = load_recommendation.get('recommended_time', '20:00')
        
        # Find the best Thursday based on load analysis
        best_thursday = None
        if load_recommendation.get('confidence_level') == 'High':
            # Use first available Thursday for high confidence
            best_thursday = available_thursdays[0]
        elif load_recommendation.get('confidence_level') == 'Medium':
            # Use second Thursday if available for medium confidence
            best_thursday = available_thursdays[1] if len(available_thursdays) > 1 else available_thursdays[0]
        else:
            # Use later Thursday for low confidence
            best_thursday = available_thursdays[-1] if available_thursdays else available_thursdays[0]
        
        # Format the response
        response = {
            'success': True,
            'recommended_date': best_thursday.strftime('%Y-%m-%d'),
            'recommended_time': recommended_time,
            'confidence_level': load_recommendation.get('confidence_level', 'Medium'),
            'reasoning': load_recommendation.get('reasoning', ['AI-based scheduling recommendation']),
            'risk_factors': load_recommendation.get('risk_factors', []),
            'alternative_times': load_recommendation.get('alternative_times', [])
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating recommendation: {str(e)}'
        }), 500

# Admin API Routes
@app.route('/api/admin/generate_report/<report_type>', methods=['POST'])
@login_required
def api_generate_report(report_type):
    """Generate and send admin reports"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        
        if report_type == 'daily':
            success = admin_manager.send_daily_report()
        elif report_type == 'weekly':
            success = admin_manager.send_weekly_report()
        elif report_type == 'monthly':
            success = admin_manager.send_monthly_report()
        else:
            return jsonify({'success': False, 'message': 'Invalid report type'})
        
        return jsonify({
            'success': success,
            'message': f'{report_type.title()} report generated and sent' if success else 'Failed to generate report'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/sync_database', methods=['POST'])
@login_required
def api_sync_database():
    """Sync CSV to database"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        success = admin_manager.sync_csv_to_database()
        
        return jsonify({
            'success': success,
            'message': 'Database sync completed' if success else 'Database sync failed'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/cleanup_data', methods=['POST'])
@login_required
def api_cleanup_data():
    """Clean up old data"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        success = admin_manager.cleanup_old_data()
        
        return jsonify({
            'success': success,
            'message': 'Data cleanup completed' if success else 'Data cleanup failed'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/intelligent_scheduling', methods=['POST'])
@login_required
def api_intelligent_scheduling():
    """Run intelligent scheduling"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.intelligent_scheduler import SmartScheduler
        from config.settings import Config
        
        scheduler = SmartScheduler()
        current_quarter = Config.get_current_quarter()
        scheduler.assign_smart_schedules(current_quarter)
        
        return jsonify({
            'success': True,
            'message': 'Intelligent scheduling completed successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/sync_ldap_users', methods=['POST'])
@login_required
def api_sync_ldap_users():
    """Sync users from LDAP"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.ldap_manager import LDAPManager
        ldap_manager = LDAPManager()
        success, message = ldap_manager.sync_users_from_ldap()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/add_server_group', methods=['POST'])
@login_required
def api_add_server_group():
    """Add new server group"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        
        group_name = request.form['group_name']
        display_name = request.form['group_display_name']
        description = request.form['group_description']
        priority = int(request.form['group_priority'])
        max_concurrent = int(request.form['max_concurrent'])
        
        # Load current config
        config = admin_manager.load_server_groups_config()
        if not config:
            config = {'server_groups': {}}
        
        # Add new group
        config['server_groups'][group_name] = {
            'name': display_name,
            'description': description,
            'priority': priority,
            'max_concurrent': max_concurrent,
            'scheduling_window': '20:00-23:00',
            'patterns': [],
            'host_groups': []
        }
        
        success = admin_manager.save_server_groups_config(config)
        
        return jsonify({
            'success': success,
            'message': 'Server group added successfully' if success else 'Failed to add server group'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test_ldap_connection', methods=['POST'])
@login_required
def api_test_ldap_connection():
    """Test LDAP connection"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.ldap_manager import LDAPManager
        ldap_manager = LDAPManager()
        success, message = ldap_manager.test_ldap_connection()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration Update Routes
@app.route('/update_admin_config', methods=['POST'])
@login_required
def update_admin_config():
    """Update admin configuration"""
    if not current_user.is_admin():
        flash('Admin access required')
        return redirect(url_for('admin_panel'))
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        
        # Get form data
        admin_email = request.form['admin_email']
        backup_admin_email = request.form.get('backup_admin_email', '')
        send_daily_reports = 'send_daily_reports' in request.form
        send_weekly_reports = 'send_weekly_reports' in request.form
        send_error_alerts = 'send_error_alerts' in request.form
        
        # Load current config
        config = admin_manager.load_admin_config()
        
        # Update config
        config['admin_settings']['admin_email'] = admin_email
        config['admin_settings']['backup_admin_email'] = backup_admin_email
        config['admin_settings']['notification_settings']['send_daily_reports'] = send_daily_reports
        config['admin_settings']['notification_settings']['send_weekly_reports'] = send_weekly_reports
        config['admin_settings']['notification_settings']['send_error_alerts'] = send_error_alerts
        
        if admin_manager.save_admin_config(config):
            flash('Admin configuration updated successfully')
        else:
            flash('Failed to update admin configuration')
            
    except Exception as e:
        flash(f'Error updating admin configuration: {e}')
    
    return redirect(url_for('admin_panel'))

@app.route('/update_ldap_config', methods=['POST'])
@login_required
def update_ldap_config():
    """Update LDAP configuration"""
    if not current_user.is_admin():
        flash('Admin access required')
        return redirect(url_for('admin_panel'))
    
    try:
        from scripts.ldap_manager import LDAPManager
        ldap_manager = LDAPManager()
        
        # Get form data
        ldap_enabled = 'ldap_enabled' in request.form
        ldap_server = request.form.get('ldap_server', '')
        ldap_base_dn = request.form.get('ldap_base_dn', '')
        ldap_bind_dn = request.form.get('ldap_bind_dn', '')
        ldap_bind_password = request.form.get('ldap_bind_password', '')
        
        # Update LDAP config
        new_config = {
            'enabled': ldap_enabled,
            'server': ldap_server,
            'base_dn': ldap_base_dn,
            'bind_dn': ldap_bind_dn
        }
        
        if ldap_bind_password:
            new_config['bind_password'] = ldap_bind_password
        
        if ldap_manager.update_ldap_config(new_config):
            flash('LDAP configuration updated successfully')
        else:
            flash('Failed to update LDAP configuration')
            
    except Exception as e:
        flash(f'Error updating LDAP configuration: {e}')
    
    return redirect(url_for('admin_panel'))

# More Admin API Routes
@app.route('/api/admin/analyze_load_patterns', methods=['POST'])
@login_required
def api_analyze_load_patterns():
    """Analyze load patterns for all servers"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.load_predictor import SmartLoadPredictor
        from config.settings import Config
        
        predictor = SmartLoadPredictor()
        current_quarter = Config.get_current_quarter()
        recommendations = predictor.analyze_all_servers(current_quarter)
        
        return jsonify({
            'success': True,
            'message': f'Analyzed load patterns for {len(recommendations)} servers'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/generate_predictions', methods=['POST'])
@login_required
def api_generate_predictions():
    """Generate AI predictions for unscheduled servers"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.load_predictor import SmartLoadPredictor
        from utils.csv_handler import CSVHandler
        
        predictor = SmartLoadPredictor()
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers()
        
        # Generate predictions for servers without schedules
        prediction_count = 0
        for server in servers:
            # Simulate historical data if needed
            predictor.simulate_historical_data(server['Server Name'], days=7)
            prediction_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Generated predictions for {prediction_count} servers'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/backup_data', methods=['POST'])
@login_required
def api_backup_data():
    """Create backup of all data"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        
        # Create backup
        backup_path = admin_manager._backup_csv_file()
        
        if backup_path:
            return jsonify({
                'success': True,
                'message': f'Data backup created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create backup'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/sync_host_groups', methods=['POST'])
@login_required
def api_sync_host_groups():
    """Sync host groups from CSV to configuration"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.sync_host_groups import HostGroupSyncer
        syncer = HostGroupSyncer()
        result = syncer.run_full_sync()
        
        return jsonify({
            'success': result['success'],
            'message': f"Found {result.get('host_groups_found', 0)} host groups: {', '.join(result.get('host_groups', []))}" if result['success'] else result.get('error', 'Unknown error'),
            'details': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Reports Dashboard
@app.route('/reports')
@login_required
def reports_dashboard():
    """Reports dashboard with charts and analytics"""
    if not current_user.is_admin():
        flash('Access denied: Admin privileges required')
        return redirect(url_for('dashboard'))
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        
        # Get basic data for initial load
        servers = csv_handler.read_servers()
        current_quarter = Config.get_current_quarter()
        
        # Get host groups
        host_groups = list(set(server.get('host_group', '') for server in servers if server.get('host_group')))
        
        # Calculate basic stats
        stats = {
            'total_servers': len(servers),
            'pending': 0,
            'approved': 0,
            'scheduled': 0,
            'completed': 0,
            'failed': 0
        }
        
        for server in servers:
            approval_status = server.get(f'Q{current_quarter} Approval Status', 'Pending')
            patch_status = server.get('Current Quarter Patching Status', 'Pending')
            
            if approval_status in ['Approved', 'Auto-Approved']:
                stats['approved'] += 1
            else:
                stats['pending'] += 1
            
            if patch_status == 'Scheduled':
                stats['scheduled'] += 1
            elif patch_status == 'Completed':
                stats['completed'] += 1
            elif patch_status == 'Failed':
                stats['failed'] += 1
        
        return render_template(
            'reports_dashboard.html',
            stats=stats,
            current_quarter=current_quarter,
            host_groups=host_groups,
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
    except Exception as e:
        flash(f'Error loading reports dashboard: {e}')
        return redirect(url_for('admin_panel'))

# API Routes for Reports
@app.route('/api/reports/data')
@login_required
def api_reports_data():
    """API endpoint for reports dashboard data"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        
        report_type = request.args.get('type', 'daily')
        quarter = request.args.get('quarter', Config.get_current_quarter())
        host_group_filter = request.args.get('host_group', 'all')
        status_filter = request.args.get('status', 'all')
        
        # Generate report data
        if report_type == 'daily':
            report_data = admin_manager.generate_daily_report()
        elif report_type == 'weekly':
            report_data = admin_manager.generate_weekly_report()
        else:
            report_data = admin_manager.generate_daily_report()
        
        if not report_data:
            return jsonify({'success': False, 'message': 'Failed to generate report data'})
        
        # Get additional data for dashboard
        servers = csv_handler.read_servers()
        
        # Filter by host group if specified
        if host_group_filter != 'all':
            servers = [s for s in servers if s.get('host_group') == host_group_filter]
        
        # Filter by status if specified
        if status_filter != 'all':
            filtered_servers = []
            for server in servers:
                approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
                patch_status = server.get('Current Quarter Patching Status', 'Pending')
                
                if status_filter == 'completed' and patch_status == 'Completed':
                    filtered_servers.append(server)
                elif status_filter == 'scheduled' and patch_status == 'Scheduled':
                    filtered_servers.append(server)
                elif status_filter == 'approved' and approval_status in ['Approved', 'Auto-Approved']:
                    filtered_servers.append(server)
                elif status_filter == 'pending' and approval_status == 'Pending':
                    filtered_servers.append(server)
                elif status_filter == 'failed' and patch_status == 'Failed':
                    filtered_servers.append(server)
            servers = filtered_servers
        
        # Calculate host group breakdown
        host_group_breakdown = {}
        for server in servers:
            hg = server.get('host_group', 'unknown')
            if hg not in host_group_breakdown:
                host_group_breakdown[hg] = {
                    'total': 0, 'approved': 0, 'pending': 0, 
                    'scheduled': 0, 'completed': 0, 'failed': 0
                }
            
            host_group_breakdown[hg]['total'] += 1
            
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            patch_status = server.get('Current Quarter Patching Status', 'Pending')
            
            if approval_status in ['Approved', 'Auto-Approved']:
                host_group_breakdown[hg]['approved'] += 1
            else:
                host_group_breakdown[hg]['pending'] += 1
            
            if patch_status == 'Scheduled':
                host_group_breakdown[hg]['scheduled'] += 1
            elif patch_status == 'Completed':
                host_group_breakdown[hg]['completed'] += 1
            elif patch_status == 'Failed':
                host_group_breakdown[hg]['failed'] += 1
        
        # Generate timeline data (mock data for now)
        timeline_data = {
            'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'completed': [2, 5, 8, len([s for s in servers if s.get('Current Quarter Patching Status') == 'Completed'])],
            'scheduled': [1, 3, 6, len([s for s in servers if s.get('Current Quarter Patching Status') == 'Scheduled'])]
        }
        
        # Find attention required items
        attention_required = []
        for server in servers:
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            patch_date = server.get(f'Q{quarter} Patch Date')
            
            if approval_status == 'Pending' and patch_date:
                try:
                    patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                    days_until = (patch_dt - datetime.now()).days
                    if days_until <= 3:
                        attention_required.append({
                            'server': server['Server Name'],
                            'issue': 'Approval overdue',
                            'owner': server.get('primary_owner', 'Unknown'),
                            'status': 'Urgent' if days_until <= 1 else 'High',
                            'priority': 'high' if days_until <= 1 else 'medium'
                        })
                except ValueError:
                    pass
        
        # Get completed servers data
        completed_servers = []
        for server in servers:
            patch_status = server.get('Current Quarter Patching Status', 'Pending')
            if patch_status in ['Completed', 'Failed']:
                completed_servers.append({
                    'server_name': server.get('Server Name', ''),
                    'host_group': server.get('host_group', ''),
                    'patch_date': server.get(f'Q{quarter} Patch Date', ''),
                    'patch_time': server.get(f'Q{quarter} Patch Time', ''),
                    'completion_date': server.get('Last Patch Date', ''),
                    'duration': server.get('Patch Duration', ''),
                    'owner': server.get('primary_owner', ''),
                    'status': patch_status
                })
        
        # Add enhanced data to report
        report_data['host_group_breakdown'] = host_group_breakdown
        report_data['timeline_data'] = timeline_data
        report_data['attention_required'] = attention_required
        report_data['completed_servers'] = completed_servers
        
        return jsonify({
            'success': True,
            'report_data': report_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reports/text')
@login_required
def api_reports_text():
    """Generate text-based reports with filters"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        report_type = request.args.get('type', 'summary')
        quarter = request.args.get('quarter', Config.get_current_quarter())
        host_group_filter = request.args.get('host_group', 'all')
        status_filter = request.args.get('status', 'all')
        format_type = request.args.get('format', 'display')
        
        # Get servers data
        servers = csv_handler.read_servers()
        
        # Filter by host group if specified
        if host_group_filter != 'all':
            servers = [s for s in servers if s.get('host_group') == host_group_filter]
        
        # Filter by status if specified
        if status_filter != 'all':
            filtered_servers = []
            for server in servers:
                approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
                patch_status = server.get('Current Quarter Patching Status', 'Pending')
                
                if status_filter == 'completed' and patch_status == 'Completed':
                    filtered_servers.append(server)
                elif status_filter == 'scheduled' and patch_status == 'Scheduled':
                    filtered_servers.append(server)
                elif status_filter == 'approved' and approval_status in ['Approved', 'Auto-Approved']:
                    filtered_servers.append(server)
                elif status_filter == 'pending' and approval_status == 'Pending':
                    filtered_servers.append(server)
                elif status_filter == 'failed' and patch_status == 'Failed':
                    filtered_servers.append(server)
            servers = filtered_servers
        
        # Generate CSV report based on type
        report_content = generate_csv_report(servers, report_type, quarter, host_group_filter)
        
        if format_type == 'download':
            from flask import Response
            filename = f"{report_type}_report_Q{quarter}_{host_group_filter}_{status_filter}.csv"
            return Response(
                report_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
        else:
            return report_content, 200, {'Content-Type': 'text/csv'}
            
    except Exception as e:
        return f"Error generating report: {str(e)}", 500

@app.route('/api/reports/export_completed')
@login_required
def api_export_completed():
    """Export completed servers list"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        quarter = request.args.get('quarter', Config.get_current_quarter())
        host_group_filter = request.args.get('host_group', 'all')
        
        # Get servers data
        servers = csv_handler.read_servers()
        
        # Filter by host group and completed status
        completed_servers = []
        for server in servers:
            patch_status = server.get('Current Quarter Patching Status', 'Pending')
            if patch_status in ['Completed', 'Failed']:
                if host_group_filter == 'all' or server.get('host_group') == host_group_filter:
                    completed_servers.append(server)
        
        # Generate CSV content
        csv_content = generate_csv_export(completed_servers, quarter)
        
        from flask import Response
        filename = f"completed_patches_Q{quarter}_{host_group_filter}.csv"
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Server Management Routes
@app.route('/update_emails', methods=['POST'])
@login_required
def update_emails():
    try:
        server_name = request.form['server_name']
        incident_ticket = request.form['incident_ticket'].strip()
        patcher_email = request.form['patcher_email'].strip()
        
        # Check permissions for incident tickets and patcher emails
        if incident_ticket and not current_user.can_modify_incident_tickets():
            flash('Access denied: Only administrators can modify incident tickets')
            return redirect(url_for('server_detail', server_name=server_name))
        
        if patcher_email and not current_user.can_modify_patcher_emails():
            flash('Access denied: Only administrators can modify patcher emails')
            return redirect(url_for('server_detail', server_name=server_name))
        
        # Update CSV
        servers = csv_handler.read_servers()
        updated = False
        
        for server in servers:
            if server['Server Name'] == server_name:
                # Check if user can access this server
                can_access = (current_user.is_admin() or 
                             server.get('primary_owner') == current_user.email or 
                             server.get('secondary_owner') == current_user.email)
                
                if can_access:
                    if incident_ticket and current_user.can_modify_incident_tickets():
                        server['incident_ticket'] = incident_ticket
                    if patcher_email and current_user.can_modify_patcher_emails():
                        server['patcher_email'] = patcher_email
                    
                    updated = True
                    break
        
        if updated:
            csv_handler.write_servers(servers)
            flash('Server information updated successfully')
        else:
            flash('Failed to update server information')
        
        return redirect(url_for('server_detail', server_name=server_name))
    
    except Exception as e:
        flash(f'Error updating server information: {e}')
        return redirect(url_for('dashboard'))

@app.route('/approve_schedule', methods=['POST'])
@login_required
def approve_schedule():
    try:
        server_name = request.form['server_name']
        quarter = request.form['quarter']
        
        # Update CSV
        servers = csv_handler.read_servers()
        updated = False
        
        for server in servers:
            if server['Server Name'] == server_name:
                # Check if user can approve this server
                can_approve = (current_user.is_admin() or 
                              server.get('primary_owner') == current_user.email or 
                              server.get('secondary_owner') == current_user.email)
                
                if can_approve:
                    # Set approval status to Approved
                    approval_field = f'Q{quarter} Approval Status'
                    server[approval_field] = 'Approved'
                    
                    # Update patching status if current quarter
                    if quarter == Config.get_current_quarter():
                        server['Current Quarter Patching Status'] = 'Approved'
                    
                    updated = True
                    break
        
        if updated:
            csv_handler.write_servers(servers)
            
            # Send approval confirmation emails to both owners
            try:
                send_approval_confirmation(server, quarter)
            except Exception as email_error:
                # Don't fail the approval if email fails
                print(f"Warning: Failed to send approval confirmation email: {email_error}")
            
            flash(f'Schedule approved successfully for Q{quarter}')
        else:
            flash('Failed to approve schedule')
        
        return redirect(url_for('server_detail', server_name=server_name))
    
    except Exception as e:
        flash(f'Error approving schedule: {e}')
        return redirect(url_for('dashboard'))

def send_approval_confirmation(server, quarter):
    """Send approval confirmation email to both primary and secondary owners"""
    try:
        # Load the approval confirmation template
        template_path = f'{Config.TEMPLATES_DIR}/approval_confirmation.html'
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Get quarter information
        quarter_name = Config.QUARTERS.get(quarter, {}).get('name', f'Q{quarter}')
        quarter_descriptions = {
            '1': 'November to January',
            '2': 'February to April', 
            '3': 'May to July',
            '4': 'August to October'
        }
        quarter_description = quarter_descriptions.get(quarter, 'Unknown')
        
        # Generate server table for the approved server
        server_table = generate_approval_confirmation_table([server], quarter)
        
        # Get current date for approval timestamp
        approval_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare email data
        email_data = {
            'quarter': quarter_name,
            'quarter_description': quarter_description,
            'server_table': server_table,
            'incident_ticket': server.get('incident_ticket', 'Not set'),
            'patcher_email': server.get('patcher_email', 'Not set'),
            'approval_date': approval_date
        }
        
        # Send to primary owner
        primary_owner = server.get('primary_owner')
        if primary_owner:
            email_content = template.format(owner_email=primary_owner, **email_data)
            subject = f"✅ APPROVED: {quarter_name} Patching Schedule Confirmed - {server['Server Name']}"
            email_sender.send_email(primary_owner, subject, email_content, is_html=True)
        
        # Send to secondary owner if exists
        secondary_owner = server.get('secondary_owner')
        if secondary_owner and secondary_owner != primary_owner:
            email_content = template.format(owner_email=secondary_owner, **email_data)
            subject = f"✅ APPROVED: {quarter_name} Patching Schedule Confirmed - {server['Server Name']}"
            email_sender.send_email(secondary_owner, subject, email_content, is_html=True)
            
    except Exception as e:
        print(f"Error sending approval confirmation: {e}")
        raise

def generate_approval_confirmation_table(servers_list, quarter):
    """Generate HTML table for approval confirmation"""
    table_rows = ""
    for server in servers_list:
        # Get patch date and time for the specified quarter
        patch_date = server.get(f'Q{quarter} Patch Date', 'Not Set')
        patch_time = server.get(f'Q{quarter} Patch Time', 'Not Set')
        approval_status = server.get(f'Q{quarter} Approval Status', 'Approved')
        
        table_rows += f"""
        <tr>
            <td>{server['Server Name']}</td>
            <td>{patch_date}</td>
            <td>{patch_time}</td>
            <td>{server['Server Timezone']}</td>
            <td><span style="color: #28a745; font-weight: bold;">{approval_status}</span></td>
            <td><span style="color: #0056b3; font-weight: bold;">{server.get('primary_owner', 'Not Set')}</span></td>
            <td>{server.get('secondary_owner', 'Not Set') if server.get('secondary_owner') else '<em>Not Set</em>'}</td>
            <td>{server.get('incident_ticket', 'Not Set')}</td>
            <td>{server.get('location', '')}</td>
        </tr>
        """
    
    return f"""
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background-color: #f2f2f2;">
            <th>Server Name</th>
            <th>Patch Date</th>
            <th>Patch Time</th>
            <th>Timezone</th>
            <th>Approval Status</th>
            <th>Primary Owner</th>
            <th>Secondary Owner</th>
            <th>Incident Ticket</th>
            <th>Location</th>
        </tr>
        {table_rows}
    </table>
    """

# Admin Panel
@app.route('/admin')
@login_required
def admin_panel():
    """Admin panel for user management"""
    if not current_user.is_admin():
        flash('Access denied: Admin privileges required')
        return redirect(url_for('dashboard'))
    
    try:
        # Get all users
        all_users = UserManager.get_all_users()
        
        # Get server statistics
        all_servers = csv_handler.read_servers()
        current_quarter = Config.get_current_quarter()
        
        # Count servers by status
        stats = {
            'total_servers': len(all_servers),
            'pending': 0,
            'approved': 0,
            'scheduled': 0,
            'completed': 0,
            'failed': 0
        }
        
        for server in all_servers:
            approval_status = server.get(f'Q{current_quarter} Approval Status', 'Pending')
            patch_status = server.get('Current Quarter Patching Status', 'Pending')
            
            # Count by approval status
            if approval_status in ['Approved', 'Auto-Approved']:
                stats['approved'] += 1
            else:
                stats['pending'] += 1
            
            # Count by patch status
            if patch_status == 'Scheduled':
                stats['scheduled'] += 1
            elif patch_status == 'Completed':
                stats['completed'] += 1
            elif patch_status == 'Failed':
                stats['failed'] += 1
        
        # Load admin configuration
        from scripts.admin_manager import AdminManager
        admin_manager = AdminManager()
        admin_config = admin_manager.load_admin_config()
        
        # Load server groups configuration
        server_groups = admin_manager.load_server_groups_config()
        if not server_groups:
            server_groups = {'server_groups': {}}
        
        # Load LDAP configuration
        ldap_config = admin_config.get('ldap_configuration', {})
        
        return render_template(
            'admin_advanced.html',
            users=all_users,
            stats=stats,
            current_quarter=current_quarter,
            admin_config=admin_config,
            server_groups=server_groups,
            ldap_config=ldap_config
        )
    except Exception as e:
        flash(f'Error loading admin panel: {e}')
        return redirect(url_for('dashboard'))

# System Configuration Routes
@app.route('/system_config', methods=['GET', 'POST'])
@login_required
def system_config():
    if not current_user.role == 'admin':
        flash('Admin access required')
        return redirect(url_for('dashboard'))
    
    messages = []
    
    if request.method == 'POST':
        try:
            # Update configuration based on form data
            config_updates = {}
            
            # LDAP settings
            config_updates['LDAP_ENABLED'] = 'ldap_enabled' in request.form
            config_updates['LDAP_SERVER'] = request.form.get('ldap_server', '')
            config_updates['LDAP_BASE_DN'] = request.form.get('ldap_base_dn', '')
            config_updates['LDAP_BIND_DN'] = request.form.get('ldap_bind_dn', '')
            config_updates['LDAP_BIND_PASSWORD'] = request.form.get('ldap_bind_password', '')
            config_updates['ADMIN_NETGROUP'] = request.form.get('admin_netgroup', '')
            
            # Email settings
            config_updates['USE_SENDMAIL'] = 'use_sendmail' in request.form
            config_updates['SMTP_SERVER'] = request.form.get('smtp_server', '')
            config_updates['SMTP_PORT'] = request.form.get('smtp_port', '587')
            config_updates['SMTP_USERNAME'] = request.form.get('smtp_username', '')
            config_updates['SMTP_PASSWORD'] = request.form.get('smtp_password', '')
            config_updates['SMTP_USE_TLS'] = 'smtp_use_tls' in request.form
            
            # Database settings
            config_updates['DB_HOST'] = request.form.get('db_host', '')
            config_updates['DB_PORT'] = request.form.get('db_port', '5432')
            config_updates['DB_NAME'] = request.form.get('db_name', '')
            config_updates['DB_USER'] = request.form.get('db_user', '')
            config_updates['DB_PASSWORD'] = request.form.get('db_password', '')
            
            # Patching script settings
            config_updates['PATCHING_SCRIPT_PATH'] = request.form.get('patching_script_path', '')
            config_updates['VALIDATE_PATCHING_SCRIPT'] = 'validate_patching_script' in request.form
            config_updates['SSH_CONNECTION_TIMEOUT'] = request.form.get('ssh_timeout', '30')
            config_updates['SSH_COMMAND_TIMEOUT'] = request.form.get('ssh_command_timeout', '300')
            config_updates['MAX_RETRY_ATTEMPTS'] = request.form.get('max_retry_attempts', '3')
            
            # Save configuration to environment file
            save_config_to_env(config_updates)
            messages.append(('success', 'Configuration saved successfully!'))
            
        except Exception as e:
            messages.append(('error', f'Error saving configuration: {str(e)}'))
    
    # Get current configuration and system status
    config = Config()
    
    # Check system status
    ldap_status, ldap_status_text = check_ldap_status()
    sendmail_status, sendmail_status_text = check_sendmail_status()
    patching_paused = is_patching_paused()
    schedule_frozen = is_schedule_frozen()
    service_status, service_status_text = check_service_status()
    system_health, system_health_text = check_system_health()
    
    return render_template('system_config.html',
                         config=config,
                         messages=messages,
                         ldap_status=ldap_status,
                         ldap_status_text=ldap_status_text,
                         sendmail_status=sendmail_status,
                         sendmail_status_text=sendmail_status_text,
                         patching_paused=patching_paused,
                         schedule_frozen=schedule_frozen,
                         service_status=service_status,
                         service_status_text=service_status_text,
                         system_health=system_health,
                         system_health_text=system_health_text)

# NOTE: This is app_split2.py - it contains API routes, admin functionality, and advanced features.
# This file should be combined with app_split1.py to create the complete Flask application.

# End of app_split2.py - add the remaining helper functions and main section as needed