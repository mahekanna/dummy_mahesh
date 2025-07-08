#!/usr/bin/env python3

import sys
import argparse
from datetime import datetime
from scripts.step0_approval_requests import ApprovalRequestHandler
from scripts.step1_monthly_notice import MonthlyNoticeHandler
from scripts.step1b_weekly_followup import WeeklyFollowupHandler
from scripts.step2_reminders import ReminderHandler
from scripts.step3_prechecks import PreCheckHandler
from scripts.step4_scheduler import PatchScheduler
from scripts.step5_patch_validation import PatchValidator
from scripts.step6_post_patch import PostPatchValidator
from scripts.intelligent_scheduler import SmartScheduler
from scripts.load_predictor import SmartLoadPredictor
from utils.logger import Logger
from utils.csv_handler import CSVHandler
from utils.external_csv_importer import ExternalCSVImporter
from utils.email_sender import EmailSender
from database.models import DatabaseManager
from config.settings import Config

def main():
    parser = argparse.ArgumentParser(description='Linux OS Patching Automation System')
    parser.add_argument('--step', choices=['0', '1', '1b', '2', '3', '4', '5', '6', 'all'], 
                       help='Execute specific step (0=approval requests, 1=monthly notice, 1b=weekly followup, etc.)')
    parser.add_argument('--quarter', choices=['1', '2', '3', '4'],
                       default=Config.get_current_quarter(),
                       help='Quarter for patching (1=Nov-Jan, 2=Feb-Apr, 3=May-Jul, 4=Aug-Oct)')
    parser.add_argument('--server', help='Specific server name for single server operations')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--import-csv', help='Import servers from CSV file')
    parser.add_argument('--update-emails', action='store_true', help='Update incident/patcher emails')
    parser.add_argument('--incident-ticket', help='Set incident ticket number for servers')
    parser.add_argument('--patcher-email', help='Set patcher email for servers')
    parser.add_argument('--host-group', help='Filter by host group for email updates')
    parser.add_argument('--approve', action='store_true', help='Approve server schedules')
    parser.add_argument('--check-approvals', action='store_true', help='Check approval status')
    parser.add_argument('--auto-approve', action='store_true', help='Auto-approve pending servers after deadline')
    parser.add_argument('--intelligent-schedule', action='store_true', help='Run intelligent scheduling for unscheduled servers')
    parser.add_argument('--analyze-load', action='store_true', help='Analyze server load patterns')
    parser.add_argument('--simulate-data', action='store_true', help='Simulate historical data for testing')
    parser.add_argument('--test-patching-script', action='store_true', help='Test patching script configuration on random server')
    parser.add_argument('--show-patching-config', action='store_true', help='Show current patching script configuration')
    
    args = parser.parse_args()
    
    logger = Logger('main')
    logger.info(f"Starting patching automation system - Step: {args.step}, Quarter: {args.quarter}")
    
    # Initialize database if requested
    if args.init_db:
        db = DatabaseManager()
        db.connect()
        db.create_tables()
        logger.info("Database initialized successfully")
        return
    
    # Import CSV if requested
    if args.import_csv:
        import_csv_file(args.import_csv, logger)
        return
    
    # Update emails if requested
    if args.update_emails or args.incident_ticket or args.patcher_email:
        update_server_emails(args, logger)
        return
    
    # Approve schedules if requested
    if args.approve:
        approve_server_schedules(args, logger)
        return
    
    # Check approvals if requested
    if args.check_approvals:
        check_approval_status(args, logger)
        return
    
    # Auto-approve pending servers if requested
    if args.auto_approve:
        auto_approve_pending_servers(args, logger)
        return
    
    # Run intelligent scheduling if requested
    if args.intelligent_schedule:
        run_intelligent_scheduling(args, logger)
        return
    
    # Analyze load patterns if requested
    if args.analyze_load:
        analyze_server_load(args, logger)
        return
    
    # Simulate historical data if requested
    if args.simulate_data:
        simulate_historical_data(args, logger)
        return
    
    if args.test_patching_script:
        test_patching_script_config(args, logger)
        return
    
    if args.show_patching_config:
        show_patching_config(logger)
        return
    
    try:
        if args.step == '0' or args.step == 'all':
            logger.info("Executing Step 0: Approval Requests")
            handler = ApprovalRequestHandler()
            handler.send_approval_requests(args.quarter)
        
        if args.step == '1' or args.step == 'all':
            logger.info("Executing Step 1: Monthly Notice")
            handler = MonthlyNoticeHandler()
            handler.send_monthly_notice(args.quarter)
        
        if args.step == '1b':
            logger.info("Executing Step 1b: Weekly Followup")
            handler = WeeklyFollowupHandler()
            handler.send_weekly_followup(args.quarter)
        
        if args.step == '2' or args.step == 'all':
            logger.info("Executing Step 2: Reminders")
            handler = ReminderHandler()
            handler.send_weekly_reminder(args.quarter)
            handler.send_daily_reminder(args.quarter)
        
        if args.step == '3' or args.step == 'all':
            logger.info("Executing Step 3: Pre-checks")
            handler = PreCheckHandler()
            handler.run_prechecks(args.quarter)
        
        if args.step == '4' or args.step == 'all':
            logger.info("Executing Step 4: Scheduling")
            handler = PatchScheduler()
            handler.schedule_patches(args.quarter)
        
        if args.step == '5' and args.server:
            logger.info(f"Executing Step 5: Patch Validation for {args.server}")
            handler = PatchValidator()
            success = handler.validate_patches(args.server)
            sys.exit(0 if success else 1)
        
        if args.step == '6' and args.server:
            logger.info(f"Executing Step 6: Post-Patch Validation for {args.server}")
            handler = PostPatchValidator()
            success = handler.post_patch_validation(args.server)
            sys.exit(0 if success else 1)
        
        logger.info("Patching automation completed successfully")
        
    except Exception as e:
        import traceback
        logger.error(f"Error in patching automation: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

def import_csv_file(csv_file_path, logger):
    """Import servers from external CSV file (source data only)"""
    try:
        import os
        import shutil
        
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found: {csv_file_path}")
            return
        
        # Create backup of existing CSV
        backup_path = Config.CSV_FILE_PATH + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(Config.CSV_FILE_PATH):
            shutil.copy2(Config.CSV_FILE_PATH, backup_path)
            logger.info(f"Existing CSV backed up to: {backup_path}")
        
        # Use external CSV importer for proper field separation
        importer = ExternalCSVImporter()
        
        # Validate external CSV first
        logger.info("Validating external CSV structure...")
        is_valid, validation_issues = importer.validate_external_csv(csv_file_path)
        
        if not is_valid:
            logger.error("External CSV validation failed:")
            for issue in validation_issues:
                logger.error(f"  - {issue}")
            logger.info("Run 'python3 scripts/csv_analyzer.py --report <csv_file>' for detailed analysis")
            return
        
        # Show import analysis
        logger.info("External CSV analysis:")
        report = importer.get_import_report(csv_file_path)
        logger.info(report)
        
        # Import external CSV with internal data preservation
        success, message = importer.import_external_csv(csv_file_path, preserve_internal_data=True)
        
        if success:
            logger.info(message)
            
            # Show summary of imported data
            csv_handler = CSVHandler()
            servers = csv_handler.read_servers(normalize_fields=True)
            
            logger.info("Sample imported servers:")
            for server in servers[:5]:  # Show first 5 servers
                server_name = server.get('server_name', 'Unknown')
                host_group = server.get('host_group', 'N/A')
                primary_owner = server.get('primary_owner', 'N/A')
                current_status = server.get('current_quarter_status', 'Pending')
                logger.info(f"  - {server_name} (Group: {host_group}, Owner: {primary_owner}, Status: {current_status})")
            
            if len(servers) > 5:
                logger.info(f"  ... and {len(servers) - 5} more servers")
                
            logger.info(f"Import completed: {len(servers)} total servers in system")
        else:
            logger.error(f"Import failed: {message}")
            
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")

def update_server_emails(args, logger):
    """Update incident ticket and patcher emails for servers"""
    try:
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers(normalize_fields=True)
        updated_count = 0
        affected_servers = 0
        
        for server in servers:
            # Filter by host group if specified
            if args.host_group and server.get('host_group') != args.host_group:
                continue
            
            affected_servers += 1
            
            # Update incident ticket
            if args.incident_ticket:
                server['incident_ticket'] = args.incident_ticket
                updated_count += 1
            
            # Update patcher email
            if args.patcher_email:
                server['patcher_email'] = args.patcher_email
                updated_count += 1
        
        if updated_count > 0:
            csv_handler.write_servers(servers)
            logger.info(f"Updated server information for {affected_servers} servers")
            
            if args.incident_ticket:
                logger.info(f"  Incident ticket set to: {args.incident_ticket}")
            if args.patcher_email:
                logger.info(f"  Patcher email set to: {args.patcher_email}")
            if args.host_group:
                logger.info(f"  Filtered by host group: {args.host_group}")
        else:
            logger.warning("No servers were updated. Check your filters and parameters.")
            
    except Exception as e:
        logger.error(f"Error updating server information: {e}")

def approve_server_schedules(args, logger):
    """Approve server schedules via CLI"""
    try:
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers(normalize_fields=True)
        updated_count = 0
        
        for server in servers:
            server_name = server.get('server_name', 'Unknown')
            
            # Filter by host group or server name if specified
            if args.host_group and server.get('host_group') != args.host_group:
                continue
            if args.server and server_name != args.server:
                continue
            
            # Check if server has a patch date for the quarter
            patch_date = server.get(f'q{args.quarter}_patch_date')
            if not patch_date:
                logger.warning(f"Server {server_name} has no patch date for Q{args.quarter}, skipping")
                continue
            
            # Update approval status
            approval_field = f'q{args.quarter}_approval_status'
            if server.get(approval_field, 'Pending') == 'Pending':
                server[approval_field] = 'Approved'
                
                # Update patching status if current quarter
                if args.quarter == Config.get_current_quarter():
                    server['current_quarter_status'] = 'Approved'
                
                updated_count += 1
                logger.info(f"  Approved: {server_name}")
                
                # Send approval confirmation email
                try:
                    send_cli_approval_confirmation(server, args.quarter, logger)
                except Exception as email_error:
                    logger.warning(f"Failed to send approval confirmation for {server_name}: {email_error}")
        
        if updated_count > 0:
            csv_handler.write_servers(servers)
            logger.info(f"Approved schedules for {updated_count} servers in Q{args.quarter}")
        else:
            logger.warning("No servers were approved. Check your filters and server schedules.")
            
    except Exception as e:
        logger.error(f"Error approving schedules: {e}")

def check_approval_status(args, logger):
    """Check approval status for servers"""
    try:
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers(normalize_fields=True)
        
        approved_count = 0
        pending_count = 0
        no_schedule_count = 0
        
        logger.info(f"Approval Status Report for Q{args.quarter}:")
        logger.info("=" * 60)
        
        for server in servers:
            # Filter by host group if specified
            if args.host_group and server.get('host_group') != args.host_group:
                continue
            
            server_name = server.get('server_name', 'Unknown')
            patch_date = server.get(f'q{args.quarter}_patch_date')
            approval_status = server.get(f'q{args.quarter}_approval_status', 'Pending')
            
            if not patch_date:
                logger.info(f"  {server_name:<30} No schedule set")
                no_schedule_count += 1
            elif approval_status in ['Approved', 'Auto-Approved']:
                status_text = approval_status if approval_status == 'Auto-Approved' else 'Approved'
                logger.info(f"  {server_name:<30} {status_text} ({patch_date})")
                approved_count += 1
            else:
                logger.info(f"  {server_name:<30} Pending ({patch_date})")
                pending_count += 1
        
        logger.info("=" * 60)
        logger.info(f"Summary: {approved_count} Approved, {pending_count} Pending, {no_schedule_count} No Schedule")
        
        if args.host_group:
            logger.info(f"Filtered by host group: {args.host_group}")
            
    except Exception as e:
        logger.error(f"Error checking approval status: {e}")

def send_cli_approval_confirmation(server, quarter, logger):
    """Send approval confirmation email from CLI"""
    try:
        email_sender = EmailSender()
        
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
        server_table = generate_cli_approval_table([server], quarter)
        
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
        server_name = server.get('server_name', 'Unknown')
        
        if primary_owner:
            email_content = template.format(owner_email=primary_owner, **email_data)
            subject = f"APPROVED: {quarter_name} Patching Schedule Confirmed - {server_name}"
            email_sender.send_email(primary_owner, subject, email_content, is_html=True)
            logger.info(f"  Approval confirmation sent to primary owner: {primary_owner}")
        
        # Send to secondary owner if exists
        secondary_owner = server.get('secondary_owner')
        if secondary_owner and secondary_owner != primary_owner:
            email_content = template.format(owner_email=secondary_owner, **email_data)
            subject = f"APPROVED: {quarter_name} Patching Schedule Confirmed - {server_name}"
            email_sender.send_email(secondary_owner, subject, email_content, is_html=True)
            logger.info(f"  Approval confirmation sent to secondary owner: {secondary_owner}")
            
    except Exception as e:
        logger.error(f"Error sending approval confirmation: {e}")
        raise

def generate_cli_approval_table(servers_list, quarter):
    """Generate HTML table for CLI approval confirmation"""
    table_rows = ""
    for server in servers_list:
        # Get patch date and time for the specified quarter (normalized field names)
        patch_date = server.get(f'q{quarter}_patch_date', 'Not Set')
        patch_time = server.get(f'q{quarter}_patch_time', 'Not Set')
        approval_status = server.get(f'q{quarter}_approval_status', 'Approved')
        server_name = server.get('server_name', 'Unknown')
        server_timezone = server.get('server_timezone', 'Unknown')
        
        table_rows += f"""
        <tr>
            <td>{server_name}</td>
            <td>{patch_date}</td>
            <td>{patch_time}</td>
            <td>{server_timezone}</td>
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

def auto_approve_pending_servers(args, logger):
    """Auto-approve servers that haven't responded after deadline"""
    try:
        handler = WeeklyFollowupHandler()
        approved_count = handler.auto_approve_pending_servers(args.quarter)
        
        if approved_count > 0:
            logger.info(f"Auto-approved {approved_count} servers for Q{args.quarter}")
        else:
            logger.info("No servers required auto-approval")
            
    except Exception as e:
        logger.error(f"Error in auto-approval: {e}")

def run_intelligent_scheduling(args, logger):
    """Run intelligent scheduling for unscheduled servers"""
    try:
        scheduler = SmartScheduler()
        
        if args.server:
            logger.info(f"Running intelligent scheduling for {args.server}")
            # For single server, we'd need to implement single-server scheduling
            logger.warning("Single server intelligent scheduling not yet implemented")
        else:
            logger.info(f"Running intelligent scheduling for all unscheduled servers in Q{args.quarter}")
            scheduler.assign_smart_schedules(args.quarter)
            
    except Exception as e:
        logger.error(f"Error in intelligent scheduling: {e}")

def analyze_server_load(args, logger):
    """Analyze server load patterns"""
    try:
        predictor = SmartLoadPredictor()
        
        if args.server:
            logger.info(f"Analyzing load patterns for {args.server}")
            recommendation = predictor.analyze_server_load_patterns(args.server)
            
            logger.info(f"Load analysis for {args.server}:")
            logger.info(f"  Recommended time: {recommendation['recommended_time']}")
            logger.info(f"  Confidence: {recommendation['confidence_level']}")
            logger.info(f"  Reasoning: {', '.join(recommendation['reasoning'])}")
            
            if recommendation['risk_factors']:
                logger.warning(f"  Risk factors: {', '.join(recommendation['risk_factors'])}")
            
        else:
            logger.info(f"Analyzing load patterns for all servers in Q{args.quarter}")
            recommendations = predictor.analyze_all_servers(args.quarter)
            logger.info(f"Generated recommendations for {len(recommendations)} servers")
            
    except Exception as e:
        logger.error(f"Error in load analysis: {e}")

def simulate_historical_data(args, logger):
    """Simulate historical data for testing"""
    try:
        predictor = SmartLoadPredictor()
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers(normalize_fields=True)
        
        if args.server:
            logger.info(f"Simulating historical data for {args.server}")
            predictor.simulate_historical_data(args.server, days=30)
        else:
            logger.info("Simulating historical data for all servers")
            for server in servers[:5]:  # Limit to first 5 servers for demo
                server_name = server.get('server_name', 'Unknown')
                predictor.simulate_historical_data(server_name, days=30)
                logger.info(f"Generated simulation data for {server_name}")
            
    except Exception as e:
        logger.error(f"Error simulating data: {e}")

def test_patching_script_config(args, logger):
    """Test patching script configuration on a random server"""
    try:
        from utils.ssh_manager import SSHManager
        
        logger.info("Testing patching script configuration")
        
        # Get servers from CSV
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers()
        
        if not servers:
            logger.error("No servers found in CSV")
            return
        
        # Pick random server or use specified server
        if args.server:
            test_server = None
            for server in servers:
                server_name = server.get('server_name', server.get('Server Name', ''))
                if server_name == args.server:
                    test_server = server
                    break
            if not test_server:
                logger.error(f"Server {args.server} not found in CSV")
                return
        else:
            import random
            test_server = random.choice(servers)
        
        server_name = test_server.get('server_name', test_server.get('Server Name', 'Unknown'))
        
        logger.info(f"Testing patching script on server: {server_name}")
        logger.info(f"Patching script path: {Config.PATCHING_SCRIPT_PATH}")
        logger.info(f"Script validation enabled: {Config.VALIDATE_PATCHING_SCRIPT}")
        
        # Test using SSH manager
        ssh_manager = SSHManager()
        
        # Test SSH connection
        logger.info("Testing SSH connection...")
        if not ssh_manager.test_connection(server_name):
            logger.error(f"SSH connection failed to {server_name}")
            return
        logger.info("✓ SSH connection successful")
        
        # Test script existence if validation is enabled
        if Config.VALIDATE_PATCHING_SCRIPT:
            logger.info("Testing script existence...")
            if not ssh_manager.check_file_exists(server_name, Config.PATCHING_SCRIPT_PATH):
                logger.error(f"Script {Config.PATCHING_SCRIPT_PATH} not found on {server_name}")
                return
            logger.info("✓ Script exists")
            
            # Test script is executable
            logger.info("Testing script executable permissions...")
            if not ssh_manager.check_file_executable(server_name, Config.PATCHING_SCRIPT_PATH):
                logger.error(f"Script {Config.PATCHING_SCRIPT_PATH} is not executable on {server_name}")
                return
            logger.info("✓ Script is executable")
        
        # Get system info
        logger.info("Getting system information...")
        sys_info = ssh_manager.get_system_info(server_name)
        logger.info(f"✓ System info retrieved:")
        for key, value in sys_info.items():
            logger.info(f"  {key}: {value}")
        
        # Validate prerequisites
        logger.info("Validating patching prerequisites...")
        success, issues = ssh_manager.validate_patching_prerequisites(server_name)
        if success:
            logger.info("✓ All patching prerequisites met")
        else:
            logger.warning("⚠ Some prerequisites not met:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        logger.info("Patching script configuration test completed successfully")
        
    except Exception as e:
        logger.error(f"Error testing patching script configuration: {e}")

def show_patching_config(logger):
    """Show current patching script configuration"""
    try:
        logger.info("Current Patching Script Configuration:")
        logger.info("=" * 50)
        logger.info(f"Script Path: {Config.PATCHING_SCRIPT_PATH}")
        logger.info(f"Validation Enabled: {Config.VALIDATE_PATCHING_SCRIPT}")
        logger.info(f"SSH Connection Timeout: {Config.SSH_CONNECTION_TIMEOUT} seconds")
        logger.info(f"SSH Command Timeout: {Config.SSH_COMMAND_TIMEOUT} seconds")
        logger.info(f"Max Retry Attempts: {Config.MAX_RETRY_ATTEMPTS}")
        logger.info("=" * 50)
        
        # Show usage example
        logger.info("CLI Usage Examples:")
        logger.info("  Test script on random server:")
        logger.info("    python3 main.py --test-patching-script")
        logger.info("  Test script on specific server:")
        logger.info("    python3 main.py --test-patching-script --server <server_name>")
        logger.info("  Show this configuration:")
        logger.info("    python3 main.py --show-patching-config")
        
    except Exception as e:
        logger.error(f"Error showing patching configuration: {e}")

if __name__ == "__main__":
    main()
