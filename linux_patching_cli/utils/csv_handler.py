"""
CSV Handler for Linux Patching Automation
Handles all CSV operations including server inventory, patch history, and reporting
"""

import csv
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import shutil
from pathlib import Path

class CSVHandler:
    """Comprehensive CSV handler for patching automation"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # CSV file paths
        self.servers_file = self.data_dir / "servers.csv"
        self.patch_history_file = self.data_dir / "patch_history.csv"
        self.approval_file = self.data_dir / "approvals.csv"
        self.precheck_file = self.data_dir / "precheck_results.csv"
        self.rollback_file = self.data_dir / "rollback_history.csv"
        
        # Archive directory
        self.archive_dir = self.data_dir / "archives"
        self.archive_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize CSV files with headers if they don't exist"""
        
        # Servers file
        if not self.servers_file.exists():
            self._create_servers_file()
        
        # Patch history file
        if not self.patch_history_file.exists():
            self._create_patch_history_file()
        
        # Approvals file
        if not self.approval_file.exists():
            self._create_approvals_file()
        
        # Precheck results file
        if not self.precheck_file.exists():
            self._create_precheck_file()
        
        # Rollback history file
        if not self.rollback_file.exists():
            self._create_rollback_file()
    
    def _create_servers_file(self):
        """Create servers.csv with proper headers"""
        headers = [
            'Server Name', 'Host Group', 'Operating System', 'Environment',
            'Server Timezone', 'Location', 'Primary Owner', 'Secondary Owner',
            'Primary Linux User', 'Secondary Linux User', 'Patcher Email',
            'Engineering Domain', 'Incident Ticket',
            'Q1 Patch Date', 'Q1 Patch Time', 'Q1 Approval Status',
            'Q2 Patch Date', 'Q2 Patch Time', 'Q2 Approval Status',
            'Q3 Patch Date', 'Q3 Patch Time', 'Q3 Approval Status',
            'Q4 Patch Date', 'Q4 Patch Time', 'Q4 Approval Status',
            'Current Quarter Patching Status', 'Last Sync Date', 'Sync Status',
            'SSH Key Path', 'SSH Port', 'Sudo User', 'Backup Required',
            'Rollback Plan', 'Critical Services', 'Maintenance Window',
            'Patch Group Priority', 'Auto Approve', 'Notification Email',
            'Created Date', 'Modified Date', 'Active Status'
        ]
        
        with open(self.servers_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _create_patch_history_file(self):
        """Create patch_history.csv with proper headers"""
        headers = [
            'Timestamp', 'Server Name', 'Quarter', 'Patch Type', 'Status',
            'Start Time', 'End Time', 'Duration Minutes', 'Patches Applied',
            'Packages Updated', 'Reboot Required', 'Reboot Completed',
            'Pre-Check Status', 'Post-Check Status', 'Error Message',
            'Rollback Status', 'Rollback Reason', 'Operator', 'Approval ID',
            'Patch Window', 'Downtime Minutes', 'Size MB', 'Success Rate',
            'Critical Patches', 'Security Patches', 'Kernel Updated',
            'Services Restarted', 'Disk Usage Before', 'Disk Usage After',
            'Load Average Before', 'Load Average After', 'Memory Usage Before',
            'Memory Usage After', 'Log File Path', 'Backup Path'
        ]
        
        with open(self.patch_history_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _create_approvals_file(self):
        """Create approvals.csv with proper headers"""
        headers = [
            'Approval ID', 'Server Name', 'Quarter', 'Requested By',
            'Request Date', 'Approver', 'Approval Date', 'Status',
            'Approval Type', 'Business Justification', 'Risk Assessment',
            'Rollback Plan', 'Notification List', 'Emergency Contact',
            'Maintenance Window', 'Dependencies', 'Testing Required',
            'Backup Required', 'Change Request ID', 'Comments',
            'Auto Approved', 'Expiry Date', 'Created Date', 'Modified Date'
        ]
        
        with open(self.approval_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _create_precheck_file(self):
        """Create precheck_results.csv with proper headers"""
        headers = [
            'Timestamp', 'Server Name', 'Quarter', 'Check Type',
            'Check Name', 'Status', 'Value', 'Threshold', 'Message',
            'Severity', 'Recommendation', 'Auto Fixable', 'Fixed',
            'Operator', 'Duration Seconds', 'Retry Count', 'Last Retry',
            'Dependencies Met', 'Business Impact', 'Technical Impact',
            'Resolution Steps', 'Escalation Required', 'Owner Notified'
        ]
        
        with open(self.precheck_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _create_rollback_file(self):
        """Create rollback_history.csv with proper headers"""
        headers = [
            'Timestamp', 'Server Name', 'Quarter', 'Rollback Type',
            'Trigger Event', 'Rollback Status', 'Start Time', 'End Time',
            'Duration Minutes', 'Packages Rolled Back', 'Services Affected',
            'Configuration Restored', 'Data Restored', 'Reboot Required',
            'Reboot Completed', 'Verification Status', 'Operator',
            'Approval Required', 'Approver', 'Business Impact',
            'Root Cause', 'Prevention Steps', 'Lessons Learned',
            'Success Rate', 'Error Message', 'Log File Path'
        ]
        
        with open(self.rollback_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def normalize_field_names(self, data: Dict) -> Dict:
        """Normalize field names to lowercase with underscores"""
        normalized = {}
        for key, value in data.items():
            # Convert to lowercase and replace spaces with underscores
            normalized_key = key.lower().replace(' ', '_').replace('-', '_')
            normalized[normalized_key] = value
        return normalized
    
    def denormalize_field_names(self, data: Dict) -> Dict:
        """Convert normalized field names back to original CSV format"""
        field_mapping = {
            'server_name': 'Server Name',
            'host_group': 'Host Group',
            'operating_system': 'Operating System',
            'environment': 'Environment',
            'server_timezone': 'Server Timezone',
            'location': 'Location',
            'primary_owner': 'Primary Owner',
            'secondary_owner': 'Secondary Owner',
            'primary_linux_user': 'Primary Linux User',
            'secondary_linux_user': 'Secondary Linux User',
            'patcher_email': 'Patcher Email',
            'engineering_domain': 'Engineering Domain',
            'incident_ticket': 'Incident Ticket',
            'q1_patch_date': 'Q1 Patch Date',
            'q1_patch_time': 'Q1 Patch Time',
            'q1_approval_status': 'Q1 Approval Status',
            'q2_patch_date': 'Q2 Patch Date',
            'q2_patch_time': 'Q2 Patch Time',
            'q2_approval_status': 'Q2 Approval Status',
            'q3_patch_date': 'Q3 Patch Date',
            'q3_patch_time': 'Q3 Patch Time',
            'q3_approval_status': 'Q3 Approval Status',
            'q4_patch_date': 'Q4 Patch Date',
            'q4_patch_time': 'Q4 Patch Time',
            'q4_approval_status': 'Q4 Approval Status',
            'current_quarter_patching_status': 'Current Quarter Patching Status',
            'last_sync_date': 'Last Sync Date',
            'sync_status': 'Sync Status',
            'ssh_key_path': 'SSH Key Path',
            'ssh_port': 'SSH Port',
            'sudo_user': 'Sudo User',
            'backup_required': 'Backup Required',
            'rollback_plan': 'Rollback Plan',
            'critical_services': 'Critical Services',
            'maintenance_window': 'Maintenance Window',
            'patch_group_priority': 'Patch Group Priority',
            'auto_approve': 'Auto Approve',
            'notification_email': 'Notification Email',
            'created_date': 'Created Date',
            'modified_date': 'Modified Date',
            'active_status': 'Active Status'
        }
        
        denormalized = {}
        for key, value in data.items():
            denormalized_key = field_mapping.get(key, key)
            denormalized[denormalized_key] = value
        
        return denormalized
    
    def read_servers(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Read server inventory with optional filtering"""
        servers = []
        
        try:
            with open(self.servers_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalize field names
                    normalized_row = self.normalize_field_names(row)
                    
                    # Apply filters if provided
                    if filters:
                        include_row = True
                        for filter_key, filter_value in filters.items():
                            if filter_key in normalized_row:
                                if isinstance(filter_value, list):
                                    if normalized_row[filter_key] not in filter_value:
                                        include_row = False
                                        break
                                else:
                                    if normalized_row[filter_key] != filter_value:
                                        include_row = False
                                        break
                        
                        if not include_row:
                            continue
                    
                    servers.append(normalized_row)
        
        except FileNotFoundError:
            return []
        
        return servers
    
    def write_servers(self, servers: List[Dict], backup: bool = True) -> bool:
        """Write server inventory with backup option"""
        try:
            # Create backup if requested
            if backup and self.servers_file.exists():
                backup_name = f"servers_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                backup_path = self.archive_dir / backup_name
                shutil.copy2(self.servers_file, backup_path)
            
            # Write the new data
            with open(self.servers_file, 'w', newline='') as f:
                if servers:
                    # Denormalize field names for CSV
                    denormalized_servers = [self.denormalize_field_names(server) for server in servers]
                    
                    # Get all unique field names
                    all_fields = set()
                    for server in denormalized_servers:
                        all_fields.update(server.keys())
                    
                    # Use standard headers if available, otherwise use discovered fields
                    writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
                    writer.writeheader()
                    writer.writerows(denormalized_servers)
            
            return True
        
        except Exception as e:
            print(f"Error writing servers file: {e}")
            return False
    
    def add_server(self, server_data: Dict) -> bool:
        """Add a new server to inventory"""
        # Add timestamp fields
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        server_data['created_date'] = current_time
        server_data['modified_date'] = current_time
        server_data['active_status'] = 'Active'
        
        # Read existing servers
        servers = self.read_servers()
        
        # Check for duplicates
        server_name = server_data.get('server_name', '')
        if any(s.get('server_name') == server_name for s in servers):
            return False
        
        # Add new server
        servers.append(server_data)
        
        return self.write_servers(servers)
    
    def update_server(self, server_name: str, updates: Dict) -> bool:
        """Update an existing server in inventory"""
        servers = self.read_servers()
        
        # Find and update the server
        server_found = False
        for i, server in enumerate(servers):
            if server.get('server_name') == server_name:
                servers[i].update(updates)
                servers[i]['modified_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                server_found = True
                break
        
        if not server_found:
            return False
        
        return self.write_servers(servers)
    
    def delete_server(self, server_name: str) -> bool:
        """Delete a server from inventory"""
        servers = self.read_servers()
        
        # Filter out the server to delete
        original_count = len(servers)
        servers = [s for s in servers if s.get('server_name') != server_name]
        
        if len(servers) == original_count:
            return False  # Server not found
        
        return self.write_servers(servers)
    
    def get_server(self, server_name: str) -> Optional[Dict]:
        """Get a specific server by name"""
        servers = self.read_servers()
        
        for server in servers:
            if server.get('server_name') == server_name:
                return server
        
        return None
    
    def get_servers_by_group(self, group: str) -> List[Dict]:
        """Get all servers in a specific host group"""
        return self.read_servers(filters={'host_group': group})
    
    def get_servers_by_quarter(self, quarter: str) -> List[Dict]:
        """Get servers scheduled for a specific quarter"""
        servers = self.read_servers()
        quarter_servers = []
        
        patch_date_field = f'q{quarter[-1]}_patch_date'
        
        for server in servers:
            if server.get(patch_date_field):
                quarter_servers.append(server)
        
        return quarter_servers
    
    def record_patch_history(self, patch_data: Dict) -> bool:
        """Record patch execution history"""
        try:
            # Add timestamp if not provided
            if 'timestamp' not in patch_data:
                patch_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Write to patch history file
            with open(self.patch_history_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_patch_history_headers())
                writer.writerow(patch_data)
            
            return True
        
        except Exception as e:
            print(f"Error recording patch history: {e}")
            return False
    
    def get_patch_history(self, server_name: Optional[str] = None, 
                         quarter: Optional[str] = None, 
                         days: Optional[int] = None) -> List[Dict]:
        """Get patch history with optional filtering"""
        history = []
        
        try:
            with open(self.patch_history_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Apply filters
                    if server_name and row.get('Server Name') != server_name:
                        continue
                    
                    if quarter and row.get('Quarter') != quarter:
                        continue
                    
                    if days:
                        try:
                            row_date = datetime.strptime(row.get('Timestamp', ''), '%Y-%m-%d %H:%M:%S')
                            cutoff_date = datetime.now() - timedelta(days=days)
                            if row_date < cutoff_date:
                                continue
                        except ValueError:
                            continue
                    
                    history.append(row)
        
        except FileNotFoundError:
            return []
        
        return history
    
    def _get_patch_history_headers(self) -> List[str]:
        """Get patch history CSV headers"""
        return [
            'Timestamp', 'Server Name', 'Quarter', 'Patch Type', 'Status',
            'Start Time', 'End Time', 'Duration Minutes', 'Patches Applied',
            'Packages Updated', 'Reboot Required', 'Reboot Completed',
            'Pre-Check Status', 'Post-Check Status', 'Error Message',
            'Rollback Status', 'Rollback Reason', 'Operator', 'Approval ID',
            'Patch Window', 'Downtime Minutes', 'Size MB', 'Success Rate',
            'Critical Patches', 'Security Patches', 'Kernel Updated',
            'Services Restarted', 'Disk Usage Before', 'Disk Usage After',
            'Load Average Before', 'Load Average After', 'Memory Usage Before',
            'Memory Usage After', 'Log File Path', 'Backup Path'
        ]
    
    def record_approval(self, approval_data: Dict) -> bool:
        """Record approval request or decision"""
        try:
            # Generate approval ID if not provided
            if 'approval_id' not in approval_data:
                approval_data['approval_id'] = f"APR_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Add timestamp
            if 'created_date' not in approval_data:
                approval_data['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Write to approvals file
            with open(self.approval_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_approvals_headers())
                writer.writerow(approval_data)
            
            return True
        
        except Exception as e:
            print(f"Error recording approval: {e}")
            return False
    
    def get_approvals(self, status: Optional[str] = None, 
                     quarter: Optional[str] = None) -> List[Dict]:
        """Get approval records with optional filtering"""
        approvals = []
        
        try:
            with open(self.approval_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Apply filters
                    if status and row.get('Status') != status:
                        continue
                    
                    if quarter and row.get('Quarter') != quarter:
                        continue
                    
                    approvals.append(row)
        
        except FileNotFoundError:
            return []
        
        return approvals
    
    def _get_approvals_headers(self) -> List[str]:
        """Get approvals CSV headers"""
        return [
            'Approval ID', 'Server Name', 'Quarter', 'Requested By',
            'Request Date', 'Approver', 'Approval Date', 'Status',
            'Approval Type', 'Business Justification', 'Risk Assessment',
            'Rollback Plan', 'Notification List', 'Emergency Contact',
            'Maintenance Window', 'Dependencies', 'Testing Required',
            'Backup Required', 'Change Request ID', 'Comments',
            'Auto Approved', 'Expiry Date', 'Created Date', 'Modified Date'
        ]
    
    def record_precheck(self, precheck_data: Dict) -> bool:
        """Record pre-check results"""
        try:
            # Add timestamp if not provided
            if 'timestamp' not in precheck_data:
                precheck_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Write to precheck file
            with open(self.precheck_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_precheck_headers())
                writer.writerow(precheck_data)
            
            return True
        
        except Exception as e:
            print(f"Error recording precheck: {e}")
            return False
    
    def get_precheck_results(self, server_name: Optional[str] = None,
                           quarter: Optional[str] = None,
                           status: Optional[str] = None) -> List[Dict]:
        """Get pre-check results with optional filtering"""
        results = []
        
        try:
            with open(self.precheck_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Apply filters
                    if server_name and row.get('Server Name') != server_name:
                        continue
                    
                    if quarter and row.get('Quarter') != quarter:
                        continue
                    
                    if status and row.get('Status') != status:
                        continue
                    
                    results.append(row)
        
        except FileNotFoundError:
            return []
        
        return results
    
    def _get_precheck_headers(self) -> List[str]:
        """Get precheck CSV headers"""
        return [
            'Timestamp', 'Server Name', 'Quarter', 'Check Type',
            'Check Name', 'Status', 'Value', 'Threshold', 'Message',
            'Severity', 'Recommendation', 'Auto Fixable', 'Fixed',
            'Operator', 'Duration Seconds', 'Retry Count', 'Last Retry',
            'Dependencies Met', 'Business Impact', 'Technical Impact',
            'Resolution Steps', 'Escalation Required', 'Owner Notified'
        ]
    
    def record_rollback(self, rollback_data: Dict) -> bool:
        """Record rollback operation"""
        try:
            # Add timestamp if not provided
            if 'timestamp' not in rollback_data:
                rollback_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Write to rollback file
            with open(self.rollback_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_rollback_headers())
                writer.writerow(rollback_data)
            
            return True
        
        except Exception as e:
            print(f"Error recording rollback: {e}")
            return False
    
    def get_rollback_history(self, server_name: Optional[str] = None,
                           quarter: Optional[str] = None) -> List[Dict]:
        """Get rollback history with optional filtering"""
        history = []
        
        try:
            with open(self.rollback_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Apply filters
                    if server_name and row.get('Server Name') != server_name:
                        continue
                    
                    if quarter and row.get('Quarter') != quarter:
                        continue
                    
                    history.append(row)
        
        except FileNotFoundError:
            return []
        
        return history
    
    def _get_rollback_headers(self) -> List[str]:
        """Get rollback CSV headers"""
        return [
            'Timestamp', 'Server Name', 'Quarter', 'Rollback Type',
            'Trigger Event', 'Rollback Status', 'Start Time', 'End Time',
            'Duration Minutes', 'Packages Rolled Back', 'Services Affected',
            'Configuration Restored', 'Data Restored', 'Reboot Required',
            'Reboot Completed', 'Verification Status', 'Operator',
            'Approval Required', 'Approver', 'Business Impact',
            'Root Cause', 'Prevention Steps', 'Lessons Learned',
            'Success Rate', 'Error Message', 'Log File Path'
        ]
    
    def export_data(self, export_type: str = 'all', 
                   format: str = 'csv', 
                   output_dir: str = 'exports') -> Dict[str, str]:
        """Export data to various formats"""
        export_dir = Path(output_dir)
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exported_files = {}
        
        try:
            if export_type in ['all', 'servers']:
                filename = f"servers_export_{timestamp}.{format}"
                filepath = export_dir / filename
                if format == 'csv':
                    shutil.copy2(self.servers_file, filepath)
                elif format == 'json':
                    servers = self.read_servers()
                    with open(filepath, 'w') as f:
                        json.dump(servers, f, indent=2)
                exported_files['servers'] = str(filepath)
            
            if export_type in ['all', 'history']:
                filename = f"patch_history_export_{timestamp}.{format}"
                filepath = export_dir / filename
                if format == 'csv':
                    shutil.copy2(self.patch_history_file, filepath)
                elif format == 'json':
                    history = self.get_patch_history()
                    with open(filepath, 'w') as f:
                        json.dump(history, f, indent=2)
                exported_files['history'] = str(filepath)
            
            if export_type in ['all', 'approvals']:
                filename = f"approvals_export_{timestamp}.{format}"
                filepath = export_dir / filename
                if format == 'csv':
                    shutil.copy2(self.approval_file, filepath)
                elif format == 'json':
                    approvals = self.get_approvals()
                    with open(filepath, 'w') as f:
                        json.dump(approvals, f, indent=2)
                exported_files['approvals'] = str(filepath)
            
            return exported_files
        
        except Exception as e:
            print(f"Error exporting data: {e}")
            return {}
    
    def import_servers(self, import_file: str, merge: bool = False) -> bool:
        """Import servers from CSV file"""
        try:
            new_servers = []
            
            with open(import_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalize field names
                    normalized_row = self.normalize_field_names(row)
                    
                    # Add timestamp fields if not present
                    if 'created_date' not in normalized_row:
                        normalized_row['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if 'modified_date' not in normalized_row:
                        normalized_row['modified_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if 'active_status' not in normalized_row:
                        normalized_row['active_status'] = 'Active'
                    
                    new_servers.append(normalized_row)
            
            if merge:
                # Merge with existing servers
                existing_servers = self.read_servers()
                existing_names = {s.get('server_name') for s in existing_servers}
                
                # Add only new servers
                for server in new_servers:
                    if server.get('server_name') not in existing_names:
                        existing_servers.append(server)
                
                return self.write_servers(existing_servers)
            else:
                # Replace all servers
                return self.write_servers(new_servers)
        
        except Exception as e:
            print(f"Error importing servers: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = {
            'servers': {},
            'patches': {},
            'approvals': {},
            'prechecks': {},
            'rollbacks': {}
        }
        
        # Server statistics
        servers = self.read_servers()
        stats['servers'] = {
            'total': len(servers),
            'active': len([s for s in servers if s.get('active_status') == 'Active']),
            'by_group': {},
            'by_os': {},
            'by_environment': {}
        }
        
        # Group servers by various attributes
        for server in servers:
            group = server.get('host_group', 'Unknown')
            os = server.get('operating_system', 'Unknown')
            env = server.get('environment', 'Unknown')
            
            stats['servers']['by_group'][group] = stats['servers']['by_group'].get(group, 0) + 1
            stats['servers']['by_os'][os] = stats['servers']['by_os'].get(os, 0) + 1
            stats['servers']['by_environment'][env] = stats['servers']['by_environment'].get(env, 0) + 1
        
        # Patch statistics
        patch_history = self.get_patch_history()
        stats['patches'] = {
            'total': len(patch_history),
            'successful': len([p for p in patch_history if p.get('Status') == 'Success']),
            'failed': len([p for p in patch_history if p.get('Status') == 'Failed']),
            'by_quarter': {}
        }
        
        for patch in patch_history:
            quarter = patch.get('Quarter', 'Unknown')
            stats['patches']['by_quarter'][quarter] = stats['patches']['by_quarter'].get(quarter, 0) + 1
        
        # Calculate success rate
        if stats['patches']['total'] > 0:
            stats['patches']['success_rate'] = (stats['patches']['successful'] / stats['patches']['total']) * 100
        else:
            stats['patches']['success_rate'] = 0
        
        # Approval statistics
        approvals = self.get_approvals()
        stats['approvals'] = {
            'total': len(approvals),
            'pending': len([a for a in approvals if a.get('Status') == 'Pending']),
            'approved': len([a for a in approvals if a.get('Status') == 'Approved']),
            'rejected': len([a for a in approvals if a.get('Status') == 'Rejected'])
        }
        
        # Precheck statistics
        prechecks = self.get_precheck_results()
        stats['prechecks'] = {
            'total': len(prechecks),
            'passed': len([p for p in prechecks if p.get('Status') == 'Passed']),
            'failed': len([p for p in prechecks if p.get('Status') == 'Failed']),
            'warnings': len([p for p in prechecks if p.get('Status') == 'Warning'])
        }
        
        # Rollback statistics
        rollbacks = self.get_rollback_history()
        stats['rollbacks'] = {
            'total': len(rollbacks),
            'successful': len([r for r in rollbacks if r.get('Rollback Status') == 'Success']),
            'failed': len([r for r in rollbacks if r.get('Rollback Status') == 'Failed'])
        }
        
        return stats
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old data files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_counts = {
            'patch_history': 0,
            'precheck_results': 0,
            'rollback_history': 0
        }
        
        # Clean patch history
        history = self.get_patch_history()
        new_history = []
        for record in history:
            try:
                record_date = datetime.strptime(record.get('Timestamp', ''), '%Y-%m-%d %H:%M:%S')
                if record_date >= cutoff_date:
                    new_history.append(record)
                else:
                    cleaned_counts['patch_history'] += 1
            except ValueError:
                new_history.append(record)  # Keep records with invalid dates
        
        # Write cleaned history back
        if cleaned_counts['patch_history'] > 0:
            with open(self.patch_history_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self._get_patch_history_headers())
                writer.writeheader()
                writer.writerows(new_history)
        
        # Similar cleanup for other files can be added here
        
        return cleaned_counts