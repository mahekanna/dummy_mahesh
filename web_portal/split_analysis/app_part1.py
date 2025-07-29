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
