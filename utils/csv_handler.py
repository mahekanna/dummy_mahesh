# utils/csv_handler.py
import csv
import os
from typing import List, Dict
from config.settings import Config

class CSVHandler:
    def __init__(self, csv_file_path=None):
        self.csv_file_path = csv_file_path or Config.CSV_FILE_PATH
    
    def read_servers(self) -> List[Dict]:
        """Read servers from CSV file"""
        servers = []
        
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")
        
        with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Strip whitespace from all values
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                servers.append(cleaned_row)
        
        return servers
    
    def write_servers(self, servers: List[Dict]) -> None:
        """Write servers to CSV file"""
        if not servers:
            return
        
        fieldnames = servers[0].keys()
        
        with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(servers)
    
    def update_server_status(self, server_name: str, quarter: str, status: str) -> bool:
        """Update server patching status"""
        servers = self.read_servers()
        updated = False
        
        for server in servers:
            if server['Server Name'] == server_name:
                server['Current Quarter Patching Status'] = status
                updated = True
                break
        
        if updated:
            self.write_servers(servers)
            return True
        
        return False
    
    def get_servers_by_owner(self, owner_email: str) -> List[Dict]:
        """Get all servers for a specific owner"""
        servers = self.read_servers()
        owner_servers = []
        
        for server in servers:
            if (server.get('primary_owner') == owner_email or 
                server.get('secondary_owner') == owner_email):
                owner_servers.append(server)
        
        return owner_servers
