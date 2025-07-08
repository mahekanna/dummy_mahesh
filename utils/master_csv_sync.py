# utils/master_csv_sync.py
import os
import shutil
import csv
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from utils.logger import Logger
from utils.phonedb_converter import PhonedbConverter
from utils.csv_handler import CSVHandler
from config.settings import Config

class MasterCSVSync:
    """
    Sync master CSV file to local database with username conversion
    """
    
    def __init__(self, master_csv_path: Optional[str] = None):
        self.logger = Logger('master_csv_sync')
        self.phonedb_converter = PhonedbConverter()
        self.csv_handler = CSVHandler()
        
        # Master CSV path configuration
        self.master_csv_path = master_csv_path or os.getenv('MASTER_CSV_PATH', '/master/servers.csv')
        self.local_csv_path = Config.CSV_FILE_PATH
        self.backup_dir = os.path.join(Config.BACKUP_DIR, 'csv_backups')
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Required fields for the new schema
        self.required_fields = [
            'Server Name', 'Server Timezone', 'primary_owner', 'secondary_owner',
            'host_group', 'location', 'Operating System', 'Environment'
        ]
        
        # New fields to be added
        self.new_fields = [
            'primary_linux_user', 'secondary_linux_user', 
            'last_sync_date', 'sync_status'
        ]
    
    def check_master_csv_changes(self) -> bool:
        """
        Check if master CSV has changes compared to local copy
        """
        try:
            if not os.path.exists(self.master_csv_path):
                self.logger.error(f"Master CSV not found: {self.master_csv_path}")
                return False
            
            if not os.path.exists(self.local_csv_path):
                self.logger.info("Local CSV doesn't exist, sync needed")
                return True
            
            # Compare file modification times
            master_mtime = os.path.getmtime(self.master_csv_path)
            local_mtime = os.path.getmtime(self.local_csv_path)
            
            if master_mtime > local_mtime:
                self.logger.info("Master CSV is newer than local copy")
                return True
            
            # Compare file hashes for more accurate detection
            master_hash = self._get_file_hash(self.master_csv_path)
            local_hash = self._get_file_hash(self.local_csv_path)
            
            if master_hash != local_hash:
                self.logger.info("Master CSV content differs from local copy")
                return True
            
            self.logger.info("No changes detected in master CSV")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking master CSV changes: {e}")
            return False
    
    def sync_master_to_local(self, force: bool = False) -> bool:
        """
        Sync master CSV to local with username conversion
        """
        try:
            # Check if sync is needed
            if not force and not self.check_master_csv_changes():
                self.logger.info("No sync needed")
                return True
            
            self.logger.info(f"Starting master CSV sync from {self.master_csv_path}")
            
            # Backup current local CSV
            if os.path.exists(self.local_csv_path):
                backup_path = self._backup_local_csv()
                self.logger.info(f"Created backup: {backup_path}")
            
            # Read master CSV
            master_data = self._read_master_csv()
            if not master_data:
                self.logger.error("Failed to read master CSV")
                return False
            
            # Convert email addresses to usernames
            converted_data = self._convert_emails_to_usernames(master_data)
            
            # Validate converted data
            if not self._validate_converted_data(converted_data):
                self.logger.error("Data validation failed")
                return False
            
            # Write to local CSV with new schema
            success = self._write_converted_csv(converted_data)
            
            if success:
                self.logger.info(f"Successfully synced {len(converted_data)} servers")
                return True
            else:
                self.logger.error("Failed to write converted CSV")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during master CSV sync: {e}")
            return False
    
    def _read_master_csv(self) -> List[Dict]:
        """
        Read and validate master CSV file
        """
        try:
            servers = []
            
            with open(self.master_csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate required fields
                missing_fields = [field for field in self.required_fields if field not in reader.fieldnames]
                if missing_fields:
                    self.logger.error(f"Missing required fields in master CSV: {missing_fields}")
                    return []
                
                for row_num, row in enumerate(reader, start=2):
                    # Clean and validate row
                    cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                    
                    # Validate required fields
                    if not cleaned_row.get('Server Name'):
                        self.logger.warning(f"Row {row_num}: Missing Server Name, skipping")
                        continue
                    
                    if not cleaned_row.get('primary_owner'):
                        self.logger.warning(f"Row {row_num}: Missing primary_owner for {cleaned_row['Server Name']}")
                    
                    servers.append(cleaned_row)
            
            self.logger.info(f"Read {len(servers)} servers from master CSV")
            return servers
            
        except Exception as e:
            self.logger.error(f"Error reading master CSV: {e}")
            return []
    
    def _convert_emails_to_usernames(self, servers: List[Dict]) -> List[Dict]:
        """
        Convert email addresses to Linux usernames using phonedb
        """
        self.logger.info("Converting email addresses to usernames...")
        
        # Test phonedb availability
        if not self.phonedb_converter.test_phonedb_availability():
            self.logger.warning("Phonedb not available, skipping username conversion")
            # Add empty username fields
            for server in servers:
                server['primary_linux_user'] = ''
                server['secondary_linux_user'] = ''
                server['sync_status'] = 'phonedb_unavailable'
            return servers
        
        # Collect all unique email addresses
        all_emails = set()
        for server in servers:
            if server.get('primary_owner'):
                all_emails.add(server['primary_owner'])
            if server.get('secondary_owner'):
                all_emails.add(server['secondary_owner'])
        
        # Bulk convert emails to usernames
        self.logger.info(f"Converting {len(all_emails)} unique email addresses")
        email_to_username = self.phonedb_converter.bulk_convert_emails(list(all_emails))
        
        # Apply conversions to servers
        converted_count = 0
        failed_count = 0
        
        for server in servers:
            # Convert primary owner
            primary_email = server.get('primary_owner', '')
            if primary_email:
                primary_username = email_to_username.get(primary_email)
                server['primary_linux_user'] = primary_username or ''
                if primary_username:
                    converted_count += 1
                else:
                    failed_count += 1
                    self.logger.warning(f"Failed to convert primary owner: {primary_email}")
            else:
                server['primary_linux_user'] = ''
            
            # Convert secondary owner
            secondary_email = server.get('secondary_owner', '')
            if secondary_email:
                secondary_username = email_to_username.get(secondary_email)
                server['secondary_linux_user'] = secondary_username or ''
                if secondary_username:
                    converted_count += 1
                elif secondary_email != primary_email:  # Don't double-count same email
                    failed_count += 1
                    self.logger.warning(f"Failed to convert secondary owner: {secondary_email}")
            else:
                server['secondary_linux_user'] = ''
            
            # Set sync metadata
            server['last_sync_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            server['sync_status'] = 'success' if (server['primary_linux_user'] or not primary_email) else 'conversion_failed'
        
        self.logger.info(f"Conversion complete: {converted_count} successful, {failed_count} failed")
        return servers
    
    def _validate_converted_data(self, servers: List[Dict]) -> bool:
        """
        Validate converted server data
        """
        try:
            if not servers:
                self.logger.error("No servers to validate")
                return False
            
            # Check for duplicate server names
            server_names = [s.get('Server Name', '') for s in servers]
            duplicates = [name for name in set(server_names) if server_names.count(name) > 1 and name]
            
            if duplicates:
                self.logger.error(f"Duplicate server names found: {duplicates}")
                return False
            
            # Validate critical fields
            validation_errors = 0
            for i, server in enumerate(servers):
                server_name = server.get('Server Name', f'Row {i+1}')
                
                # Check required fields
                if not server.get('Server Name'):
                    self.logger.error(f"Server {i+1}: Missing Server Name")
                    validation_errors += 1
                
                if not server.get('host_group'):
                    self.logger.warning(f"Server {server_name}: Missing host_group")
                
                # Validate timezone
                if not server.get('Server Timezone'):
                    self.logger.warning(f"Server {server_name}: Missing Server Timezone")
            
            if validation_errors > 0:
                self.logger.error(f"Validation failed with {validation_errors} errors")
                return False
            
            self.logger.info(f"Validation successful for {len(servers)} servers")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating converted data: {e}")
            return False
    
    def _write_converted_csv(self, servers: List[Dict]) -> bool:
        """
        Write converted server data to local CSV
        """
        try:
            if not servers:
                self.logger.error("No servers to write")
                return False
            
            # Ensure all required fields are present
            fieldnames = list(servers[0].keys())
            
            # Add any missing new fields
            for field in self.new_fields:
                if field not in fieldnames:
                    fieldnames.append(field)
                    for server in servers:
                        if field not in server:
                            server[field] = ''
            
            # Write to local CSV
            with open(self.local_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(servers)
            
            self.logger.info(f"Successfully wrote {len(servers)} servers to {self.local_csv_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing converted CSV: {e}")
            return False
    
    def _backup_local_csv(self) -> str:
        """
        Create backup of current local CSV
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"servers_backup_{timestamp}.csv"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        shutil.copy2(self.local_csv_path, backup_path)
        return backup_path
    
    def _get_file_hash(self, filepath: str) -> str:
        """
        Calculate MD5 hash of file content
        """
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_sync_status(self) -> Dict:
        """
        Get current sync status and statistics
        """
        try:
            status = {
                'master_csv_exists': os.path.exists(self.master_csv_path),
                'local_csv_exists': os.path.exists(self.local_csv_path),
                'master_csv_path': self.master_csv_path,
                'local_csv_path': self.local_csv_path,
                'phonedb_available': self.phonedb_converter.test_phonedb_availability(),
                'cache_stats': self.phonedb_converter.get_cache_stats()
            }
            
            if status['master_csv_exists']:
                status['master_csv_mtime'] = datetime.fromtimestamp(
                    os.path.getmtime(self.master_csv_path)
                ).strftime('%Y-%m-%d %H:%M:%S')
                status['master_csv_size'] = os.path.getsize(self.master_csv_path)
            
            if status['local_csv_exists']:
                status['local_csv_mtime'] = datetime.fromtimestamp(
                    os.path.getmtime(self.local_csv_path)
                ).strftime('%Y-%m-%d %H:%M:%S')
                status['local_csv_size'] = os.path.getsize(self.local_csv_path)
                
                # Get server count and conversion statistics
                servers = self.csv_handler.read_servers()
                status['server_count'] = len(servers)
                status['servers_with_linux_users'] = len([
                    s for s in servers 
                    if s.get('primary_linux_user') or s.get('secondary_linux_user')
                ])
            
            status['sync_needed'] = self.check_master_csv_changes()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting sync status: {e}")
            return {'error': str(e)}
    
    def force_username_conversion(self) -> bool:
        """
        Force re-conversion of all email addresses to usernames
        """
        try:
            self.logger.info("Starting forced username conversion")
            
            # Clear phonedb cache
            self.phonedb_converter.clear_cache()
            
            # Read current local CSV
            if not os.path.exists(self.local_csv_path):
                self.logger.error("Local CSV not found")
                return False
            
            servers = self.csv_handler.read_servers()
            if not servers:
                self.logger.error("No servers found in local CSV")
                return False
            
            # Backup current CSV
            backup_path = self._backup_local_csv()
            self.logger.info(f"Created backup: {backup_path}")
            
            # Convert emails to usernames
            converted_servers = self._convert_emails_to_usernames(servers)
            
            # Write back to CSV
            success = self._write_converted_csv(converted_servers)
            
            if success:
                self.logger.info("Forced username conversion completed successfully")
            else:
                self.logger.error("Forced username conversion failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in forced username conversion: {e}")
            return False