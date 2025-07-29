# web_portal/app_split1.py - Part 1: Imports, Utilities, User Management, and Core Routes
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import csv
import os
import sys
import calendar

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_handler import CSVHandler
from utils.timezone_handler import TimezoneHandler
from utils.email_sender import EmailSender
from config.settings import Config
from config.users import UserManager

app = Flask(__name__)
# WARNING: Generate a secure secret key for production
# Use: python -c "import secrets; print(secrets.token_hex(32))"
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'CHANGE_ME_IN_PRODUCTION_USE_SECURE_RANDOM_KEY')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize handlers
csv_handler = CSVHandler()
timezone_handler = TimezoneHandler()
email_sender = EmailSender()

def generate_csv_report(servers, report_type, quarter, host_group_filter):
    """Generate CSV-based reports"""
    import io
    from datetime import datetime
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'summary':
        return generate_summary_csv(servers, quarter, writer, output)
    elif report_type == 'detailed':
        return generate_detailed_csv(servers, quarter, writer, output)
    elif report_type == 'completed':
        return generate_completed_csv(servers, quarter, writer, output)
    elif report_type == 'pending':
        return generate_pending_csv(servers, quarter, writer, output)
    elif report_type == 'failed':
        return generate_failed_csv(servers, quarter, writer, output)
    elif report_type == 'upcoming':
        return generate_upcoming_csv(servers, quarter, writer, output)
    else:
        return generate_summary_csv(servers, quarter, writer, output)

def generate_summary_csv(servers, quarter, writer, output):
    """Generate summary report in CSV format"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Header information
    writer.writerow(['Linux Patching Automation System - Summary Report'])
    writer.writerow(['Generated', current_time])
    writer.writerow(['Quarter', f'Q{quarter}'])
    writer.writerow(['Total Servers', len(servers)])
    writer.writerow([])  # Empty row
    
    # Calculate statistics
    stats = {'total': len(servers), 'approved': 0, 'pending': 0, 'scheduled': 0, 'completed': 0, 'failed': 0}
    
    for server in servers:
        approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
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
    
    # Statistics section
    writer.writerow(['Patching Status Summary'])
    writer.writerow(['Status', 'Count', 'Percentage'])
    writer.writerow(['Total Servers', stats['total'], '100.0%'])
    writer.writerow(['Approved', stats['approved'], f"{(stats['approved']/stats['total']*100) if stats['total'] > 0 else 0:.1f}%"])
    writer.writerow(['Pending Approval', stats['pending'], f"{(stats['pending']/stats['total']*100) if stats['total'] > 0 else 0:.1f}%"])
    writer.writerow(['Scheduled', stats['scheduled'], f"{(stats['scheduled']/stats['total']*100) if stats['total'] > 0 else 0:.1f}%"])
    writer.writerow(['Completed', stats['completed'], f"{(stats['completed']/stats['total']*100) if stats['total'] > 0 else 0:.1f}%"])
    writer.writerow(['Failed', stats['failed'], f"{(stats['failed']/stats['total']*100) if stats['total'] > 0 else 0:.1f}%"])
    writer.writerow([])  # Empty row
    
    # Host group breakdown
    host_groups = {}
    for server in servers:
        hg = server.get('host_group', 'unknown')
        if hg not in host_groups:
            host_groups[hg] = 0
        host_groups[hg] += 1
    
    writer.writerow(['Host Group Breakdown'])
    writer.writerow(['Host Group', 'Server Count', 'Percentage'])
    for hg, count in host_groups.items():
        writer.writerow([hg, count, f"{(count/stats['total']*100) if stats['total'] > 0 else 0:.1f}%"])
    
    return output.getvalue()

def generate_detailed_csv(servers, quarter, writer, output):
    """Generate detailed server list in CSV format"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Header information
    writer.writerow(['Linux Patching Automation System - Detailed Server Report'])
    writer.writerow(['Generated', current_time])
    writer.writerow(['Quarter', f'Q{quarter}'])
    writer.writerow(['Total Servers', len(servers)])
    writer.writerow([])  # Empty row
    
    # Column headers
    writer.writerow([
        'Server Name', 'Host Group', 'Primary Owner', 'Secondary Owner',
        'Approval Status', 'Patch Status', 'Patch Date', 'Patch Time',
        'Operating System', 'Environment'
    ])
    
    # Server data
    for server in servers:
        writer.writerow([
            server.get('Server Name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get('secondary_owner', ''),
            server.get(f'Q{quarter} Approval Status', 'Pending'),
            server.get('Current Quarter Patching Status', 'Pending'),
            server.get(f'Q{quarter} Patch Date', ''),
            server.get(f'Q{quarter} Patch Time', ''),
            server.get('Operating System', ''),
            server.get('Environment', '')
        ])
    
    return output.getvalue()

def generate_completed_csv(servers, quarter, writer, output):
    """Generate completed patches report in CSV format"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Header information
    writer.writerow(['Linux Patching Automation System - Completed Patches Report'])
    writer.writerow(['Generated', current_time])
    writer.writerow(['Quarter', f'Q{quarter}'])
    writer.writerow([])  # Empty row
    
    # Filter completed/failed servers
    completed_servers = [s for s in servers if s.get('Current Quarter Patching Status') in ['Completed', 'Failed']]
    
    writer.writerow(['Total Completed/Failed Servers', len(completed_servers)])
    writer.writerow([])  # Empty row
    
    # Column headers
    writer.writerow([
        'Server Name', 'Host Group', 'Primary Owner', 'Patch Date', 'Patch Time',
        'Status', 'Completion Date', 'Duration', 'Notes'
    ])
    
    # Server data
    for server in completed_servers:
        writer.writerow([
            server.get('Server Name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get(f'Q{quarter} Patch Date', ''),
            server.get(f'Q{quarter} Patch Time', ''),
            server.get('Current Quarter Patching Status', ''),
            server.get('Completion Date', ''),
            server.get('Duration', ''),
            server.get('Notes', '')
        ])
    
    return output.getvalue()

def generate_pending_csv(servers, quarter, writer, output):
    """Generate pending approvals report in CSV format"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Header information
    writer.writerow(['Linux Patching Automation System - Pending Approvals Report'])
    writer.writerow(['Generated', current_time])
    writer.writerow(['Quarter', f'Q{quarter}'])
    writer.writerow([])  # Empty row
    
    # Filter pending servers
    pending_servers = [s for s in servers if s.get(f'Q{quarter} Approval Status', 'Pending') == 'Pending']
    
    writer.writerow(['Total Pending Approvals', len(pending_servers)])
    writer.writerow([])  # Empty row
    
    # Column headers
    writer.writerow([
        'Server Name', 'Host Group', 'Primary Owner', 'Secondary Owner',
        'Patch Date', 'Patch Time', 'Days Until Patch', 'Priority'
    ])
    
    # Server data
    for server in pending_servers:
        patch_date = server.get(f'Q{quarter} Patch Date', '')
        days_until = ''
        if patch_date:
            try:
                patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                days_until = (patch_dt - datetime.now()).days
            except ValueError:
                pass
        
        writer.writerow([
            server.get('Server Name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get('secondary_owner', ''),
            patch_date,
            server.get(f'Q{quarter} Patch Time', ''),
            days_until,
            'High' if isinstance(days_until, int) and days_until <= 3 else 'Normal'
        ])
    
    return output.getvalue()

def generate_failed_csv(servers, quarter, writer, output):
    """Generate failed patches report in CSV format"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Header information
    writer.writerow(['Linux Patching Automation System - Failed Patches Report'])
    writer.writerow(['Generated', current_time])
    writer.writerow(['Quarter', f'Q{quarter}'])
    writer.writerow([])  # Empty row
    
    # Filter failed servers
    failed_servers = [s for s in servers if s.get('Current Quarter Patching Status') == 'Failed']
    
    writer.writerow(['Total Failed Patches', len(failed_servers)])
    writer.writerow([])  # Empty row
    
    # Column headers
    writer.writerow([
        'Server Name', 'Host Group', 'Primary Owner', 'Patch Date', 'Patch Time',
        'Failure Date', 'Error Description', 'Retry Count', 'Next Retry'
    ])
    
    # Server data
    for server in failed_servers:
        writer.writerow([
            server.get('Server Name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get(f'Q{quarter} Patch Date', ''),
            server.get(f'Q{quarter} Patch Time', ''),
            server.get('Failure Date', ''),
            server.get('Error Description', ''),
            server.get('Retry Count', '0'),
            server.get('Next Retry', '')
        ])
    
    return output.getvalue()

def generate_upcoming_csv(servers, quarter, writer, output):
    """Generate upcoming patches report in CSV format"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Header information
    writer.writerow(['Linux Patching Automation System - Upcoming Patches Report'])
    writer.writerow(['Generated', current_time])
    writer.writerow(['Quarter', f'Q{quarter}'])
    writer.writerow([])  # Empty row
    
    # Filter upcoming patches (next 7 days)
    upcoming_servers = []
    for server in servers:
        patch_date = server.get(f'Q{quarter} Patch Date', '')
        if patch_date:
            try:
                patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                days_until = (patch_dt - datetime.now()).days
                if 0 <= days_until <= 7:
                    upcoming_servers.append((server, days_until))
            except ValueError:
                pass
    
    # Sort by days until patch
    upcoming_servers.sort(key=lambda x: x[1])
    
    writer.writerow(['Total Upcoming Patches (Next 7 Days)', len(upcoming_servers)])
    writer.writerow([])  # Empty row
    
    # Column headers
    writer.writerow([
        'Server Name', 'Host Group', 'Primary Owner', 'Patch Date', 'Patch Time',
        'Days Until Patch', 'Approval Status', 'Readiness'
    ])
    
    # Server data
    for server, days_until in upcoming_servers:
        approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
        readiness = 'Ready' if approval_status in ['Approved', 'Auto-Approved'] else 'Awaiting Approval'
        
        writer.writerow([
            server.get('Server Name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get(f'Q{quarter} Patch Date', ''),
            server.get(f'Q{quarter} Patch Time', ''),
            days_until,
            approval_status,
            readiness
        ])
    
    return output.getvalue()

def generate_summary_report(servers, quarter, report_lines):
    """Generate summary report"""
    # Calculate statistics
    stats = {'total': len(servers), 'approved': 0, 'pending': 0, 'scheduled': 0, 'completed': 0, 'failed': 0}
    
    for server in servers:
        approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
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
    
    report_lines.append("PATCHING STATUS SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Servers:        {stats['total']:>10}")
    report_lines.append(f"Approved:             {stats['approved']:>10}")
    report_lines.append(f"Pending Approval:     {stats['pending']:>10}")
    report_lines.append(f"Scheduled:            {stats['scheduled']:>10}")
    report_lines.append(f"Completed:            {stats['completed']:>10}")
    report_lines.append(f"Failed:               {stats['failed']:>10}")
    report_lines.append("")
    
    # Approval percentage
    approval_pct = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
    completion_pct = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
    
    report_lines.append("PROGRESS METRICS")
    report_lines.append("-" * 40)
    report_lines.append(f"Approval Rate:        {approval_pct:>9.1f}%")
    report_lines.append(f"Completion Rate:      {completion_pct:>9.1f}%")
    report_lines.append("")
    
    # Host group breakdown
    host_groups = {}
    for server in servers:
        hg = server.get('host_group', 'unknown')
        if hg not in host_groups:
            host_groups[hg] = 0
        host_groups[hg] += 1
    
    report_lines.append("HOST GROUP BREAKDOWN")
    report_lines.append("-" * 40)
    for hg, count in sorted(host_groups.items()):
        report_lines.append(f"{hg:<25} {count:>10}")
    
    return "\n".join(report_lines)

def generate_detailed_report(servers, quarter, report_lines):
    """Generate detailed server list"""
    report_lines.append("DETAILED SERVER LIST")
    report_lines.append("-" * 120)
    report_lines.append(f"{'Server Name':<35} {'Host Group':<15} {'Approval':<15} {'Status':<15} {'Patch Date':<12} {'Owner':<20}")
    report_lines.append("-" * 120)
    
    for server in servers:
        server_name = server.get('Server Name', '')[:34]
        host_group = server.get('host_group', '')[:14]
        approval = server.get(f'Q{quarter} Approval Status', 'Pending')[:14]
        status = server.get('Current Quarter Patching Status', 'Pending')[:14]
        patch_date = server.get(f'Q{quarter} Patch Date', '')[:11]
        owner = server.get('primary_owner', '')[:19]
        
        report_lines.append(f"{server_name:<35} {host_group:<15} {approval:<15} {status:<15} {patch_date:<12} {owner:<20}")
    
    return "\n".join(report_lines)

def generate_completed_report(servers, quarter, report_lines):
    """Generate completed patches report"""
    completed_servers = [s for s in servers if s.get('Current Quarter Patching Status') in ['Completed', 'Failed']]
    
    report_lines.append(f"COMPLETED PATCHES ({len(completed_servers)} servers)")
    report_lines.append("-" * 100)
    report_lines.append(f"{'Server Name':<30} {'Host Group':<15} {'Status':<12} {'Date':<12} {'Owner':<20}")
    report_lines.append("-" * 100)
    
    for server in completed_servers:
        server_name = server.get('Server Name', '')[:29]
        host_group = server.get('host_group', '')[:14]
        status = server.get('Current Quarter Patching Status', '')[:11]
        patch_date = server.get(f'Q{quarter} Patch Date', '')[:11]
        owner = server.get('primary_owner', '')[:19]
        
        report_lines.append(f"{server_name:<30} {host_group:<15} {status:<12} {patch_date:<12} {owner:<20}")
    
    return "\n".join(report_lines)

def generate_pending_report(servers, quarter, report_lines):
    """Generate pending approvals report"""
    pending_servers = [s for s in servers if s.get(f'Q{quarter} Approval Status', 'Pending') == 'Pending']
    
    report_lines.append(f"PENDING APPROVALS ({len(pending_servers)} servers)")
    report_lines.append("-" * 100)
    report_lines.append(f"{'Server Name':<30} {'Host Group':<15} {'Proposed Date':<15} {'Owner':<30}")
    report_lines.append("-" * 100)
    
    for server in pending_servers:
        server_name = server.get('Server Name', '')[:29]
        host_group = server.get('host_group', '')[:14]
        patch_date = server.get(f'Q{quarter} Patch Date', '')[:14]
        owner = server.get('primary_owner', '')[:29]
        
        report_lines.append(f"{server_name:<30} {host_group:<15} {patch_date:<15} {owner:<30}")
    
    return "\n".join(report_lines)

def generate_failed_report(servers, quarter, report_lines):
    """Generate failed patches report"""
    failed_servers = [s for s in servers if s.get('Current Quarter Patching Status') == 'Failed']
    
    report_lines.append(f"FAILED PATCHES ({len(failed_servers)} servers)")
    report_lines.append("-" * 100)
    report_lines.append(f"{'Server Name':<30} {'Host Group':<15} {'Date':<12} {'Owner':<30}")
    report_lines.append("-" * 100)
    
    for server in failed_servers:
        server_name = server.get('Server Name', '')[:29]
        host_group = server.get('host_group', '')[:14]
        patch_date = server.get(f'Q{quarter} Patch Date', '')[:11]
        owner = server.get('primary_owner', '')[:29]
        
        report_lines.append(f"{server_name:<30} {host_group:<15} {patch_date:<12} {owner:<30}")
    
    return "\n".join(report_lines)

def generate_upcoming_report(servers, quarter, report_lines):
    """Generate upcoming patches report"""
    upcoming_servers = []
    for server in servers:
        patch_date = server.get(f'Q{quarter} Patch Date')
        if patch_date:
            try:
                patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                days_until = (patch_dt - datetime.now()).days
                if 0 <= days_until <= 7:
                    upcoming_servers.append((server, days_until))
            except ValueError:
                pass
    
    upcoming_servers.sort(key=lambda x: x[1])
    
    report_lines.append(f"UPCOMING PATCHES - NEXT 7 DAYS ({len(upcoming_servers)} servers)")
    report_lines.append("-" * 100)
    report_lines.append(f"{'Server Name':<30} {'Host Group':<15} {'Date':<12} {'Days':<6} {'Owner':<25}")
    report_lines.append("-" * 100)
    
    for server, days_until in upcoming_servers:
        server_name = server.get('Server Name', '')[:29]
        host_group = server.get('host_group', '')[:14]
        patch_date = server.get(f'Q{quarter} Patch Date', '')[:11]
        owner = server.get('primary_owner', '')[:24]
        
        report_lines.append(f"{server_name:<30} {host_group:<15} {patch_date:<12} {days_until:<6} {owner:<25}")
    
    return "\n".join(report_lines)

def generate_csv_export(servers, quarter):
    """Generate CSV export for completed servers"""
    import io
    import csv as csv_module
    
    output = io.StringIO()
    writer = csv_module.writer(output)
    
    # Header
    writer.writerow([
        'Server Name', 'Host Group', 'Approval Status', 'Patch Status', 
        'Patch Date', 'Patch Time', 'Primary Owner', 'Secondary Owner',
        'Location', 'Operating System', 'Last Updated'
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

# NOTE: This is app_split1.py - it contains the core functionality.
# For the complete application, import and combine with app_split2.py