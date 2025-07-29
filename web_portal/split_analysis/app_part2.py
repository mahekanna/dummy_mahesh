    ])
    
    # Data rows
    for server in servers:
        writer.writerow([
            server.get('Server Name', ''),
            server.get('host_group', ''),
            server.get(f'Q{quarter} Approval Status', ''),
            server.get('Current Quarter Patching Status', ''),
            server.get(f'Q{quarter} Patch Date', ''),
            server.get(f'Q{quarter} Patch Time', ''),
            server.get('primary_owner', ''),
            server.get('secondary_owner', ''),
            server.get('location', ''),
            server.get('operating_system', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return output.getvalue()

class User(UserMixin):
    def __init__(self, email, role=None, name=None, permissions=None, username=None, auth_method='local', **kwargs):
        self.id = email
        self.email = email
        self.username = username or email.split('@')[0] if '@' in email else email
        self.role = role
        self.name = name
        self.permissions = permissions or []
        self.auth_method = auth_method
        self.ldap_groups = kwargs.get('ldap_groups', [])
        self.department = kwargs.get('department', '')
        self.title = kwargs.get('title', '')
        
    @staticmethod
    def get(email_or_username):
        # Initialize UserManager instance for new methods
        user_manager = UserManager()
        user_info = user_manager.get_user_info(email_or_username)
        if user_info:
            return User(
                email=user_info['email'],
                username=user_info.get('username', email_or_username),
                role=user_info['role'],
                name=user_info['name'],
                permissions=user_info['permissions'],
                auth_method=user_info.get('auth_method', 'local'),
                ldap_groups=user_info.get('ldap_groups', []),
                department=user_info.get('department', ''),
                title=user_info.get('title', '')
            )
        return None
    
    def has_permission(self, permission):
        return permission in self.permissions
    
    def is_admin(self):
        return self.has_permission('system_admin')
    
    def can_modify_incident_tickets(self):
        return self.has_permission('update_incident_tickets')
    
    def can_modify_patcher_emails(self):
        return self.has_permission('update_patcher_emails')
    
    def get_accessible_servers(self):
        """Get servers that this user can access"""
        user_manager = UserManager()
        return user_manager.get_user_servers(self.email, self.role)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['email']  # Can be username or email
        password = request.form['password']
        
        # Use UserManager instance for authentication (LDAP + fallback)
        user_manager = UserManager()
        user_data = user_manager.authenticate_user(username_or_email, password)
        
        if user_data:
            user = User(
                email=user_data['email'],
                username=user_data.get('username', username_or_email),
                role=user_data['role'],
                name=user_data['name'],
                permissions=user_data['permissions'],
                auth_method=user_data.get('auth_method', 'local'),
                ldap_groups=user_data.get('ldap_groups', []),
                department=user_data.get('department', ''),
                title=user_data.get('title', '')
            )
            login_user(user)
            
            # Log successful authentication
            auth_method = user_data.get('auth_method', 'local')
            app.logger.info(f"User {user_data['name']} ({username_or_email}) logged in via {auth_method}")
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get servers based on user permissions and ownership
        user_servers = current_user.get_accessible_servers()
        
        # Convert normalized field names back to template-expected format
        template_servers = []
        for server in user_servers:
            template_server = {
                'Server Name': server.get('server_name', ''),
                'Server Timezone': server.get('server_timezone', ''),
                'Q1 Patch Date': server.get('q1_patch_date', ''),
                'Q1 Patch Time': server.get('q1_patch_time', ''),
                'Q2 Patch Date': server.get('q2_patch_date', ''),
                'Q2 Patch Time': server.get('q2_patch_time', ''),
                'Q3 Patch Date': server.get('q3_patch_date', ''),
                'Q3 Patch Time': server.get('q3_patch_time', ''),
                'Q4 Patch Date': server.get('q4_patch_date', ''),
                'Q4 Patch Time': server.get('q4_patch_time', ''),
                'Q1 Approval Status': server.get('q1_approval_status', 'Pending'),
                'Q2 Approval Status': server.get('q2_approval_status', 'Pending'),
                'Q3 Approval Status': server.get('q3_approval_status', 'Pending'),
                'Q4 Approval Status': server.get('q4_approval_status', 'Pending'),
                'Current Quarter Patching Status': server.get('current_quarter_status', 'Pending'),
                'primary_owner': server.get('primary_owner', ''),
                'secondary_owner': server.get('secondary_owner', ''),
                'location': server.get('location', ''),
                'incident_ticket': server.get('incident_ticket', ''),
                'patcher_email': server.get('patcher_email', ''),
                'host_group': server.get('host_group', ''),
                'operating_system': server.get('operating_system', ''),
                'environment': server.get('environment', '')
            }
            template_servers.append(template_server)
        
        # Get current quarter
        current_quarter = Config.get_current_quarter()
        quarter_name = Config.QUARTERS.get(current_quarter, {}).get('name', f'Q{current_quarter}')
        
        return render_template(
            'dashboard.html', 
            servers=template_servers, 
            current_quarter=current_quarter,
            quarter_name=quarter_name,
            quarters=Config.QUARTERS,
            user_role=current_user.role,
            user_name=current_user.name,
            user_auth_method=getattr(current_user, 'auth_method', 'local'),
            user_department=getattr(current_user, 'department', ''),
            user_title=getattr(current_user, 'title', '')
        )
    except Exception as e:
        flash(f'Error loading dashboard: {e}')
        return render_template('dashboard.html', 
                             servers=[], 
                             current_quarter=Config.get_current_quarter(),
                             quarter_name=Config.QUARTERS.get(Config.get_current_quarter(), {}).get('name', 'Current Quarter'),
                             quarters=Config.QUARTERS,
                             user_role=getattr(current_user, 'role', 'user'),
                             user_name=getattr(current_user, 'name', 'User'),
                             user_auth_method='local',
                             user_department='',
                             user_title='')

@app.route('/server/<server_name>')
@login_required
def server_detail(server_name):
    try:
        servers = csv_handler.read_servers()
        server = None
        
        for s in servers:
            # Check normalized field name 'server_name'
            if s.get('server_name') == server_name:
                # Admins can access all servers, regular users only their own
                if (current_user.is_admin() or 
                    s.get('primary_owner') == current_user.email or 
                    s.get('secondary_owner') == current_user.email):
                    server = s
                    break
        
        if not server:
            flash('Server not found or access denied')
            return redirect(url_for('dashboard'))
        
        # Get current quarter
        current_quarter = Config.get_current_quarter()
        quarter_name = Config.QUARTERS.get(current_quarter, {}).get('name', f'Q{current_quarter}')
        
        # Convert normalized field names back to template-expected format
        template_server = {
            'Server Name': server.get('server_name', ''),
            'Server Timezone': server.get('server_timezone', ''),
            'Q1 Patch Date': server.get('q1_patch_date', ''),
            'Q1 Patch Time': server.get('q1_patch_time', ''),
            'Q2 Patch Date': server.get('q2_patch_date', ''),
            'Q2 Patch Time': server.get('q2_patch_time', ''),
            'Q3 Patch Date': server.get('q3_patch_date', ''),
            'Q3 Patch Time': server.get('q3_patch_time', ''),
            'Q4 Patch Date': server.get('q4_patch_date', ''),
            'Q4 Patch Time': server.get('q4_patch_time', ''),
            'Q1 Approval Status': server.get('q1_approval_status', 'Pending'),
            'Q2 Approval Status': server.get('q2_approval_status', 'Pending'),
            'Q3 Approval Status': server.get('q3_approval_status', 'Pending'),
            'Q4 Approval Status': server.get('q4_approval_status', 'Pending'),
            'Current Quarter Patching Status': server.get('current_quarter_status', 'Pending'),
            'primary_owner': server.get('primary_owner', ''),
            'secondary_owner': server.get('secondary_owner', ''),
            'location': server.get('location', ''),
            'incident_ticket': server.get('incident_ticket', ''),
            'patcher_email': server.get('patcher_email', ''),
            'host_group': server.get('host_group', ''),
            'operating_system': server.get('operating_system', ''),
            'environment': server.get('environment', '')
        }
        
        return render_template(
            'server_detail.html', 
            server=template_server, 
            current_quarter=current_quarter,
            quarter_name=quarter_name,
            quarters=Config.QUARTERS,
            user_role=current_user.role,
            can_modify_incident_tickets=current_user.can_modify_incident_tickets(),
            can_modify_patcher_emails=current_user.can_modify_patcher_emails()
        )
    except Exception as e:
        flash(f'Error loading server details: {e}')
        return redirect(url_for('dashboard'))

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
