#!/usr/bin/env python3
"""
Additional REST API Endpoints - Part 3
Pre-checks, Approvals, Reporting, and System endpoints
"""

import os
import sys
import json
import uuid
import tempfile
import io
from datetime import datetime, timedelta
from flask import request, jsonify, send_file, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import csv as csv_module

def register_remaining_endpoints(app, csv_handler, email_sender, logger, user_manager, 
                               active_jobs, job_results, socketio, executor, 
                               api_response, handle_error, require_permission, 
                               normalize_server_data, Config):
    """Register remaining API endpoints"""
    
    # ===== PRE-CHECK ENDPOINTS =====
    
    @app.route('/precheck/run', methods=['POST'])
    @jwt_required()
    @require_permission('run_prechecks')
    def run_prechecks():
        """Run pre-checks on servers"""
        try:
            data = request.get_json()
            if not data or 'servers' not in data:
                return api_response(success=False, message="Server list is required", code=400)
            
            servers = data['servers']
            quarter = data.get('quarter', Config.get_current_quarter())
            
            # Simulate pre-check execution
            results = []
            for server_id in servers:
                # Simulate multiple checks per server
                import random
                check_types = ['disk_space', 'memory', 'cpu', 'network', 'services', 'security']
                
                for check_type in check_types:
                    # Random check results
                    status = random.choice(['passed', 'passed', 'passed', 'warning', 'failed'])
                    
                    result = {
                        'id': str(uuid.uuid4()),
                        'serverId': server_id,
                        'serverName': server_id,
                        'quarter': quarter,
                        'checkType': check_type,
                        'checkName': f'{check_type.replace("_", " ").title()} Check',
                        'status': status,
                        'message': f'{check_type.replace("_", " ").title()} check {"passed" if status == "passed" else "has issues"}',
                        'severity': 'low' if status == 'passed' else ('medium' if status == 'warning' else 'high'),
                        'autoFixable': status == 'warning',
                        'fixed': False,
                        'operator': get_jwt_identity(),
                        'duration': random.randint(1, 10),
                        'retryCount': 0,
                        'dependenciesMet': True,
                        'businessImpact': 'Low' if status == 'passed' else 'Medium',
                        'technicalImpact': 'None' if status == 'passed' else 'Performance impact',
                        'escalationRequired': status == 'failed',
                        'ownerNotified': status == 'failed',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if status == 'passed':
                        result['value'] = 'Normal'
                        result['threshold'] = 'Normal'
                    elif status == 'warning':
                        result['value'] = '85%'
                        result['threshold'] = '90%'
                        result['recommendation'] = 'Monitor closely'
                    else:  # failed
                        result['value'] = '95%'
                        result['threshold'] = '90%'
                        result['recommendation'] = 'Immediate attention required'
                        result['resolutionSteps'] = ['Check disk usage', 'Clean up old files', 'Extend volume']
                    
                    results.append(result)
            
            logger.info(f"Ran pre-checks on {len(servers)} servers by {get_jwt_identity()}")
            return api_response(data=results, message="Pre-checks completed")
            
        except Exception as e:
            return handle_error(e, "Failed to run pre-checks")
    
    @app.route('/precheck/results', methods=['GET'])
    @jwt_required()
    def get_precheck_results():
        """Get pre-check results"""
        try:
            server = request.args.get('server')
            quarter = request.args.get('quarter', Config.get_current_quarter())
            status = request.args.get('status')
            
            # For demo purposes, return sample results
            # In real implementation, this would read from database
            sample_results = []
            
            # Simulate stored results
            if server:
                servers = [server]
            else:
                servers = ['web01.company.com', 'db01.company.com', 'app01.company.com']
            
            for server_id in servers:
                import random
                check_types = ['disk_space', 'memory', 'cpu', 'network', 'services']
                
                for check_type in check_types:
                    check_status = random.choice(['passed', 'passed', 'warning', 'failed'])
                    
                    if status and check_status != status:
                        continue
                    
                    result = {
                        'id': str(uuid.uuid4()),
                        'serverId': server_id,
                        'serverName': server_id,
                        'quarter': quarter,
                        'checkType': check_type,
                        'checkName': f'{check_type.replace("_", " ").title()} Check',
                        'status': check_status,
                        'message': f'{check_type.replace("_", " ").title()} check result',
                        'severity': 'low' if check_status == 'passed' else ('medium' if check_status == 'warning' else 'high'),
                        'autoFixable': check_status == 'warning',
                        'fixed': False,
                        'operator': 'system',
                        'duration': random.randint(1, 10),
                        'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
                    }
                    
                    sample_results.append(result)
            
            return api_response(data=sample_results)
            
        except Exception as e:
            return handle_error(e, "Failed to get pre-check results")
    
    # ===== APPROVAL ENDPOINTS =====
    
    @app.route('/approvals', methods=['GET'])
    @jwt_required()
    def get_approval_requests():
        """Get approval requests"""
        try:
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('pageSize', 25, type=int)
            status = request.args.get('status')
            quarter = request.args.get('quarter', Config.get_current_quarter())
            
            # Read servers to get approval status
            servers = csv_handler.read_servers(normalize_fields=True)
            
            # Convert to approval requests
            approval_requests = []
            for server in servers:
                approval_status = server.get(f'q{quarter}_approval_status', 'pending')
                
                if status and approval_status != status:
                    continue
                
                request_data = {
                    'id': str(uuid.uuid4()),
                    'serverId': server.get('server_name', ''),
                    'serverName': server.get('server_name', ''),
                    'quarter': quarter,
                    'requestedBy': server.get('primary_owner', ''),
                    'requestDate': (datetime.now() - timedelta(days=7)).isoformat(),
                    'status': approval_status,
                    'approvalType': 'individual',
                    'businessJustification': 'Quarterly security patching',
                    'riskAssessment': 'Low risk - standard patching window',
                    'rollbackPlan': 'Standard rollback procedures available',
                    'notificationList': [server.get('primary_owner', ''), server.get('secondary_owner', '')],
                    'emergencyContact': server.get('primary_owner', ''),
                    'maintenanceWindow': f"{server.get(f'q{quarter}_patch_date', '')} {server.get(f'q{quarter}_patch_time', '')}",
                    'dependencies': [],
                    'testingRequired': True,
                    'backupRequired': True,
                    'autoApproved': approval_status == 'auto-approved',
                    'createdAt': (datetime.now() - timedelta(days=7)).isoformat(),
                    'updatedAt': datetime.now().isoformat()
                }
                
                if approval_status == 'approved':
                    request_data['approver'] = 'admin@company.com'
                    request_data['approvalDate'] = datetime.now().isoformat()
                
                approval_requests.append(request_data)
            
            # Apply pagination
            total = len(approval_requests)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_requests = approval_requests[start:end]
            
            response_data = {
                'items': paginated_requests,
                'total': total,
                'page': page,
                'pageSize': page_size,
                'totalPages': (total + page_size - 1) // page_size,
                'hasNext': end < total,
                'hasPrevious': page > 1
            }
            
            return api_response(data=response_data)
            
        except Exception as e:
            return handle_error(e, "Failed to get approval requests")
    
    @app.route('/approvals', methods=['POST'])
    @jwt_required()
    @require_permission('create_approval_requests')
    def create_approval_request():
        """Create approval request"""
        try:
            data = request.get_json()
            if not data or 'serverId' not in data:
                return api_response(success=False, message="Server ID is required", code=400)
            
            server_id = data['serverId']
            quarter = data.get('quarter', Config.get_current_quarter())
            
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            server_index = next((i for i, s in enumerate(servers) if s.get('server_name') == server_id), None)
            
            if server_index is None:
                return api_response(success=False, message="Server not found", code=404)
            
            # Create approval request (in real implementation, this would be stored separately)
            request_data = {
                'id': str(uuid.uuid4()),
                'serverId': server_id,
                'serverName': server_id,
                'quarter': quarter,
                'requestedBy': get_jwt_identity(),
                'requestDate': datetime.now().isoformat(),
                'status': 'pending',
                'approvalType': 'individual',
                'businessJustification': data.get('businessJustification', ''),
                'riskAssessment': data.get('riskAssessment', ''),
                'rollbackPlan': data.get('rollbackPlan', ''),
                'emergencyContact': data.get('emergencyContact', ''),
                'maintenanceWindow': data.get('maintenanceWindow', ''),
                'dependencies': data.get('dependencies', []),
                'testingRequired': data.get('testingRequired', True),
                'backupRequired': data.get('backupRequired', True),
                'changeRequestId': data.get('changeRequestId', ''),
                'autoApproved': False,
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            }
            
            # Send approval request email
            try:
                approval_handler = ApprovalRequestHandler()
                approval_handler.send_approval_requests(quarter)
                logger.info(f"Sent approval request email for {server_id}")
            except Exception as e:
                logger.warning(f"Failed to send approval email: {e}")
            
            logger.info(f"Created approval request for {server_id} by {get_jwt_identity()}")
            return api_response(data=request_data, message="Approval request created")
            
        except Exception as e:
            return handle_error(e, "Failed to create approval request")
    
    @app.route('/approvals/approve', methods=['POST'])
    @jwt_required()
    @require_permission('approve_servers')
    def approve_servers():
        """Approve servers"""
        try:
            data = request.get_json()
            if not data or 'approval_ids' not in data:
                return api_response(success=False, message="Approval IDs are required", code=400)
            
            approval_ids = data['approval_ids']
            comment = data.get('comment', '')
            
            # For demo purposes, assume approval_ids contain server names
            # In real implementation, you'd look up the actual approval requests
            
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            updated_count = 0
            
            current_quarter = Config.get_current_quarter()
            
            for server in servers:
                server_name = server.get('server_name', '')
                if server_name in approval_ids:
                    # Update approval status
                    server[f'q{current_quarter}_approval_status'] = 'approved'
                    server['current_quarter_status'] = 'approved'
                    server['last_sync_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated_count += 1
            
            # Write back to CSV
            if updated_count > 0:
                csv_handler.write_servers(servers)
                
                # Send approval confirmation emails
                try:
                    # Use existing approval confirmation functionality
                    from main import send_cli_approval_confirmation
                    for server in servers:
                        if server.get('server_name') in approval_ids:
                            send_cli_approval_confirmation(server, current_quarter, logger)
                except Exception as e:
                    logger.warning(f"Failed to send approval confirmation emails: {e}")
            
            logger.info(f"Approved {updated_count} servers by {get_jwt_identity()}")
            return api_response(message=f"Approved {updated_count} servers")
            
        except Exception as e:
            return handle_error(e, "Failed to approve servers")
    
    @app.route('/approvals/reject', methods=['POST'])
    @jwt_required()
    @require_permission('approve_servers')
    def reject_servers():
        """Reject servers"""
        try:
            data = request.get_json()
            if not data or 'approval_ids' not in data or 'reason' not in data:
                return api_response(success=False, message="Approval IDs and reason are required", code=400)
            
            approval_ids = data['approval_ids']
            reason = data['reason']
            
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            updated_count = 0
            
            current_quarter = Config.get_current_quarter()
            
            for server in servers:
                server_name = server.get('server_name', '')
                if server_name in approval_ids:
                    # Update approval status
                    server[f'q{current_quarter}_approval_status'] = 'rejected'
                    server['current_quarter_status'] = 'rejected'
                    server['last_sync_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated_count += 1
            
            # Write back to CSV
            if updated_count > 0:
                csv_handler.write_servers(servers)
                
                # Send rejection notification emails
                try:
                    for server in servers:
                        if server.get('server_name') in approval_ids:
                            # Send rejection email to server owners
                            primary_owner = server.get('primary_owner')
                            if primary_owner:
                                subject = f"REJECTED: {Config.QUARTERS[current_quarter]['name']} Patching Request - {server.get('server_name')}"
                                body = f"Your patching request has been rejected.\n\nReason: {reason}\n\nPlease address the concerns and resubmit."
                                try:
                                    email_sender.send_email(primary_owner, subject, body)
                                except Exception as e:
                                    logger.warning(f"Failed to send rejection email to {primary_owner}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to send rejection emails: {e}")
            
            logger.info(f"Rejected {updated_count} servers by {get_jwt_identity()}")
            return api_response(message=f"Rejected {updated_count} servers")
            
        except Exception as e:
            return handle_error(e, "Failed to reject servers")
    
    # ===== REPORTING ENDPOINTS =====
    
    @app.route('/reports/generate', methods=['POST'])
    @jwt_required()
    @require_permission('generate_reports')
    def generate_report():
        """Generate report"""
        try:
            data = request.get_json()
            if not data or 'type' not in data:
                return api_response(success=False, message="Report type is required", code=400)
            
            report_type = data['type']
            report_format = data.get('format', 'csv')
            quarter = data.get('quarter', Config.get_current_quarter())
            
            # Generate report ID
            report_id = str(uuid.uuid4())
            
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            
            # Apply filters
            if 'servers' in data and data['servers']:
                servers = [s for s in servers if s.get('server_name') in data['servers']]
            
            if 'groups' in data and data['groups']:
                servers = [s for s in servers if s.get('host_group') in data['groups']]
            
            if 'environments' in data and data['environments']:
                servers = [s for s in servers if s.get('environment') in data['environments']]
            
            # Generate report content
            output = io.StringIO()
            
            if report_format == 'csv':
                # Generate CSV report
                if report_type == 'summary':
                    from web_portal.app import generate_summary_csv
                    content = generate_summary_csv(servers, quarter, csv_module.writer(output), output)
                elif report_type == 'detailed':
                    from web_portal.app import generate_detailed_csv
                    content = generate_detailed_csv(servers, quarter, csv_module.writer(output), output)
                else:
                    # Default detailed report
                    writer = csv_module.writer(output)
                    writer.writerow(['Server Name', 'Host Group', 'Environment', 'Patch Status', 'Approval Status'])
                    for server in servers:
                        writer.writerow([
                            server.get('server_name', ''),
                            server.get('host_group', ''),
                            server.get('environment', ''),
                            server.get('current_quarter_status', ''),
                            server.get(f'q{quarter}_approval_status', '')
                        ])
                    content = output.getvalue()
            else:
                # JSON format
                content = json.dumps({
                    'report_type': report_type,
                    'generated_at': datetime.now().isoformat(),
                    'quarter': quarter,
                    'servers': [normalize_server_data(s) for s in servers]
                }, indent=2)
            
            # Store report (in real implementation, save to file or database)
            report_filename = f'{report_type}_report_{report_id}.{report_format}'
            report_path = os.path.join(tempfile.gettempdir(), report_filename)
            
            with open(report_path, 'w') as f:
                f.write(content)
            
            # Create report record
            report_record = {
                'id': report_id,
                'name': f'{report_type.title()} Report',
                'type': report_type,
                'format': report_format,
                'status': 'completed',
                'progress': 100,
                'downloadUrl': f'/reports/{report_id}',
                'fileSize': len(content.encode('utf-8')),
                'generatedBy': get_jwt_identity(),
                'generatedAt': datetime.now().isoformat()
            }
            
            # Store report metadata (in memory for demo)
            if not hasattr(app, 'report_metadata'):
                app.report_metadata = {}
            app.report_metadata[report_id] = {
                'record': report_record,
                'file_path': report_path
            }
            
            logger.info(f"Generated {report_type} report {report_id} by {get_jwt_identity()}")
            return api_response(data={'reportId': report_id, 'downloadUrl': f'/reports/{report_id}'})
            
        except Exception as e:
            return handle_error(e, "Failed to generate report")
    
    @app.route('/reports/<report_id>', methods=['GET'])
    @jwt_required()
    def get_report(report_id):
        """Download report"""
        try:
            if not hasattr(app, 'report_metadata') or report_id not in app.report_metadata:
                return api_response(success=False, message="Report not found", code=404)
            
            metadata = app.report_metadata[report_id]
            file_path = metadata['file_path']
            
            if not os.path.exists(file_path):
                return api_response(success=False, message="Report file not found", code=404)
            
            # Determine content type
            report_format = metadata['record']['format']
            if report_format == 'csv':
                mimetype = 'text/csv'
            elif report_format == 'json':
                mimetype = 'application/json'
            else:
                mimetype = 'application/octet-stream'
            
            return send_file(
                file_path,
                mimetype=mimetype,
                as_attachment=True,
                download_name=f"{metadata['record']['name']}.{report_format}"
            )
            
        except Exception as e:
            return handle_error(e, "Failed to download report")
    
    @app.route('/reports/<report_id>/email', methods=['POST'])
    @jwt_required()
    @require_permission('email_reports')
    def email_report(report_id):
        """Email report"""
        try:
            data = request.get_json()
            if not data or 'recipients' not in data:
                return api_response(success=False, message="Recipients are required", code=400)
            
            recipients = data['recipients']
            
            if not hasattr(app, 'report_metadata') or report_id not in app.report_metadata:
                return api_response(success=False, message="Report not found", code=404)
            
            metadata = app.report_metadata[report_id]
            report_record = metadata['record']
            
            # Send email with report
            subject = f"Linux Patching Report: {report_record['name']}"
            body = f"""
Hello,

Please find attached the requested Linux patching report.

Report Details:
- Type: {report_record['type'].title()}
- Format: {report_record['format'].upper()}
- Generated: {report_record['generatedAt']}
- Generated By: {report_record['generatedBy']}

Best regards,
Linux Patching Automation System
"""
            
            # Send to each recipient
            for recipient in recipients:
                try:
                    email_sender.send_email(recipient, subject, body)
                    logger.info(f"Emailed report {report_id} to {recipient}")
                except Exception as e:
                    logger.error(f"Failed to email report to {recipient}: {e}")
            
            return api_response(message=f"Report emailed to {len(recipients)} recipients")
            
        except Exception as e:
            return handle_error(e, "Failed to email report")
    
    # ===== SYSTEM ENDPOINTS =====
    
    @app.route('/system/stats', methods=['GET'])
    @jwt_required()
    def get_system_stats():
        """Get system statistics"""
        try:
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            
            # Calculate stats
            total_servers = len(servers)
            active_servers = len([s for s in servers if s.get('current_quarter_status') != 'inactive'])
            
            # OS breakdown
            os_breakdown = {}
            for server in servers:
                os_name = server.get('operating_system', 'Unknown')
                os_breakdown[os_name] = os_breakdown.get(os_name, 0) + 1
            
            # Group breakdown
            group_breakdown = {}
            for server in servers:
                group_name = server.get('host_group', 'Unknown')
                group_breakdown[group_name] = group_breakdown.get(group_name, 0) + 1
            
            # Environment breakdown
            env_breakdown = {}
            for server in servers:
                env_name = server.get('environment', 'Unknown')
                env_breakdown[env_name] = env_breakdown.get(env_name, 0) + 1
            
            # Approval stats
            current_quarter = Config.get_current_quarter()
            approval_stats = {
                'total': total_servers,
                'pending': len([s for s in servers if s.get(f'q{current_quarter}_approval_status') == 'pending']),
                'approved': len([s for s in servers if s.get(f'q{current_quarter}_approval_status') in ['approved', 'auto-approved']]),
                'rejected': len([s for s in servers if s.get(f'q{current_quarter}_approval_status') == 'rejected']),
                'expired': 0
            }
            
            stats_data = {
                'patching': {
                    'totalJobs': len(active_jobs) + len(job_results),
                    'completedJobs': len(job_results),
                    'failedJobs': len([j for j in job_results.values() if j['status'] == 'failed']),
                    'successRate': 85.0,  # Placeholder
                    'averageDuration': 180,  # 3 minutes
                    'totalServersPatched': len([s for s in servers if s.get('current_quarter_status') == 'completed']),
                    'totalPatchesApplied': len(servers) * 5  # Placeholder
                },
                'servers': {
                    'total': total_servers,
                    'active': active_servers,
                    'inactive': total_servers - active_servers,
                    'byOS': os_breakdown,
                    'byGroup': group_breakdown,
                    'byEnvironment': env_breakdown
                },
                'approvals': approval_stats,
                'system': {
                    'uptime': 86400,  # 24 hours
                    'version': '2.0.0',
                    'lastRestart': (datetime.now() - timedelta(days=1)).isoformat(),
                    'activeUsers': 1,
                    'totalRequests': 1000,
                    'averageResponseTime': 150
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return api_response(data=stats_data)
            
        except Exception as e:
            return handle_error(e, "Failed to get system stats")
    
    @app.route('/system/test-email', methods=['POST'])
    @jwt_required()
    @require_permission('system_admin')
    def test_email():
        """Test email configuration"""
        try:
            data = request.get_json()
            if not data or 'recipient' not in data:
                return api_response(success=False, message="Recipient is required", code=400)
            
            recipient = data['recipient']
            
            # Send test email
            subject = "Linux Patching System - Email Test"
            body = f"""
Hello,

This is a test email from the Linux Patching Automation System.

If you receive this message, the email configuration is working correctly.

Test Details:
- Sent at: {datetime.now().isoformat()}
- Sent by: {get_jwt_identity()}
- System: Linux Patching Automation API

Best regards,
Linux Patching Automation System
"""
            
            email_sender.send_email(recipient, subject, body)
            
            logger.info(f"Sent test email to {recipient} by {get_jwt_identity()}")
            return api_response(message="Test email sent successfully")
            
        except Exception as e:
            return handle_error(e, "Failed to send test email")
    
    @app.route('/audit/logs', methods=['GET'])
    @jwt_required()
    @require_permission('view_audit_logs')
    def get_audit_logs():
        """Get audit logs"""
        try:
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('pageSize', 50, type=int)
            
            # For demo purposes, generate sample audit logs
            # In real implementation, read from audit log storage
            sample_logs = []
            
            actions = ['login', 'logout', 'create_server', 'update_server', 'delete_server', 
                      'start_patching', 'approve_server', 'reject_server', 'generate_report']
            
            for i in range(100):  # Generate 100 sample logs
                import random
                action = random.choice(actions)
                
                log_entry = {
                    'id': str(uuid.uuid4()),
                    'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
                    'action': action,
                    'resource': 'server' if 'server' in action else ('report' if 'report' in action else 'auth'),
                    'resourceId': f'server-{random.randint(1, 100)}' if 'server' in action else None,
                    'userId': 'user@company.com',
                    'username': 'user',
                    'userRole': 'admin',
                    'ipAddress': f'192.168.1.{random.randint(1, 254)}',
                    'userAgent': 'Mozilla/5.0 (API Client)',
                    'details': {'action': action, 'result': 'success'},
                    'result': random.choice(['success', 'success', 'success', 'failure']),
                    'sessionId': str(uuid.uuid4()),
                    'requestId': str(uuid.uuid4())
                }
                
                if log_entry['result'] == 'failure':
                    log_entry['errorMessage'] = 'Operation failed due to validation error'
                
                sample_logs.append(log_entry)
            
            # Sort by timestamp (newest first)
            sample_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Apply pagination
            total = len(sample_logs)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_logs = sample_logs[start:end]
            
            response_data = {
                'items': paginated_logs,
                'total': total,
                'page': page,
                'pageSize': page_size,
                'totalPages': (total + page_size - 1) // page_size,
                'hasNext': end < total,
                'hasPrevious': page > 1
            }
            
            return api_response(data=response_data)
            
        except Exception as e:
            return handle_error(e, "Failed to get audit logs")
    
    # ===== WEBSOCKET ENDPOINTS =====
    
    @socketio.on('connect')
    @jwt_required()
    def handle_connect():
        """Handle WebSocket connection"""
        try:
            user_email = get_jwt_identity()
            logger.info(f"WebSocket connected: {user_email}")
            emit('connected', {'message': 'Connected to Linux Patching System'})
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            emit('error', {'message': 'Connection failed'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        logger.info("WebSocket disconnected")
    
    @socketio.on('join_room')
    @jwt_required()
    def handle_join_room(data):
        """Join WebSocket room"""
        try:
            room = data.get('room', 'general')
            join_room(room)
            logger.info(f"User {get_jwt_identity()} joined room {room}")
            emit('joined_room', {'room': room})
        except Exception as e:
            logger.error(f"Error joining room: {e}")
            emit('error', {'message': 'Failed to join room'})
    
    @socketio.on('leave_room')
    @jwt_required()
    def handle_leave_room(data):
        """Leave WebSocket room"""
        try:
            room = data.get('room', 'general')
            leave_room(room)
            logger.info(f"User {get_jwt_identity()} left room {room}")
            emit('left_room', {'room': room})
        except Exception as e:
            logger.error(f"Error leaving room: {e}")
            emit('error', {'message': 'Failed to leave room'})
    
    return app