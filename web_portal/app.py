# web_portal/app.py
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
    def __init__(self, email, role=None, name=None, permissions=None):
        self.id = email
        self.email = email
        self.role = role
        self.name = name
        self.permissions = permissions or []
        
    @staticmethod
    def get(email):
        user_info = UserManager.get_user_info(email)
        if user_info:
            return User(
                email=user_info['email'],
                role=user_info['role'],
                name=user_info['name'],
                permissions=user_info['permissions']
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
        email = request.form['email']
        password = request.form['password']
        
        # Use UserManager for authentication
        try:
            # Try the new method name first
            user_data = UserManager.authenticate_user(email, password)
        except AttributeError:
            # Fall back to old method name if new one doesn't exist
            user_data = UserManager.authenticate(email, password)
        
        if user_data:
            user = User(
                email=user_data['email'],
                role=user_data['role'],
                name=user_data['name'],
                permissions=user_data['permissions']
            )
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
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
        # Admins can see all servers, regular users only their own
        if current_user.is_admin():
            user_servers = csv_handler.read_servers()
        else:
            user_servers = csv_handler.get_servers_by_owner(current_user.email)
        
        # Get current quarter
        current_quarter = Config.get_current_quarter()
        quarter_name = Config.QUARTERS.get(current_quarter, {}).get('name', f'Q{current_quarter}')
        
        return render_template(
            'dashboard.html', 
            servers=user_servers, 
            current_quarter=current_quarter,
            quarter_name=quarter_name,
            quarters=Config.QUARTERS,
            user_role=current_user.role,
            user_name=current_user.name
        )
    except Exception as e:
        flash(f'Error loading dashboard: {e}')
        return render_template('dashboard.html', 
                             servers=[], 
                             current_quarter=Config.get_current_quarter(),
                             quarter_name=Config.QUARTERS.get(Config.get_current_quarter(), {}).get('name', 'Current Quarter'),
                             quarters=Config.QUARTERS,
                             user_role=getattr(current_user, 'role', 'user'),
                             user_name=getattr(current_user, 'name', 'User'))

@app.route('/server/<server_name>')
@login_required
def server_detail(server_name):
    try:
        servers = csv_handler.read_servers()
        server = None
        
        for s in servers:
            if s['Server Name'] == server_name:
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
        
        return render_template(
            'server_detail.html', 
            server=server, 
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
