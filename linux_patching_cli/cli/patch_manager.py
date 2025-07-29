#!/usr/bin/env python3
"""
Linux Patching Automation - Main CLI Interface
Complete command-line interface for all patching operations
"""

import click
import sys
import os
import json
from datetime import datetime
from tabulate import tabulate
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.patching_engine import PatchingEngine
from utils.csv_handler import CSVHandler
from utils.logger import get_logger
from utils.ssh_handler import test_ssh_connectivity
from config.settings import Config

# Initialize components
config = Config()
logger = get_logger('patch_manager')
patching_engine = PatchingEngine(config)
csv_handler = CSVHandler(config.DATA_DIR)

def print_json(data):
    """Print data in JSON format"""
    click.echo(json.dumps(data, indent=2, default=str))

def print_table(data, headers):
    """Print data in table format"""
    click.echo(tabulate(data, headers=headers, tablefmt='grid'))

def format_status(status):
    """Format status with colors"""
    colors = {
        'success': 'green',
        'completed': 'green',
        'approved': 'green',
        'passed': 'green',
        'failed': 'red',
        'error': 'red',
        'pending': 'yellow',
        'warning': 'yellow',
        'scheduled': 'blue',
        'in_progress': 'cyan'
    }
    
    color = colors.get(status.lower(), 'white')
    return click.style(status, fg=color)

@click.group()
@click.version_option(version='1.0.0')
@click.option('--config-file', '-c', help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, config_file, debug):
    """Linux Patching Automation CLI - Complete Management Tool"""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config_file
    ctx.obj['debug'] = debug
    
    if debug:
        logger.logger.setLevel('DEBUG')
        click.echo("Debug mode enabled")

# ============================================================================
# PATCH COMMANDS
# ============================================================================

@cli.group()
def patch():
    """Patching operations"""
    pass

@patch.command()
@click.option('--server', '-s', required=True, help='Server name to patch')
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to patch (default: current quarter)')
@click.option('--user', '-u', default='system', help='Operator username')
@click.option('--dry-run', is_flag=True, help='Perform dry run without actual patching')
@click.option('--force', is_flag=True, help='Force patching even if pre-checks fail')
@click.option('--skip-precheck', is_flag=True, help='Skip pre-check validation')
@click.option('--skip-postcheck', is_flag=True, help='Skip post-check validation')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def server(server, quarter, user, dry_run, force, skip_precheck, skip_postcheck, output):
    """Patch a single server"""
    click.echo(f"{'Dry run' if dry_run else 'Patching'} server: {server}")
    
    if dry_run:
        # Just run pre-checks
        result = patching_engine.run_precheck(server, quarter, user)
    else:
        if not force and not click.confirm(f"Are you sure you want to patch {server}?"):
            click.echo("Patching cancelled.")
            return
        
        result = patching_engine.patch_server(
            server=server,
            quarter=quarter,
            user=user,
            force=force,
            skip_precheck=skip_precheck,
            skip_postcheck=skip_postcheck
        )
    
    if output == 'json':
        print_json(result)
    else:
        if result['success']:
            click.echo(f"✓ {format_status('Success')}: {server}")
            if not dry_run:
                click.echo(f"  Duration: {result.get('duration', 'N/A')}")
                click.echo(f"  Patches Applied: {result.get('patches_applied', 0)}")
                click.echo(f"  Reboot Required: {result.get('reboot_required', 'No')}")
        else:
            click.echo(f"✗ {format_status('Failed')}: {server}")
            click.echo(f"  Error: {result.get('error', 'Unknown error')}")

@patch.command()
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to process')
@click.option('--group', '-g', help='Host group to process')
@click.option('--environment', '-e', help='Environment to process')
@click.option('--user', '-u', default='system', help='Operator username')
@click.option('--dry-run', is_flag=True, help='Show what would be patched')
@click.option('--force', is_flag=True, help='Force patching without approvals')
@click.option('--max-parallel', type=int, help='Maximum parallel operations')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def batch(quarter, group, environment, user, dry_run, force, max_parallel, output):
    """Execute batch patching for multiple servers"""
    click.echo(f"Starting batch {'dry run' if dry_run else 'patching'}...")
    
    if quarter:
        click.echo(f"Quarter: {quarter}")
    if group:
        click.echo(f"Host Group: {group}")
    if environment:
        click.echo(f"Environment: {environment}")
    
    # Get servers for patching
    servers = patching_engine.get_servers_for_patching(
        quarter=quarter,
        group=group,
        environment=environment,
        approved_only=not force
    )
    
    if not servers:
        click.echo("No servers found for patching.")
        return
    
    click.echo(f"Found {len(servers)} servers for patching")
    
    if dry_run:
        if output == 'json':
            print_json([{'name': s['server_name'], 'group': s.get('host_group', 'N/A')} for s in servers])
        else:
            headers = ['Server', 'Host Group', 'Environment', 'OS', 'Patch Date']
            table_data = []
            for server in servers:
                patch_date = server.get(f'q{quarter[-1] if quarter else patching_engine.get_current_quarter()[-1]}_patch_date', 'N/A')
                table_data.append([
                    server['server_name'],
                    server.get('host_group', 'N/A'),
                    server.get('environment', 'N/A'),
                    server.get('operating_system', 'N/A'),
                    patch_date
                ])
            print_table(table_data, headers)
    else:
        if not force and not click.confirm(f"Patch {len(servers)} servers?"):
            return
        
        server_names = [s['server_name'] for s in servers]
        
        with click.progressbar(length=len(server_names), label='Patching servers') as bar:
            results = patching_engine.batch_patch(
                servers=server_names,
                quarter=quarter,
                group=group,
                environment=environment,
                user=user,
                max_parallel=max_parallel,
                force=force
            )
            bar.update(len(server_names))
        
        if output == 'json':
            print_json(results)
        else:
            # Display results summary
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            
            click.echo(f"\nBatch Patching Results:")
            click.echo(f"  Total: {len(results)}")
            click.echo(f"  {format_status('Success')}: {successful}")
            click.echo(f"  {format_status('Failed')}: {failed}")
            click.echo(f"  Success Rate: {(successful/len(results)*100):.1f}%")
            
            # Show failed servers
            if failed > 0:
                click.echo(f"\nFailed Servers:")
                for result in results:
                    if not result['success']:
                        click.echo(f"  ✗ {result['server']}: {result.get('error', 'Unknown error')}")

@patch.command()
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def status():
    """Show current patching status"""
    status_data = patching_engine.get_patching_status()
    
    if output == 'json':
        print_json(status_data)
    else:
        click.echo(f"\nPatching Status Summary - {status_data['current_quarter']}")
        click.echo("=" * 50)
        
        headers = ['Metric', 'Count', 'Percentage']
        total = status_data['total_servers']
        
        table_data = [
            ['Total Servers', total, '100.0%'],
            ['Pending Approval', status_data['pending_approval'], 
             f"{(status_data['pending_approval']/total*100):.1f}%" if total > 0 else '0%'],
            ['Approved', status_data['approved'], 
             f"{(status_data['approved']/total*100):.1f}%" if total > 0 else '0%'],
            ['Scheduled', status_data['scheduled'], 
             f"{(status_data['scheduled']/total*100):.1f}%" if total > 0 else '0%'],
            ['In Progress', status_data['in_progress'], 
             f"{(status_data['in_progress']/total*100):.1f}%" if total > 0 else '0%'],
            ['Completed', status_data['completed'], 
             f"{(status_data['completed']/total*100):.1f}%" if total > 0 else '0%'],
            ['Failed', status_data['failed'], 
             f"{(status_data['failed']/total*100):.1f}%" if total > 0 else '0%'],
            ['Rolled Back', status_data['rolled_back'], 
             f"{(status_data['rolled_back']/total*100):.1f}%" if total > 0 else '0%']
        ]
        
        print_table(table_data, headers)
        
        click.echo(f"\nOverall Success Rate: {status_data['success_rate']:.1f}%")
        click.echo(f"Active Operations: {status_data['active_operations']}")
        click.echo(f"Last Updated: {status_data['last_updated']}")

@patch.command()
@click.option('--server', '-s', required=True, help='Server name to rollback')
@click.option('--reason', '-r', required=True, help='Reason for rollback')
@click.option('--user', '-u', default='system', help='Operator username')
@click.option('--force', is_flag=True, help='Force rollback without confirmation')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def rollback(server, reason, user, force, output):
    """Rollback a server to previous state"""
    if not force and not click.confirm(f"Are you sure you want to rollback {server}?"):
        click.echo("Rollback cancelled.")
        return
    
    click.echo(f"Rolling back server: {server}")
    click.echo(f"Reason: {reason}")
    
    result = patching_engine.rollback_server(server, reason, user)
    
    if output == 'json':
        print_json(result)
    else:
        if result['success']:
            click.echo(f"✓ {format_status('Success')}: Rollback completed for {server}")
            click.echo(f"  Duration: {result.get('duration', 'N/A')}")
        else:
            click.echo(f"✗ {format_status('Failed')}: Rollback failed for {server}")
            click.echo(f"  Error: {result.get('error', 'Unknown error')}")

# ============================================================================
# SERVER MANAGEMENT COMMANDS
# ============================================================================

@cli.group()
def server():
    """Server management operations"""
    pass

@server.command()
@click.option('--group', '-g', help='Filter by host group')
@click.option('--environment', '-e', help='Filter by environment')
@click.option('--os', '-o', help='Filter by operating system')
@click.option('--status', '-s', help='Filter by status')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.option('--limit', '-l', type=int, help='Limit number of results')
def list(group, environment, os, status, output, limit):
    """List servers in inventory"""
    filters = {}
    if group:
        filters['host_group'] = group
    if environment:
        filters['environment'] = environment
    if os:
        filters['operating_system'] = os
    if status:
        filters['active_status'] = status
    
    servers = csv_handler.read_servers(filters)
    
    if limit:
        servers = servers[:limit]
    
    if output == 'json':
        print_json(servers)
    else:
        if not servers:
            click.echo("No servers found matching criteria.")
            return
        
        headers = ['Server Name', 'Host Group', 'Environment', 'OS', 'Timezone', 'Status']
        table_data = []
        
        for server in servers:
            table_data.append([
                server.get('server_name', ''),
                server.get('host_group', ''),
                server.get('environment', ''),
                server.get('operating_system', ''),
                server.get('server_timezone', 'UTC'),
                format_status(server.get('active_status', 'Active'))
            ])
        
        click.echo(f"\nTotal Servers: {len(servers)}")
        print_table(table_data, headers)

@server.command()
@click.option('--name', '-n', required=True, help='Server hostname')
@click.option('--group', '-g', required=True, help='Host group')
@click.option('--environment', '-e', required=True, help='Environment')
@click.option('--os', '-o', required=True, help='Operating system')
@click.option('--timezone', '-t', default='UTC', help='Server timezone')
@click.option('--owner', help='Primary owner email')
@click.option('--ssh-user', default='patchadmin', help='SSH user')
@click.option('--ssh-port', type=int, default=22, help='SSH port')
@click.option('--auto-approve', is_flag=True, help='Enable auto-approval')
@click.option('--backup-required', is_flag=True, help='Backup required before patching')
def add(name, group, environment, os, timezone, owner, ssh_user, ssh_port, auto_approve, backup_required):
    """Add a new server to inventory"""
    # Check if server already exists
    existing = csv_handler.get_server(name)
    if existing:
        click.echo(f"✗ {format_status('Error')}: Server {name} already exists!")
        return
    
    # Create new server record
    new_server = {
        'server_name': name,
        'host_group': group,
        'environment': environment,
        'operating_system': os,
        'server_timezone': timezone,
        'primary_owner': owner or '',
        'primary_linux_user': ssh_user,
        'ssh_port': str(ssh_port),
        'auto_approve': 'Yes' if auto_approve else 'No',
        'backup_required': 'Yes' if backup_required else 'No',
        'active_status': 'Active'
    }
    
    if csv_handler.add_server(new_server):
        click.echo(f"✓ {format_status('Success')}: Server {name} added successfully!")
        logger.server_added(name, 'cli_user')
    else:
        click.echo(f"✗ {format_status('Error')}: Failed to add server {name}")

@server.command()
@click.option('--name', '-n', required=True, help='Server hostname')
@click.option('--force', is_flag=True, help='Skip confirmation')
def remove(name, force):
    """Remove a server from inventory"""
    if not force and not click.confirm(f"Remove server {name}?"):
        return
    
    if csv_handler.delete_server(name):
        click.echo(f"✓ {format_status('Success')}: Server {name} removed successfully!")
        logger.server_removed(name, 'cli_user')
    else:
        click.echo(f"✗ {format_status('Error')}: Server {name} not found!")

@server.command()
@click.option('--name', '-n', required=True, help='Server hostname')
@click.option('--field', '-f', required=True, help='Field to update')
@click.option('--value', '-v', required=True, help='New value')
def update(name, field, value):
    """Update server information"""
    # Convert field name to normalized format
    normalized_field = field.lower().replace(' ', '_').replace('-', '_')
    
    if csv_handler.update_server(name, {normalized_field: value}):
        click.echo(f"✓ {format_status('Success')}: Updated {field} for {name}")
        logger.server_updated(name, 'cli_user', {field: value})
    else:
        click.echo(f"✗ {format_status('Error')}: Failed to update {name} or server not found")

@server.command()
@click.option('--name', '-n', required=True, help='Server hostname')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def info(name, output):
    """Show detailed server information"""
    server = csv_handler.get_server(name)
    
    if not server:
        click.echo(f"✗ {format_status('Error')}: Server {name} not found!")
        return
    
    if output == 'json':
        print_json(server)
    else:
        click.echo(f"\nServer Information: {name}")
        click.echo("=" * 50)
        
        # Group information logically
        sections = {
            'Basic Information': ['server_name', 'host_group', 'environment', 'operating_system', 'server_timezone'],
            'Contact Information': ['primary_owner', 'secondary_owner', 'patcher_email'],
            'SSH Configuration': ['primary_linux_user', 'ssh_port', 'ssh_key_path'],
            'Patching Configuration': ['auto_approve', 'backup_required', 'critical_services'],
            'Status': ['active_status', 'current_quarter_patching_status', 'last_sync_date']
        }
        
        for section, fields in sections.items():
            click.echo(f"\n{section}:")
            for field in fields:
                value = server.get(field, 'N/A')
                display_field = field.replace('_', ' ').title()
                click.echo(f"  {display_field}: {value}")

@server.command()
@click.option('--servers', '-s', help='Comma-separated list of servers (default: all)')
@click.option('--user', '-u', default='patchadmin', help='SSH user')
@click.option('--parallel', is_flag=True, help='Test connections in parallel')
@click.option('--timeout', type=int, default=30, help='Connection timeout')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def test(servers, user, parallel, timeout, output):
    """Test SSH connectivity to servers"""
    if servers:
        server_list = [s.strip() for s in servers.split(',')]
    else:
        # Get all active servers
        all_servers = csv_handler.read_servers({'active_status': 'Active'})
        server_list = [s['server_name'] for s in all_servers]
    
    if not server_list:
        click.echo("No servers to test.")
        return
    
    click.echo(f"Testing connectivity to {len(server_list)} servers...")
    
    results = test_ssh_connectivity(server_list, user, parallel)
    
    if output == 'json':
        print_json(results)
    else:
        headers = ['Server', 'Status', 'Connection Time', 'Error']
        table_data = []
        
        successful = 0
        for server, result in results.items():
            if result['success']:
                status = format_status('Success')
                conn_time = f"{result.get('connection_time', 0):.2f}s"
                error = ''
                successful += 1
            else:
                status = format_status('Failed')
                conn_time = 'N/A'
                error = result.get('error', 'Unknown error')
            
            table_data.append([server, status, conn_time, error])
        
        print_table(table_data, headers)
        
        click.echo(f"\nConnectivity Summary:")
        click.echo(f"  Total: {len(server_list)}")
        click.echo(f"  {format_status('Success')}: {successful}")
        click.echo(f"  {format_status('Failed')}: {len(server_list) - successful}")
        click.echo(f"  Success Rate: {(successful/len(server_list)*100):.1f}%")

@server.command()
@click.option('--file', '-f', required=True, help='CSV file to import')
@click.option('--merge', is_flag=True, help='Merge with existing servers')
@click.option('--dry-run', is_flag=True, help='Show what would be imported')
def import_csv(file, merge, dry_run):
    """Import servers from CSV file"""
    if not os.path.exists(file):
        click.echo(f"✗ {format_status('Error')}: File {file} not found!")
        return
    
    if dry_run:
        click.echo(f"Would import servers from {file}")
        click.echo(f"Merge mode: {'Yes' if merge else 'No'}")
        return
    
    if csv_handler.import_servers(file, merge):
        click.echo(f"✓ {format_status('Success')}: Servers imported from {file}")
    else:
        click.echo(f"✗ {format_status('Error')}: Failed to import servers from {file}")

@server.command()
@click.option('--file', '-f', help='Output file (default: servers_export.csv)')
@click.option('--format', '-fmt', type=click.Choice(['csv', 'json']), default='csv',
              help='Export format')
@click.option('--group', '-g', help='Filter by host group')
@click.option('--environment', '-e', help='Filter by environment')
def export(file, format, group, environment):
    """Export servers to file"""
    filters = {}
    if group:
        filters['host_group'] = group
    if environment:
        filters['environment'] = environment
    
    if not file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file = f"servers_export_{timestamp}.{format}"
    
    try:
        servers = csv_handler.read_servers(filters)
        
        if format == 'csv':
            # Use existing export functionality
            export_files = csv_handler.export_data('servers', 'csv', os.path.dirname(file) or '.')
            if export_files:
                # Move to desired filename
                import shutil
                shutil.move(list(export_files.values())[0], file)
                click.echo(f"✓ {format_status('Success')}: Exported {len(servers)} servers to {file}")
            else:
                click.echo(f"✗ {format_status('Error')}: Export failed")
        else:
            # JSON export
            with open(file, 'w') as f:
                json.dump(servers, f, indent=2, default=str)
            click.echo(f"✓ {format_status('Success')}: Exported {len(servers)} servers to {file}")
    
    except Exception as e:
        click.echo(f"✗ {format_status('Error')}: Export failed: {str(e)}")

# ============================================================================
# APPROVAL COMMANDS
# ============================================================================

@cli.group()
def approval():
    """Approval workflow operations"""
    pass

@approval.command()
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to show approvals for')
@click.option('--status', '-s', type=click.Choice(['Pending', 'Approved', 'Rejected']),
              help='Filter by approval status')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def list(quarter, status, output):
    """List approval requests"""
    approvals = csv_handler.get_approvals(status=status, quarter=quarter)
    
    if output == 'json':
        print_json(approvals)
    else:
        if not approvals:
            click.echo("No approval requests found.")
            return
        
        headers = ['Approval ID', 'Server', 'Quarter', 'Status', 'Requested By', 'Request Date']
        table_data = []
        
        for approval in approvals:
            table_data.append([
                approval.get('Approval ID', ''),
                approval.get('Server Name', ''),
                approval.get('Quarter', ''),
                format_status(approval.get('Status', 'Pending')),
                approval.get('Requested By', ''),
                approval.get('Request Date', '')
            ])
        
        print_table(table_data, headers)

@approval.command()
@click.option('--server', '-s', help='Server name to approve')
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to approve')
@click.option('--group', '-g', help='Approve entire host group')
@click.option('--all', is_flag=True, help='Approve all pending requests')
@click.option('--approver', '-a', default='cli_user', help='Approver name')
@click.option('--comment', '-c', help='Approval comment')
@click.option('--force', is_flag=True, help='Skip confirmation')
def approve(server, quarter, group, all, approver, comment, force):
    """Approve patching requests"""
    quarter = quarter or patching_engine.get_current_quarter()
    
    if all:
        # Approve all pending requests
        servers = csv_handler.read_servers()
        approval_field = f'q{quarter[-1]}_approval_status'
        
        servers_to_approve = []
        for srv in servers:
            if srv.get(approval_field, 'Pending') == 'Pending':
                servers_to_approve.append(srv['server_name'])
        
        if not servers_to_approve:
            click.echo("No servers pending approval.")
            return
        
        if not force and not click.confirm(f"Approve {len(servers_to_approve)} servers for {quarter}?"):
            return
        
        count = 0
        for server_name in servers_to_approve:
            if csv_handler.update_server(server_name, {approval_field: 'Approved'}):
                count += 1
                
                # Record approval
                approval_data = {
                    'server_name': server_name,
                    'quarter': quarter,
                    'requested_by': 'system',
                    'approver': approver,
                    'status': 'Approved',
                    'approval_type': 'Batch',
                    'comments': comment or f'Batch approval for {quarter}'
                }
                csv_handler.record_approval(approval_data)
                logger.approval_granted(server_name, quarter, approver)
        
        click.echo(f"✓ {format_status('Success')}: Approved {count} servers for {quarter}")
    
    elif group:
        # Approve entire group
        servers = csv_handler.get_servers_by_group(group)
        approval_field = f'q{quarter[-1]}_approval_status'
        
        servers_to_approve = []
        for srv in servers:
            if srv.get(approval_field, 'Pending') == 'Pending':
                servers_to_approve.append(srv['server_name'])
        
        if not servers_to_approve:
            click.echo(f"No servers in group {group} pending approval.")
            return
        
        if not force and not click.confirm(f"Approve {len(servers_to_approve)} servers in group {group}?"):
            return
        
        count = 0
        for server_name in servers_to_approve:
            if csv_handler.update_server(server_name, {approval_field: 'Approved'}):
                count += 1
                
                # Record approval
                approval_data = {
                    'server_name': server_name,
                    'quarter': quarter,
                    'requested_by': 'system',
                    'approver': approver,
                    'status': 'Approved',
                    'approval_type': 'Group',
                    'comments': comment or f'Group approval for {group}'
                }
                csv_handler.record_approval(approval_data)
                logger.approval_granted(server_name, quarter, approver)
        
        click.echo(f"✓ {format_status('Success')}: Approved {count} servers in group {group}")
    
    elif server:
        # Approve single server
        approval_field = f'q{quarter[-1]}_approval_status'
        
        if csv_handler.update_server(server, {approval_field: 'Approved'}):
            # Record approval
            approval_data = {
                'server_name': server,
                'quarter': quarter,
                'requested_by': 'system',
                'approver': approver,
                'status': 'Approved',
                'approval_type': 'Individual',
                'comments': comment or f'Individual approval for {server}'
            }
            csv_handler.record_approval(approval_data)
            logger.approval_granted(server, quarter, approver)
            
            click.echo(f"✓ {format_status('Success')}: Approved {server} for {quarter}")
        else:
            click.echo(f"✗ {format_status('Error')}: Failed to approve {server}")
    
    else:
        click.echo("Please specify --server, --group, or --all")

@approval.command()
@click.option('--server', '-s', help='Server name to reject')
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to reject')
@click.option('--reason', '-r', required=True, help='Rejection reason')
@click.option('--approver', '-a', default='cli_user', help='Approver name')
def reject(server, quarter, reason, approver):
    """Reject patching requests"""
    quarter = quarter or patching_engine.get_current_quarter()
    
    if not server:
        click.echo("Please specify --server")
        return
    
    approval_field = f'q{quarter[-1]}_approval_status'
    
    if csv_handler.update_server(server, {approval_field: 'Rejected'}):
        # Record rejection
        approval_data = {
            'server_name': server,
            'quarter': quarter,
            'requested_by': 'system',
            'approver': approver,
            'status': 'Rejected',
            'approval_type': 'Individual',
            'comments': reason
        }
        csv_handler.record_approval(approval_data)
        logger.approval_denied(server, quarter, approver, reason)
        
        click.echo(f"✓ {format_status('Success')}: Rejected {server} for {quarter}")
        click.echo(f"  Reason: {reason}")
    else:
        click.echo(f"✗ {format_status('Error')}: Failed to reject {server}")

# ============================================================================
# PRECHECK COMMANDS
# ============================================================================

@cli.group()
def precheck():
    """Pre-check operations"""
    pass

@precheck.command()
@click.option('--server', '-s', help='Server to check')
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to check')
@click.option('--group', '-g', help='Host group to check')
@click.option('--user', '-u', default='system', help='Operator username')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def run(server, quarter, group, user, output):
    """Run pre-checks on servers"""
    quarter = quarter or patching_engine.get_current_quarter()
    
    if server:
        servers_to_check = [server]
    elif group:
        servers_data = csv_handler.get_servers_by_group(group)
        servers_to_check = [s['server_name'] for s in servers_data]
    else:
        servers_data = patching_engine.get_servers_for_patching(quarter=quarter)
        servers_to_check = [s['server_name'] for s in servers_data]
    
    if not servers_to_check:
        click.echo("No servers to check.")
        return
    
    click.echo(f"Running pre-checks on {len(servers_to_check)} servers...")
    
    results = []
    for server_name in servers_to_check:
        result = patching_engine.run_precheck(server_name, quarter, user)
        results.append(result)
    
    if output == 'json':
        print_json(results)
    else:
        headers = ['Server', 'Status', 'Issues', 'Details']
        table_data = []
        
        passed = 0
        for result in results:
            if result['success'] and result['overall_status'] == 'passed':
                status = format_status('Passed')
                issues = '0'
                details = 'All checks passed'
                passed += 1
            else:
                status = format_status('Failed')
                issues = str(len(result.get('issues', [])))
                details = '; '.join([issue['issue'] for issue in result.get('issues', [])][:2])
                if len(result.get('issues', [])) > 2:
                    details += '...'
            
            table_data.append([result['server'], status, issues, details])
        
        print_table(table_data, headers)
        
        click.echo(f"\nPre-check Summary:")
        click.echo(f"  Total: {len(results)}")
        click.echo(f"  {format_status('Passed')}: {passed}")
        click.echo(f"  {format_status('Failed')}: {len(results) - passed}")
        click.echo(f"  Success Rate: {(passed/len(results)*100):.1f}%")

@precheck.command()
@click.option('--server', '-s', help='Server to show results for')
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter to show results for')
@click.option('--status', '-st', type=click.Choice(['Passed', 'Failed', 'Warning']),
              help='Filter by status')
@click.option('--output', '-o', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
def results(server, quarter, status, output):
    """Show pre-check results"""
    results = csv_handler.get_precheck_results(server, quarter, status)
    
    if output == 'json':
        print_json(results)
    else:
        if not results:
            click.echo("No pre-check results found.")
            return
        
        headers = ['Timestamp', 'Server', 'Check', 'Status', 'Message']
        table_data = []
        
        for result in results:
            table_data.append([
                result.get('Timestamp', ''),
                result.get('Server Name', ''),
                result.get('Check Name', ''),
                format_status(result.get('Status', 'Unknown')),
                result.get('Message', '')[:50] + '...' if len(result.get('Message', '')) > 50 else result.get('Message', '')
            ])
        
        print_table(table_data, headers)

# ============================================================================
# REPORT COMMANDS
# ============================================================================

@cli.group()
def report():
    """Reporting operations"""
    pass

@report.command()
@click.option('--type', '-t', type=click.Choice(['summary', 'detailed', 'quarterly', 'daily']),
              default='summary', help='Report type')
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter for report')
@click.option('--group', '-g', help='Host group filter')
@click.option('--environment', '-e', help='Environment filter')
@click.option('--output', '-o', type=click.Choice(['table', 'json', 'csv']), default='table',
              help='Output format')
@click.option('--file', '-f', help='Output to file')
def generate(type, quarter, group, environment, output, file):
    """Generate various reports"""
    quarter = quarter or patching_engine.get_current_quarter()
    
    click.echo(f"Generating {type} report for {quarter}...")
    
    # Get data based on filters
    filters = {}
    if group:
        filters['host_group'] = group
    if environment:
        filters['environment'] = environment
    
    servers = csv_handler.read_servers(filters)
    patch_history = csv_handler.get_patch_history(quarter=quarter)
    
    if type == 'summary':
        _generate_summary_report(servers, patch_history, quarter, output, file)
    elif type == 'detailed':
        _generate_detailed_report(servers, patch_history, quarter, output, file)
    elif type == 'quarterly':
        _generate_quarterly_report(servers, patch_history, quarter, output, file)
    elif type == 'daily':
        _generate_daily_report(servers, patch_history, output, file)

def _generate_summary_report(servers, patch_history, quarter, output, file):
    """Generate summary report"""
    # Calculate statistics
    total_servers = len(servers)
    patched_servers = len([h for h in patch_history if h.get('Status') == 'Success'])
    failed_servers = len([h for h in patch_history if h.get('Status') == 'Failed'])
    
    success_rate = (patched_servers / total_servers * 100) if total_servers > 0 else 0
    
    summary = {
        'quarter': quarter,
        'total_servers': total_servers,
        'patched_servers': patched_servers,
        'failed_servers': failed_servers,
        'success_rate': success_rate,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if output == 'json':
        if file:
            with open(file, 'w') as f:
                json.dump(summary, f, indent=2)
            click.echo(f"Report saved to {file}")
        else:
            print_json(summary)
    else:
        report_lines = [
            f"Patching Summary Report - {quarter}",
            "=" * 40,
            f"Total Servers: {total_servers}",
            f"Successfully Patched: {patched_servers}",
            f"Failed: {failed_servers}",
            f"Success Rate: {success_rate:.1f}%",
            f"Generated: {summary['timestamp']}"
        ]
        
        if file:
            with open(file, 'w') as f:
                f.write('\n'.join(report_lines))
            click.echo(f"Report saved to {file}")
        else:
            for line in report_lines:
                click.echo(line)

def _generate_detailed_report(servers, patch_history, quarter, output, file):
    """Generate detailed report"""
    if output == 'json':
        report_data = {
            'quarter': quarter,
            'servers': servers,
            'patch_history': patch_history,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if file:
            with open(file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            click.echo(f"Detailed report saved to {file}")
        else:
            print_json(report_data)
    else:
        headers = ['Server', 'Group', 'Status', 'Patch Date', 'Duration', 'Reboot Required']
        table_data = []
        
        for history in patch_history:
            table_data.append([
                history.get('Server Name', ''),
                '', # Would need to join with server data
                format_status(history.get('Status', 'Unknown')),
                history.get('Start Time', ''),
                history.get('Duration Minutes', ''),
                history.get('Reboot Required', 'No')
            ])
        
        if file:
            with open(file, 'w') as f:
                f.write(f"Detailed Patching Report - {quarter}\n")
                f.write("=" * 50 + "\n\n")
                f.write(tabulate(table_data, headers=headers, tablefmt='simple'))
            click.echo(f"Detailed report saved to {file}")
        else:
            click.echo(f"Detailed Patching Report - {quarter}")
            click.echo("=" * 50)
            print_table(table_data, headers)

def _generate_quarterly_report(servers, patch_history, quarter, output, file):
    """Generate quarterly report"""
    # This would be more comprehensive
    _generate_summary_report(servers, patch_history, quarter, output, file)

def _generate_daily_report(servers, patch_history, output, file):
    """Generate daily report"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Filter history for today
    today_history = [h for h in patch_history if h.get('Start Time', '').startswith(today)]
    
    _generate_summary_report(servers, today_history, f"Daily-{today}", output, file)

@report.command()
@click.option('--type', '-t', type=click.Choice(['summary', 'detailed', 'quarterly']),
              default='summary', help='Report type')
@click.option('--quarter', '-q', type=click.Choice(['Q1', 'Q2', 'Q3', 'Q4']), 
              help='Quarter for report')
@click.option('--to', '-to', required=True, help='Email recipient')
@click.option('--subject', '-s', help='Email subject')
def email(type, quarter, to, subject):
    """Email reports"""
    quarter = quarter or patching_engine.get_current_quarter()
    
    if not subject:
        subject = f"Patching {type.title()} Report - {quarter}"
    
    click.echo(f"Sending {type} report to {to}...")
    
    # Generate report content
    servers = csv_handler.read_servers()
    patch_history = csv_handler.get_patch_history(quarter=quarter)
    
    # Create email body
    total_servers = len(servers)
    patched_servers = len([h for h in patch_history if h.get('Status') == 'Success'])
    failed_servers = len([h for h in patch_history if h.get('Status') == 'Failed'])
    success_rate = (patched_servers / total_servers * 100) if total_servers > 0 else 0
    
    body = f"""
    Patching Report - {quarter}
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Summary:
    - Total Servers: {total_servers}
    - Successfully Patched: {patched_servers}
    - Failed: {failed_servers}
    - Success Rate: {success_rate:.1f}%
    
    This report was generated automatically by the Linux Patching Automation System.
    """
    
    try:
        patching_engine.email_sender.send_email(
            to=[to],
            subject=subject,
            body=body
        )
        click.echo(f"✓ {format_status('Success')}: Report sent to {to}")
    except Exception as e:
        click.echo(f"✗ {format_status('Error')}: Failed to send report: {str(e)}")

# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@cli.group()
def system():
    """System operations"""
    pass

@system.command()
def stats():
    """Show system statistics"""
    stats = patching_engine.get_statistics()
    
    click.echo("System Statistics")
    click.echo("=" * 30)
    
    click.echo(f"\nPatching Engine:")
    click.echo(f"  Total Patches: {stats['total_patches']}")
    click.echo(f"  Successful: {stats['successful_patches']}")
    click.echo(f"  Failed: {stats['failed_patches']}")
    click.echo(f"  Active Operations: {stats['active_operations']}")
    
    click.echo(f"\nRollbacks:")
    click.echo(f"  Total: {stats['total_rollbacks']}")
    click.echo(f"  Successful: {stats['successful_rollbacks']}")
    click.echo(f"  Failed: {stats['failed_rollbacks']}")
    
    csv_stats = stats.get('csv_statistics', {})
    if csv_stats:
        click.echo(f"\nData Statistics:")
        click.echo(f"  Servers: {csv_stats.get('servers', {}).get('total', 0)}")
        click.echo(f"  Patch History: {csv_stats.get('patches', {}).get('total', 0)}")
        click.echo(f"  Approvals: {csv_stats.get('approvals', {}).get('total', 0)}")

@system.command()
@click.option('--days', '-d', type=int, default=30, help='Days of data to keep')
@click.option('--confirm', is_flag=True, help='Confirm cleanup')
def cleanup(days, confirm):
    """Clean up old data"""
    if not confirm and not click.confirm(f"Clean up data older than {days} days?"):
        return
    
    click.echo(f"Cleaning up data older than {days} days...")
    
    # Clean up CSV data
    cleaned = csv_handler.cleanup_old_data(days)
    
    # Clean up logs
    patching_engine.logger.cleanup_old_logs(days)
    
    click.echo(f"✓ {format_status('Success')}: Cleanup completed")
    click.echo(f"  Patch history cleaned: {cleaned.get('patch_history', 0)} records")
    click.echo(f"  Precheck results cleaned: {cleaned.get('precheck_results', 0)} records")

@system.command()
def health():
    """Check system health"""
    click.echo("System Health Check")
    click.echo("=" * 30)
    
    # Check data files
    data_files = [
        csv_handler.servers_file,
        csv_handler.patch_history_file,
        csv_handler.approval_file
    ]
    
    for file_path in data_files:
        if file_path.exists():
            click.echo(f"✓ {format_status('OK')}: {file_path.name}")
        else:
            click.echo(f"✗ {format_status('Error')}: {file_path.name} missing")
    
    # Check log files
    log_files = patching_engine.logger.get_log_files()
    for log_name, log_path in log_files.items():
        if os.path.exists(log_path):
            click.echo(f"✓ {format_status('OK')}: {log_name}")
        else:
            click.echo(f"✗ {format_status('Error')}: {log_name} missing")
    
    # Check active operations
    active_ops = len(patching_engine.active_operations)
    click.echo(f"Active Operations: {active_ops}")

@system.command()
@click.option('--to', '-to', required=True, help='Test email recipient')
def test_email(to):
    """Test email configuration"""
    try:
        patching_engine.email_sender.send_email(
            to=[to],
            subject="Test Email from Patching System",
            body="This is a test email from the Linux Patching Automation System."
        )
        click.echo(f"✓ {format_status('Success')}: Test email sent to {to}")
    except Exception as e:
        click.echo(f"✗ {format_status('Error')}: Failed to send test email: {str(e)}")

@system.command()
def version():
    """Show version information"""
    click.echo("Linux Patching Automation CLI v1.0.0")
    click.echo("Built with Python and Click")
    click.echo("Copyright 2024")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in CLI: {str(e)}")
        click.echo(f"✗ {format_status('Error')}: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            patching_engine.shutdown()
        except:
            pass

if __name__ == '__main__':
    main()