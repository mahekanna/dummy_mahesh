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
