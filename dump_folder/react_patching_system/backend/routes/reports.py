"""
Reports API routes - converted from Flask reports functionality
"""

from flask import Blueprint, request, jsonify, Response
import sys
import os
import io
import csv
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from utils.csv_handler import CSVHandler
from config.settings import Config
from scripts.admin_manager import AdminManager

reports_bp = Blueprint('reports', __name__)

# Initialize handlers
csv_handler = CSVHandler()

@reports_bp.route('/api/reports/dashboard', methods=['GET'])
def api_reports_data(current_user):
    """API endpoint for reports dashboard data"""
    try:
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
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Filter by host group if specified
        if host_group_filter != 'all':
            servers = [s for s in servers if s.get('host_group') == host_group_filter]
        
        # Filter by status if specified
        if status_filter != 'all':
            filtered_servers = []
            for server in servers:
                approval_status = server.get(f'q{quarter}_approval_status', 'Pending')
                patch_status = server.get('current_quarter_status', 'Pending')
                
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
            
            approval_status = server.get(f'q{quarter}_approval_status', 'Pending')
            patch_status = server.get('current_quarter_status', 'Pending')
            
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
            'completed': [2, 5, 8, len([s for s in servers if s.get('current_quarter_status') == 'Completed'])],
            'scheduled': [1, 3, 6, len([s for s in servers if s.get('current_quarter_status') == 'Scheduled'])]
        }
        
        # Find attention required items
        attention_required = []
        for server in servers:
            approval_status = server.get(f'q{quarter}_approval_status', 'Pending')
            patch_date = server.get(f'q{quarter}_patch_date')
            
            if approval_status == 'Pending' and patch_date:
                try:
                    patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                    days_until = (patch_dt - datetime.now()).days
                    if days_until <= 3:
                        attention_required.append({
                            'server': server['server_name'],
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
            patch_status = server.get('current_quarter_status', 'Pending')
            if patch_status in ['Completed', 'Failed']:
                completed_servers.append({
                    'server_name': server.get('server_name', ''),
                    'host_group': server.get('host_group', ''),
                    'patch_date': server.get(f'q{quarter}_patch_date', ''),
                    'patch_time': server.get(f'q{quarter}_patch_time', ''),
                    'completion_date': server.get('last_patch_date', ''),
                    'duration': server.get('patch_duration', ''),
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

@reports_bp.route('/api/reports/csv', methods=['GET'])
def api_reports_csv(current_user):
    """Generate CSV-based reports with filters"""
    try:
        report_type = request.args.get('type', 'summary')
        quarter = request.args.get('quarter', Config.get_current_quarter())
        host_group_filter = request.args.get('host_group', 'all')
        status_filter = request.args.get('status', 'all')
        format_type = request.args.get('format', 'display')
        
        # Get servers data
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Filter by host group if specified
        if host_group_filter != 'all':
            servers = [s for s in servers if s.get('host_group') == host_group_filter]
        
        # Filter by status if specified
        if status_filter != 'all':
            filtered_servers = []
            for server in servers:
                approval_status = server.get(f'q{quarter}_approval_status', 'Pending')
                patch_status = server.get('current_quarter_status', 'Pending')
                
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
            filename = f"{report_type}_report_Q{quarter}_{host_group_filter}_{status_filter}.csv"
            return Response(
                report_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
        else:
            return Response(report_content, mimetype='text/csv')
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error generating report: {str(e)}'}), 500

@reports_bp.route('/api/reports/export/completed')
def api_export_completed(current_user):
    """Export completed servers list"""
    try:
        quarter = request.args.get('quarter', Config.get_current_quarter())
        host_group_filter = request.args.get('host_group', 'all')
        
        # Get servers data
        servers = csv_handler.read_servers(normalize_fields=True)
        
        # Filter by host group and completed status
        completed_servers = []
        for server in servers:
            patch_status = server.get('current_quarter_status', 'Pending')
            if patch_status in ['Completed', 'Failed']:
                if host_group_filter == 'all' or server.get('host_group') == host_group_filter:
                    completed_servers.append(server)
        
        # Generate CSV content
        csv_content = generate_csv_export(completed_servers, quarter)
        
        filename = f"completed_patches_Q{quarter}_{host_group_filter}.csv"
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def generate_csv_report(servers, report_type, quarter, host_group_filter):
    """Generate CSV-based reports (reused from Flask app)"""
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
        approval_status = server.get(f'q{quarter}_approval_status', 'Pending')
        patch_status = server.get('current_quarter_status', 'Pending')
        
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
            server.get('server_name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get('secondary_owner', ''),
            server.get(f'q{quarter}_approval_status', 'Pending'),
            server.get('current_quarter_status', 'Pending'),
            server.get(f'q{quarter}_patch_date', ''),
            server.get(f'q{quarter}_patch_time', ''),
            server.get('operating_system', ''),
            server.get('environment', '')
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
    completed_servers = [s for s in servers if s.get('current_quarter_status') in ['Completed', 'Failed']]
    
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
            server.get('server_name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get(f'q{quarter}_patch_date', ''),
            server.get(f'q{quarter}_patch_time', ''),
            server.get('current_quarter_status', ''),
            server.get('completion_date', ''),
            server.get('duration', ''),
            server.get('notes', '')
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
    pending_servers = [s for s in servers if s.get(f'q{quarter}_approval_status', 'Pending') == 'Pending']
    
    writer.writerow(['Total Pending Approvals', len(pending_servers)])
    writer.writerow([])  # Empty row
    
    # Column headers
    writer.writerow([
        'Server Name', 'Host Group', 'Primary Owner', 'Secondary Owner',
        'Patch Date', 'Patch Time', 'Days Until Patch', 'Priority'
    ])
    
    # Server data
    for server in pending_servers:
        patch_date = server.get(f'q{quarter}_patch_date', '')
        days_until = ''
        if patch_date:
            try:
                patch_dt = datetime.strptime(patch_date, '%Y-%m-%d')
                days_until = (patch_dt - datetime.now()).days
            except ValueError:
                pass
        
        writer.writerow([
            server.get('server_name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get('secondary_owner', ''),
            patch_date,
            server.get(f'q{quarter}_patch_time', ''),
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
    failed_servers = [s for s in servers if s.get('current_quarter_status') == 'Failed']
    
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
            server.get('server_name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get(f'q{quarter}_patch_date', ''),
            server.get(f'q{quarter}_patch_time', ''),
            server.get('failure_date', ''),
            server.get('error_description', ''),
            server.get('retry_count', '0'),
            server.get('next_retry', '')
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
        patch_date = server.get(f'q{quarter}_patch_date', '')
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
        approval_status = server.get(f'q{quarter}_approval_status', 'Pending')
        readiness = 'Ready' if approval_status in ['Approved', 'Auto-Approved'] else 'Awaiting Approval'
        
        writer.writerow([
            server.get('server_name', ''),
            server.get('host_group', ''),
            server.get('primary_owner', ''),
            server.get(f'q{quarter}_patch_date', ''),
            server.get(f'q{quarter}_patch_time', ''),
            days_until,
            approval_status,
            readiness
        ])
    
    return output.getvalue()

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
            server.get('server_name', ''),
            server.get('host_group', ''),
            server.get(f'q{quarter}_approval_status', ''),
            server.get('current_quarter_status', ''),
            server.get(f'q{quarter}_patch_date', ''),
            server.get(f'q{quarter}_patch_time', ''),
            server.get('primary_owner', ''),
            server.get('secondary_owner', ''),
            server.get('location', ''),
            server.get('operating_system', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return output.getvalue()