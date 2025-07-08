# utils/database_sync.py
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from utils.logger import Logger
from utils.csv_handler import CSVHandler
from database.models import DatabaseManager
from config.settings import Config

class DatabaseSync:
    """
    Synchronize CSV data with database, including new linux_user fields
    """
    
    def __init__(self):
        self.logger = Logger('database_sync')
        self.csv_handler = CSVHandler()
        self.db_manager = DatabaseManager()
        
    def sync_csv_to_database(self, force: bool = False) -> bool:
        """
        Sync CSV data to database with linux_user fields
        """
        try:
            self.logger.info("Starting CSV to database sync")
            
            # Connect to database
            self.db_manager.connect()
            
            # Update database schema if needed
            if not self._check_and_update_schema():
                self.logger.error("Failed to update database schema")
                return False
            
            # Read servers from CSV
            servers = self.csv_handler.read_servers()
            if not servers:
                self.logger.error("No servers found in CSV")
                return False
            
            # Sync each server
            success_count = 0
            error_count = 0
            
            for server in servers:
                try:
                    if self._sync_server_to_database(server):
                        success_count += 1
                    else:
                        error_count += 1
                        self.logger.error(f"Failed to sync server: {server.get('Server Name', 'Unknown')}")
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Error syncing server {server.get('Server Name', 'Unknown')}: {e}")
            
            self.logger.info(f"Database sync completed: {success_count} success, {error_count} errors")
            return error_count == 0
            
        except Exception as e:
            self.logger.error(f"Error during database sync: {e}")
            return False
        finally:
            self.db_manager.close()
    
    def _check_and_update_schema(self) -> bool:
        """
        Check if database schema needs updating and add new fields
        """
        try:
            cursor = self.db_manager.connection.cursor()
            
            # Check if linux_user fields exist
            if self.db_manager.use_sqlite:
                cursor.execute("PRAGMA table_info(servers)")
                columns = [row[1] for row in cursor.fetchall()]
            else:
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'servers'
                """)
                columns = [row[0] for row in cursor.fetchall()]
            
            # List of new fields to add
            new_fields = [
                ('primary_linux_user', 'VARCHAR(100)'),
                ('secondary_linux_user', 'VARCHAR(100)'),
                ('last_sync_date', 'TIMESTAMP'),
                ('sync_status', 'VARCHAR(50)'),
                ('operating_system', 'VARCHAR(100)'),
                ('environment', 'VARCHAR(50)'),
                ('incident_ticket', 'VARCHAR(100)'),
                ('patcher_email', 'VARCHAR(255)'),
                ('q1_approval_status', 'VARCHAR(50) DEFAULT "Pending"'),
                ('q2_approval_status', 'VARCHAR(50) DEFAULT "Pending"'),
                ('q3_approval_status', 'VARCHAR(50) DEFAULT "Pending"'),
                ('q4_approval_status', 'VARCHAR(50) DEFAULT "Pending"')
            ]
            
            # Add missing fields
            for field_name, field_type in new_fields:
                if field_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE servers ADD COLUMN {field_name} {field_type}")
                        self.logger.info(f"Added column: {field_name}")
                    except Exception as e:
                        self.logger.warning(f"Could not add column {field_name}: {e}")
            
            self.db_manager.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating database schema: {e}")
            return False
    
    def _sync_server_to_database(self, server_data: Dict) -> bool:
        """
        Sync individual server data to database
        """
        try:
            cursor = self.db_manager.connection.cursor()
            
            server_name = server_data.get('Server Name', '').strip()
            if not server_name:
                return False
            
            # Prepare data for database insertion
            sync_data = {
                'server_name': server_name,
                'server_timezone': server_data.get('Server Timezone', ''),
                'primary_owner': server_data.get('primary_owner', ''),
                'secondary_owner': server_data.get('secondary_owner', ''),
                'primary_linux_user': server_data.get('primary_linux_user', ''),
                'secondary_linux_user': server_data.get('secondary_linux_user', ''),
                'host_group': server_data.get('host_group', ''),
                'engr_domain': server_data.get('engr_domain', ''),
                'location': server_data.get('location', ''),
                'operating_system': server_data.get('Operating System', ''),
                'environment': server_data.get('Environment', ''),
                'incident_ticket': server_data.get('incident_ticket', ''),
                'patcher_email': server_data.get('patcher_email', ''),
                'q1_patch_date': server_data.get('Q1 Patch Date', ''),
                'q1_patch_time': server_data.get('Q1 Patch Time', ''),
                'q1_approval_status': server_data.get('Q1 Approval Status', 'Pending'),
                'q2_patch_date': server_data.get('Q2 Patch Date', ''),
                'q2_patch_time': server_data.get('Q2 Patch Time', ''),
                'q2_approval_status': server_data.get('Q2 Approval Status', 'Pending'),
                'q3_patch_date': server_data.get('Q3 Patch Date', ''),
                'q3_patch_time': server_data.get('Q3 Patch Time', ''),
                'q3_approval_status': server_data.get('Q3 Approval Status', 'Pending'),
                'q4_patch_date': server_data.get('Q4 Patch Date', ''),
                'q4_patch_time': server_data.get('Q4 Patch Time', ''),
                'q4_approval_status': server_data.get('Q4 Approval Status', 'Pending'),
                'current_quarter_status': server_data.get('Current Quarter Patching Status', 'Pending'),
                'last_sync_date': server_data.get('last_sync_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'sync_status': server_data.get('sync_status', 'synced')
            }
            
            # Check if server exists
            cursor.execute("SELECT id FROM servers WHERE server_name = ?", (server_name,))
            existing_server = cursor.fetchone()
            
            if existing_server:
                # Update existing server
                update_fields = []
                values = []
                
                for field, value in sync_data.items():
                    if field != 'server_name':  # Don't update the primary key
                        update_fields.append(f"{field} = ?")
                        values.append(value)
                
                values.append(server_name)  # For WHERE clause
                
                update_sql = f"UPDATE servers SET {', '.join(update_fields)} WHERE server_name = ?"
                cursor.execute(update_sql, values)
                
                self.logger.debug(f"Updated server: {server_name}")
                
            else:
                # Insert new server
                fields = list(sync_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                values = list(sync_data.values())
                
                insert_sql = f"INSERT INTO servers ({', '.join(fields)}) VALUES ({placeholders})"
                cursor.execute(insert_sql, values)
                
                self.logger.debug(f"Inserted server: {server_name}")
            
            self.db_manager.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error syncing server {server_name}: {e}")
            return False
    
    def sync_database_to_csv(self, output_path: Optional[str] = None) -> bool:
        """
        Sync database data back to CSV (for backup or export)
        """
        try:
            self.logger.info("Starting database to CSV sync")
            
            # Connect to database
            self.db_manager.connect()
            
            # Query all servers
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT * FROM servers ORDER BY server_name")
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            servers = []
            
            # Convert database rows to CSV format
            for row in cursor.fetchall():
                server_dict = dict(zip(columns, row))
                
                # Convert database fields back to CSV format
                csv_server = {
                    'Server Name': server_dict.get('server_name', ''),
                    'Server Timezone': server_dict.get('server_timezone', ''),
                    'Q1 Patch Date': server_dict.get('q1_patch_date', ''),
                    'Q1 Patch Time': server_dict.get('q1_patch_time', ''),
                    'Q2 Patch Date': server_dict.get('q2_patch_date', ''),
                    'Q2 Patch Time': server_dict.get('q2_patch_time', ''),
                    'Q3 Patch Date': server_dict.get('q3_patch_date', ''),
                    'Q3 Patch Time': server_dict.get('q3_patch_time', ''),
                    'Q4 Patch Date': server_dict.get('q4_patch_date', ''),
                    'Q4 Patch Time': server_dict.get('q4_patch_time', ''),
                    'Current Quarter Patching Status': server_dict.get('current_quarter_status', ''),
                    'primary_owner': server_dict.get('primary_owner', ''),
                    'secondary_owner': server_dict.get('secondary_owner', ''),
                    'primary_linux_user': server_dict.get('primary_linux_user', ''),
                    'secondary_linux_user': server_dict.get('secondary_linux_user', ''),
                    'host_group': server_dict.get('host_group', ''),
                    'engr_domain': server_dict.get('engr_domain', ''),
                    'location': server_dict.get('location', ''),
                    'incident_ticket': server_dict.get('incident_ticket', ''),
                    'patcher_email': server_dict.get('patcher_email', ''),
                    'last_sync_date': server_dict.get('last_sync_date', ''),
                    'sync_status': server_dict.get('sync_status', ''),
                    'Operating System': server_dict.get('operating_system', ''),
                    'Environment': server_dict.get('environment', ''),
                    'Q1 Approval Status': server_dict.get('q1_approval_status', 'Pending'),
                    'Q2 Approval Status': server_dict.get('q2_approval_status', 'Pending'),
                    'Q3 Approval Status': server_dict.get('q3_approval_status', 'Pending'),
                    'Q4 Approval Status': server_dict.get('q4_approval_status', 'Pending')
                }
                
                servers.append(csv_server)
            
            # Write to CSV
            output_file = output_path or Config.CSV_FILE_PATH
            success = self.csv_handler.write_servers(servers, output_file)
            
            if success:
                self.logger.info(f"Successfully exported {len(servers)} servers to {output_file}")
            else:
                self.logger.error("Failed to write CSV file")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during database to CSV sync: {e}")
            return False
        finally:
            self.db_manager.close()
    
    def get_sync_status(self) -> Dict:
        """
        Get current sync status and statistics
        """
        try:
            status = {
                'csv_exists': os.path.exists(Config.CSV_FILE_PATH),
                'database_exists': False,
                'csv_server_count': 0,
                'db_server_count': 0,
                'last_sync_date': None,
                'sync_errors': []
            }
            
            # Check CSV status
            if status['csv_exists']:
                servers = self.csv_handler.read_servers()
                status['csv_server_count'] = len(servers)
                
                # Get last sync date from CSV
                sync_dates = [s.get('last_sync_date', '') for s in servers if s.get('last_sync_date')]
                if sync_dates:
                    status['last_sync_date'] = max(sync_dates)
            
            # Check database status
            try:
                self.db_manager.connect()
                cursor = self.db_manager.connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM servers")
                status['db_server_count'] = cursor.fetchone()[0]
                status['database_exists'] = True
                
                # Check for servers with sync errors
                cursor.execute("SELECT server_name, sync_status FROM servers WHERE sync_status != 'synced'")
                error_servers = cursor.fetchall()
                status['sync_errors'] = [{'server': row[0], 'status': row[1]} for row in error_servers]
                
            except Exception as e:
                status['database_error'] = str(e)
            finally:
                self.db_manager.close()
            
            return status
            
        except Exception as e:
            return {'error': str(e)}
    
    def validate_sync_integrity(self) -> Tuple[bool, List[str]]:
        """
        Validate sync integrity between CSV and database
        """
        try:
            issues = []
            
            # Read CSV servers
            csv_servers = self.csv_handler.read_servers()
            csv_server_names = set(s.get('Server Name', '') for s in csv_servers)
            
            # Read database servers
            self.db_manager.connect()
            cursor = self.db_manager.connection.cursor()
            cursor.execute("SELECT server_name FROM servers")
            db_server_names = set(row[0] for row in cursor.fetchall())
            
            # Check for missing servers
            missing_in_db = csv_server_names - db_server_names
            if missing_in_db:
                issues.append(f"Servers in CSV but not in database: {', '.join(missing_in_db)}")
            
            missing_in_csv = db_server_names - csv_server_names
            if missing_in_csv:
                issues.append(f"Servers in database but not in CSV: {', '.join(missing_in_csv)}")
            
            # Check for servers without linux_user mappings
            servers_without_linux_users = []
            for server in csv_servers:
                if (server.get('primary_owner') and not server.get('primary_linux_user')):
                    servers_without_linux_users.append(server.get('Server Name', ''))
            
            if servers_without_linux_users:
                issues.append(f"Servers without linux_user mappings: {', '.join(servers_without_linux_users)}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
        finally:
            self.db_manager.close()
    
    def repair_sync_issues(self) -> bool:
        """
        Attempt to repair common sync issues
        """
        try:
            self.logger.info("Starting sync repair")
            
            # Force a full sync to repair inconsistencies
            success = self.sync_csv_to_database(force=True)
            
            if success:
                self.logger.info("Sync repair completed successfully")
            else:
                self.logger.error("Sync repair failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during sync repair: {e}")
            return False