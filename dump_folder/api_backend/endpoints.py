#!/usr/bin/env python3
"""
Complete REST API Endpoints - Part 2
Additional endpoints for the Linux Patching Automation System
"""

import os
import sys
import json
import uuid
import tempfile
import io
from datetime import datetime
from flask import request, jsonify, send_file, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import csv as csv_module

# This file contains additional endpoints that extend the main app.py

def register_additional_endpoints(app, csv_handler, email_sender, logger, user_manager, 
                                 active_jobs, job_results, socketio, executor, 
                                 api_response, handle_error, require_permission, 
                                 normalize_server_data, create_patching_job, run_patching_job):
    """Register additional API endpoints"""
    
    # ===== SERVER MANAGEMENT ENDPOINTS (CONTINUED) =====
    
    @app.route('/servers', methods=['POST'])
    @jwt_required()
    @require_permission('manage_servers')
    def create_server():
        """Create new server"""
        try:
            data = request.get_json()
            if not data or 'serverName' not in data:
                return api_response(success=False, message="Server name is required", code=400)
            
            # Read existing servers
            servers = csv_handler.read_servers(normalize_fields=True)
            
            # Check if server already exists
            if any(s.get('server_name') == data['serverName'] for s in servers):
                return api_response(success=False, message="Server already exists", code=409)
            
            # Create new server record
            new_server = {
                'server_name': data['serverName'],
                'host_group': data.get('hostGroup', ''),
                'operating_system': data.get('operatingSystem', ''),
                'environment': data.get('environment', 'production'),
                'server_timezone': data.get('serverTimezone', 'UTC'),
                'location': data.get('location', ''),
                'primary_owner': data.get('primaryOwner', get_jwt_identity()),
                'secondary_owner': data.get('secondaryOwner', ''),
                'primary_linux_user': data.get('primaryLinuxUser', ''),
                'secondary_linux_user': data.get('secondaryLinuxUser', ''),
                'patcher_email': data.get('patcherEmail', ''),
                'engr_domain': data.get('engineeringDomain', ''),
                'incident_ticket': data.get('incidentTicket', ''),
                'current_quarter_status': 'pending',
                'q1_approval_status': 'pending',
                'q2_approval_status': 'pending',
                'q3_approval_status': 'pending',
                'q4_approval_status': 'pending',
                'last_sync_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sync_status': 'success'
            }
            
            # Add to servers list
            servers.append(new_server)
            
            # Write back to CSV
            csv_handler.write_servers(servers)
            
            logger.info(f"Created new server: {data['serverName']} by {get_jwt_identity()}")
            return api_response(data=normalize_server_data(new_server), message="Server created successfully")
            
        except Exception as e:
            return handle_error(e, "Failed to create server")
    
    @app.route('/servers/<server_id>', methods=['PUT'])
    @jwt_required()
    @require_permission('manage_servers')
    def update_server(server_id):
        """Update server"""
        try:
            data = request.get_json()
            if not data:
                return api_response(success=False, message="Update data is required", code=400)
            
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            server_index = next((i for i, s in enumerate(servers) if s.get('server_name') == server_id), None)
            
            if server_index is None:
                return api_response(success=False, message="Server not found", code=404)
            
            # Check permissions
            current_user_email = get_jwt_identity()
            user_info = user_manager.get_user_info(current_user_email)
            server = servers[server_index]
            
            if (user_info['role'] != 'admin' and 
                server.get('primary_owner') != current_user_email and 
                server.get('secondary_owner') != current_user_email):
                return api_response(success=False, message="Access denied", code=403)
            
            # Update server fields
            updateable_fields = {
                'hostGroup': 'host_group',
                'operatingSystem': 'operating_system',
                'environment': 'environment',
                'serverTimezone': 'server_timezone',
                'location': 'location',
                'primaryOwner': 'primary_owner',
                'secondaryOwner': 'secondary_owner',
                'primaryLinuxUser': 'primary_linux_user',
                'secondaryLinuxUser': 'secondary_linux_user',
                'patcherEmail': 'patcher_email',
                'engineeringDomain': 'engr_domain',
                'incidentTicket': 'incident_ticket',
                'q1PatchDate': 'q1_patch_date',
                'q1PatchTime': 'q1_patch_time',
                'q2PatchDate': 'q2_patch_date',
                'q2PatchTime': 'q2_patch_time',
                'q3PatchDate': 'q3_patch_date',
                'q3PatchTime': 'q3_patch_time',
                'q4PatchDate': 'q4_patch_date',
                'q4PatchTime': 'q4_patch_time'
            }
            
            for api_field, csv_field in updateable_fields.items():
                if api_field in data:
                    servers[server_index][csv_field] = data[api_field]
            
            # Update timestamp
            servers[server_index]['last_sync_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Write back to CSV
            csv_handler.write_servers(servers)
            
            logger.info(f"Updated server: {server_id} by {get_jwt_identity()}")
            return api_response(data=normalize_server_data(servers[server_index]), message="Server updated successfully")
            
        except Exception as e:
            return handle_error(e, "Failed to update server")
    
    @app.route('/servers/<server_id>', methods=['DELETE'])
    @jwt_required()
    @require_permission('manage_servers')
    def delete_server(server_id):
        """Delete server"""
        try:
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            server_index = next((i for i, s in enumerate(servers) if s.get('server_name') == server_id), None)
            
            if server_index is None:
                return api_response(success=False, message="Server not found", code=404)
            
            # Check permissions
            current_user_email = get_jwt_identity()
            user_info = user_manager.get_user_info(current_user_email)
            server = servers[server_index]
            
            if (user_info['role'] != 'admin' and 
                server.get('primary_owner') != current_user_email):
                return api_response(success=False, message="Access denied", code=403)
            
            # Remove server
            removed_server = servers.pop(server_index)
            
            # Write back to CSV
            csv_handler.write_servers(servers)
            
            logger.info(f"Deleted server: {server_id} by {get_jwt_identity()}")
            return api_response(message="Server deleted successfully")
            
        except Exception as e:
            return handle_error(e, "Failed to delete server")
    
    @app.route('/servers/<server_id>/test', methods=['POST'])
    @jwt_required()
    @require_permission('test_connectivity')
    def test_server_connectivity(server_id):
        """Test server connectivity"""
        try:
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            server = next((s for s in servers if s.get('server_name') == server_id), None)
            
            if not server:
                return api_response(success=False, message="Server not found", code=404)
            
            # Simulate connectivity test
            import time
            import random
            
            start_time = time.time()
            time.sleep(random.uniform(0.5, 2.0))  # Simulate network delay
            
            # Random success/failure for demo
            connected = random.choice([True, True, True, False])  # 75% success rate
            response_time = int((time.time() - start_time) * 1000)  # Convert to ms
            
            result = {
                'connected': connected,
                'message': 'Connection successful' if connected else 'Connection failed - timeout',
                'responseTime': response_time
            }
            
            logger.info(f"Connectivity test for {server_id}: {result}")
            return api_response(data=result)
            
        except Exception as e:
            return handle_error(e, "Failed to test connectivity")
    
    @app.route('/servers/import', methods=['POST'])
    @jwt_required()
    @require_permission('import_servers')
    def import_servers():
        """Import servers from CSV file"""
        try:
            if 'file' not in request.files:
                return api_response(success=False, message="No file provided", code=400)
            
            file = request.files['file']
            if file.filename == '':
                return api_response(success=False, message="No file selected", code=400)
            
            if not file.filename.endswith('.csv'):
                return api_response(success=False, message="File must be a CSV", code=400)
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as tmp_file:
                file.save(tmp_file.name)
                tmp_file_path = tmp_file.name
            
            try:
                # Use existing CSV import functionality
                from utils.external_csv_importer import ExternalCSVImporter
                importer = ExternalCSVImporter()
                
                # Validate and import
                is_valid, validation_issues = importer.validate_external_csv(tmp_file_path)
                
                if not is_valid:
                    return api_response(success=False, 
                                      message="CSV validation failed", 
                                      data={'errors': validation_issues}, 
                                      code=400)
                
                # Import with internal data preservation
                success, message = importer.import_external_csv(tmp_file_path, preserve_internal_data=True)
                
                if success:
                    # Count imported servers
                    servers = csv_handler.read_servers(normalize_fields=True)
                    imported_count = len(servers)
                    
                    logger.info(f"Imported {imported_count} servers from CSV by {get_jwt_identity()}")
                    return api_response(data={'imported': imported_count, 'errors': []}, 
                                      message="Import successful")
                else:
                    return api_response(success=False, 
                                      message="Import failed", 
                                      data={'imported': 0, 'errors': [message]}, 
                                      code=400)
                    
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
        except Exception as e:
            return handle_error(e, "Failed to import servers")
    
    @app.route('/servers/export', methods=['GET'])
    @jwt_required()
    def export_servers():
        """Export servers to CSV"""
        try:
            # Get filters
            group = request.args.get('group')
            environment = request.args.get('environment')
            
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            
            # Apply filters
            if group:
                servers = [s for s in servers if s.get('host_group') == group]
            if environment:
                servers = [s for s in servers if s.get('environment') == environment]
            
            # Create CSV in memory
            output = io.StringIO()
            
            if servers:
                writer = csv_module.DictWriter(output, fieldnames=servers[0].keys())
                writer.writeheader()
                writer.writerows(servers)
            
            # Create response
            mem = io.BytesIO()
            mem.write(output.getvalue().encode('utf-8'))
            mem.seek(0)
            
            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'servers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
        except Exception as e:
            return handle_error(e, "Failed to export servers")
    
    # ===== PATCHING ENDPOINTS =====
    
    @app.route('/patching/status', methods=['GET'])
    @jwt_required()
    def get_patching_status():
        """Get patching status"""
        try:
            quarter = request.args.get('quarter', Config.get_current_quarter())
            
            # Read servers
            servers = csv_handler.read_servers(normalize_fields=True)
            
            # Calculate statistics
            stats = {
                'currentQuarter': quarter,
                'totalServers': len(servers),
                'pendingApproval': 0,
                'approved': 0,
                'scheduled': 0,
                'inProgress': 0,
                'completed': 0,
                'failed': 0,
                'rolledBack': 0,
                'activeOperations': len(active_jobs),
                'lastUpdated': datetime.now().isoformat()
            }
            
            # Count by status
            for server in servers:
                approval_status = server.get(f'q{quarter}_approval_status', 'pending')
                patch_status = server.get('current_quarter_status', 'pending')
                
                if approval_status == 'pending':
                    stats['pendingApproval'] += 1
                elif approval_status in ['approved', 'auto-approved']:
                    stats['approved'] += 1
                
                if patch_status == 'scheduled':
                    stats['scheduled'] += 1
                elif patch_status == 'in_progress':
                    stats['inProgress'] += 1
                elif patch_status == 'completed':
                    stats['completed'] += 1
                elif patch_status == 'failed':
                    stats['failed'] += 1
                elif patch_status == 'rolled_back':
                    stats['rolledBack'] += 1
            
            # Calculate success rate
            total_attempted = stats['completed'] + stats['failed'] + stats['rolledBack']
            stats['successRate'] = (stats['completed'] / total_attempted * 100) if total_attempted > 0 else 0
            
            # Quarterly stats (simplified)
            stats['quarterlyStats'] = {
                quarter: {
                    'total': stats['totalServers'],
                    'completed': stats['completed'],
                    'failed': stats['failed'],
                    'pending': stats['pendingApproval'],
                    'successRate': stats['successRate']
                }
            }
            
            # Group stats
            group_stats = {}
            for server in servers:
                group = server.get('host_group', 'unknown')
                if group not in group_stats:
                    group_stats[group] = {'total': 0, 'completed': 0, 'failed': 0, 'pending': 0}
                
                group_stats[group]['total'] += 1
                patch_status = server.get('current_quarter_status', 'pending')
                if patch_status == 'completed':
                    group_stats[group]['completed'] += 1
                elif patch_status == 'failed':
                    group_stats[group]['failed'] += 1
                elif patch_status == 'pending':
                    group_stats[group]['pending'] += 1
            
            # Calculate success rates for groups
            for group in group_stats:
                total_attempted = group_stats[group]['completed'] + group_stats[group]['failed']
                group_stats[group]['successRate'] = (group_stats[group]['completed'] / total_attempted * 100) if total_attempted > 0 else 0
            
            stats['groupStats'] = group_stats
            
            return api_response(data=stats)
            
        except Exception as e:
            return handle_error(e, "Failed to get patching status")
    
    @app.route('/patching/start', methods=['POST'])
    @jwt_required()
    @require_permission('start_patching')
    def start_patching():
        """Start patching job"""
        try:
            data = request.get_json()
            if not data or 'servers' not in data:
                return api_response(success=False, message="Server list is required", code=400)
            
            servers = data['servers']
            if not servers:
                return api_response(success=False, message="At least one server is required", code=400)
            
            # Create job
            job_id = str(uuid.uuid4())
            job = create_patching_job(job_id, {
                'name': data.get('name', f'Patching Job {job_id[:8]}'),
                'description': data.get('description', ''),
                'servers': servers,
                'quarter': data.get('quarter', Config.get_current_quarter()),
                'dryRun': data.get('dryRun', False),
                'force': data.get('force', False),
                'skipPrecheck': data.get('skipPrecheck', False),
                'skipPostcheck': data.get('skipPostcheck', False)
            })
            
            # Store job
            active_jobs[job_id] = job
            
            # Start job in background
            executor.submit(run_patching_job, job_id)
            
            logger.info(f"Started patching job {job_id} for {len(servers)} servers by {get_jwt_identity()}")
            return api_response(data=job, message="Patching job started")
            
        except Exception as e:
            return handle_error(e, "Failed to start patching")
    
    @app.route('/patching/jobs', methods=['GET'])
    @jwt_required()
    def get_patching_jobs():
        """Get patching jobs"""
        try:
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('pageSize', 25, type=int)
            status = request.args.get('status')
            quarter = request.args.get('quarter')
            
            # Combine active and completed jobs
            all_jobs = list(active_jobs.values()) + list(job_results.values())
            
            # Apply filters
            if status:
                all_jobs = [j for j in all_jobs if j['status'] == status]
            if quarter:
                all_jobs = [j for j in all_jobs if j['quarter'] == quarter]
            
            # Sort by creation date (newest first)
            all_jobs.sort(key=lambda x: x['createdAt'], reverse=True)
            
            # Apply pagination
            total = len(all_jobs)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_jobs = all_jobs[start:end]
            
            response_data = {
                'items': paginated_jobs,
                'total': total,
                'page': page,
                'pageSize': page_size,
                'totalPages': (total + page_size - 1) // page_size,
                'hasNext': end < total,
                'hasPrevious': page > 1
            }
            
            return api_response(data=response_data)
            
        except Exception as e:
            return handle_error(e, "Failed to get patching jobs")
    
    @app.route('/patching/jobs/<job_id>', methods=['GET'])
    @jwt_required()
    def get_patching_job(job_id):
        """Get patching job details"""
        try:
            job = active_jobs.get(job_id) or job_results.get(job_id)
            
            if not job:
                return api_response(success=False, message="Job not found", code=404)
            
            return api_response(data=job)
            
        except Exception as e:
            return handle_error(e, "Failed to get patching job")
    
    @app.route('/patching/jobs/<job_id>/cancel', methods=['POST'])
    @jwt_required()
    @require_permission('cancel_patching')
    def cancel_patching_job(job_id):
        """Cancel patching job"""
        try:
            job = active_jobs.get(job_id)
            
            if not job:
                return api_response(success=False, message="Job not found or already completed", code=404)
            
            # Cancel job
            job['status'] = 'cancelled'
            job['updatedAt'] = datetime.now().isoformat()
            
            # Move to results
            job_results[job_id] = job
            del active_jobs[job_id]
            
            # Emit cancellation
            socketio.emit('job_update', {
                'jobId': job_id,
                'status': 'cancelled',
                'message': 'Job cancelled by user'
            })
            
            logger.info(f"Cancelled patching job {job_id} by {get_jwt_identity()}")
            return api_response(message="Job cancelled successfully")
            
        except Exception as e:
            return handle_error(e, "Failed to cancel job")
    
    return app