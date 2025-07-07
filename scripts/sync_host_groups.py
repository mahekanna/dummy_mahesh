#!/usr/bin/env python3
"""
Sync host groups from CSV to database and server groups configuration
"""

import sys
import os
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_handler import CSVHandler
from scripts.admin_manager import AdminManager
from database.models import DatabaseManager
from utils.logger import Logger

class HostGroupSyncer:
    def __init__(self):
        self.logger = Logger('host_group_syncer')
        self.csv_handler = CSVHandler()
        self.admin_manager = AdminManager()
        self.db_manager = DatabaseManager()
        
    def get_csv_host_groups(self):
        """Get all unique host groups from CSV"""
        servers = self.csv_handler.read_servers()
        host_groups = set()
        host_group_details = defaultdict(list)
        
        for server in servers:
            host_group = server.get('host_group', '')
            if host_group:
                host_groups.add(host_group)
                host_group_details[host_group].append({
                    'server_name': server['Server Name'],
                    'location': server.get('location', ''),
                    'engr_domain': server.get('engr_domain', '')
                })
        
        return host_groups, host_group_details
    
    def update_server_groups_config(self):
        """Update server groups configuration based on current CSV data"""
        self.logger.info("Updating server groups configuration from CSV data")
        
        host_groups, host_group_details = self.get_csv_host_groups()
        
        # Load existing configuration
        existing_config = self.admin_manager.load_server_groups_config()
        if not existing_config:
            existing_config = {"server_groups": {}, "load_balancing": {}}
        
        # Preserve load balancing settings
        if "load_balancing" not in existing_config:
            existing_config["load_balancing"] = {
                "max_servers_per_hour": 5,
                "min_gap_between_critical": 60,
                "preferred_start_time": "20:00",
                "max_duration_hours": 6
            }
        
        # Update server groups based on CSV data
        updated_groups = {}
        
        for host_group in host_groups:
            servers_in_group = host_group_details[host_group]
            server_count = len(servers_in_group)
            
            # Check if group already exists in configuration
            if host_group in existing_config.get("server_groups", {}):
                # Preserve existing configuration but update server count
                existing_group = existing_config["server_groups"][host_group]
                existing_group["server_count"] = server_count
                existing_group["description"] = f"{existing_group.get('name', host_group)} ({server_count} servers) - Synced from CSV"
                updated_groups[host_group] = existing_group
            else:
                # Create new group configuration
                updated_groups[host_group] = self._create_default_group_config(host_group, server_count)
            
            self.logger.info(f"Updated group '{host_group}' with {server_count} servers")
        
        # Remove groups that no longer exist in CSV
        removed_groups = []
        for existing_group in existing_config.get("server_groups", {}):
            if existing_group not in host_groups:
                removed_groups.append(existing_group)
        
        if removed_groups:
            self.logger.warning(f"Removed groups no longer in CSV: {removed_groups}")
        
        # Update configuration
        existing_config["server_groups"] = updated_groups
        
        # Save updated configuration
        if self.admin_manager.save_server_groups_config(existing_config):
            self.logger.info("Server groups configuration updated successfully")
            return True
        else:
            self.logger.error("Failed to save server groups configuration")
            return False
    
    def _create_default_group_config(self, host_group, server_count):
        """Create default configuration for a new host group"""
        # Determine priority based on group name
        priority_mapping = {
            'db_servers': 1,
            'database': 1,
            'web_servers': 2,
            'web': 2,
            'app_servers': 3,
            'application': 3,
            'dev_servers': 4,
            'development': 4,
            'test_servers': 5,
            'test': 5,
        }
        
        priority = priority_mapping.get(host_group.lower(), 3)  # Default to medium priority
        
        # Determine max concurrent based on server count and type
        if 'db' in host_group.lower() or 'database' in host_group.lower():
            max_concurrent = min(2, max(1, server_count // 3))  # Conservative for databases
        elif 'test' in host_group.lower() or 'dev' in host_group.lower():
            max_concurrent = min(8, max(2, server_count // 2))  # Liberal for test/dev
        else:
            max_concurrent = min(5, max(2, server_count // 2))  # Moderate for others
        
        # Determine scheduling window
        if 'db' in host_group.lower() or 'database' in host_group.lower():
            scheduling_window = "21:00-02:00"  # Late night for databases
        elif 'dev' in host_group.lower() or 'test' in host_group.lower():
            scheduling_window = "18:00-23:59"  # Flexible for dev/test
        else:
            scheduling_window = "20:00-23:00"  # Evening for production
        
        return {
            "name": host_group.replace('_', ' ').title(),
            "description": f"{host_group.replace('_', ' ').title()} ({server_count} servers) - Auto-generated from CSV",
            "priority": priority,
            "max_concurrent": max_concurrent,
            "scheduling_window": scheduling_window,
            "patterns": [],
            "host_groups": [host_group],
            "server_count": server_count,
            "auto_generated": True
        }
    
    def sync_to_database(self):
        """Sync all servers to database"""
        self.logger.info("Syncing CSV data to database")
        
        try:
            servers = self.csv_handler.read_servers()
            self.db_manager.connect()
            
            synced_count = 0
            for server in servers:
                if self.db_manager.upsert_server(server):
                    synced_count += 1
                else:
                    self.logger.warning(f"Failed to sync server: {server.get('Server Name', 'Unknown')}")
            
            self.logger.info(f"Synced {synced_count} servers to database")
            return synced_count
            
        except Exception as e:
            self.logger.error(f"Database sync failed: {e}")
            return 0
        finally:
            self.db_manager.close()
    
    def run_full_sync(self):
        """Run complete synchronization process"""
        self.logger.info("Starting full host group synchronization")
        
        try:
            # Update server groups configuration
            config_updated = self.update_server_groups_config()
            
            # Sync to database
            synced_count = self.sync_to_database()
            
            # Get summary
            host_groups, host_group_details = self.get_csv_host_groups()
            
            self.logger.info("Full synchronization completed")
            
            return {
                'success': True,
                'config_updated': config_updated,
                'servers_synced': synced_count,
                'host_groups_found': len(host_groups),
                'host_groups': list(host_groups)
            }
            
        except Exception as e:
            self.logger.error(f"Full sync failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    print("🔄 Host Group Synchronization")
    print("=" * 50)
    
    syncer = HostGroupSyncer()
    result = syncer.run_full_sync()
    
    if result['success']:
        print("✅ Synchronization completed successfully!")
        print(f"📊 Found {result['host_groups_found']} host groups:")
        for group in result['host_groups']:
            print(f"   - {group}")
        print(f"🔄 Configuration updated: {result['config_updated']}")
        print(f"💾 Servers synced to database: {result['servers_synced']}")
    else:
        print(f"ERROR: Synchronization failed: {result['error']}")

if __name__ == "__main__":
    main()