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

@app.route('/test_ldap', methods=['POST'])
@login_required
def test_ldap():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        data = request.json
        from utils.nslcd_ldap_auth import NSLCDLDAPAuthenticator
        
        auth = NSLCDLDAPAuthenticator()
        # Test LDAP connection with provided settings
        result = auth.test_ldap_connection(
            server=data['server'],
            base_dn=data['base_dn'],
            bind_dn=data['bind_dn'],
            password=data['password']
        )
        
        return jsonify({'success': result, 'error': None if result else 'Connection failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_email', methods=['POST'])
@login_required
def test_email():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        data = request.json
        from utils.email_sender import EmailSender
        
        email_sender = EmailSender()
        # Test email with provided settings
        result = email_sender.test_email_config(data)
        
        return jsonify({'success': result, 'error': None if result else 'Email test failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_database', methods=['POST'])
@login_required
def test_database():
    if not current_user.role == 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'})
    
    try:
        data = request.json
