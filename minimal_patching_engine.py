#!/usr/bin/env python3
"""
Minimal Patching Engine Example
This shows the core patching logic without all the dependencies
"""

import subprocess
import csv
import json
from datetime import datetime
import os
import sys

class MinimalPatchingEngine:
    def __init__(self, servers_file='servers.csv', log_file='patching.log'):
        self.servers_file = servers_file
        self.log_file = log_file
        
    def log(self, message):
        """Simple logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def read_servers(self):
        """Read server list from CSV"""
        servers = []
        try:
            with open(self.servers_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    servers.append(row)
        except FileNotFoundError:
            self.log(f"ERROR: {self.servers_file} not found")
        return servers
    
    def run_ssh_command(self, server, command, timeout=300):
        """Execute command on remote server via SSH"""
        ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', 
                   '-o', 'ConnectTimeout=30', server, command]
        
        try:
            result = subprocess.run(ssh_cmd, capture_output=True, 
                                  text=True, timeout=timeout)
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def precheck_server(self, server_name):
        """Run pre-patching checks"""
        self.log(f"Running pre-checks on {server_name}")
        
        checks = {
            'connectivity': False,
            'disk_space': False,
            'load_average': False,
            'critical_services': False
        }
        
        # Check connectivity
        result = self.run_ssh_command(server_name, 'echo "connected"', timeout=30)
        checks['connectivity'] = result['success']
        
        if not checks['connectivity']:
            self.log(f"ERROR: Cannot connect to {server_name}")
            return False, checks
        
        # Check disk space (need at least 20% free on /)
        result = self.run_ssh_command(server_name, 
            "df -h / | awk 'NR==2 {print 100-$5}'")
        if result['success']:
            try:
                free_percent = int(result['stdout'].strip().replace('%', ''))
                checks['disk_space'] = free_percent >= 20
            except:
                checks['disk_space'] = False
        
        # Check load average
        result = self.run_ssh_command(server_name, 
            "uptime | awk -F'load average:' '{print $2}' | awk -F, '{print $1}'")
        if result['success']:
            try:
                load = float(result['stdout'].strip())
                checks['load_average'] = load < 10.0
            except:
                checks['load_average'] = False
        
        # Check critical services (example: ssh, cron)
        services_ok = True
        for service in ['ssh', 'cron']:
            result = self.run_ssh_command(server_name, 
                f"systemctl is-active {service} || service {service} status | grep -q running")
            if not result['success']:
                services_ok = False
                break
        checks['critical_services'] = services_ok
        
        # All checks must pass
        all_passed = all(checks.values())
        return all_passed, checks
    
    def patch_server(self, server_name, os_type='ubuntu'):
        """Execute patching on a server"""
        self.log(f"Starting patch process for {server_name} ({os_type})")
        
        # Run pre-checks
        passed, check_results = self.precheck_server(server_name)
        if not passed:
            self.log(f"Pre-checks failed for {server_name}: {check_results}")
            return False, "Pre-check validation failed"
        
        # Update package list
        if os_type.lower() in ['ubuntu', 'debian']:
            update_cmd = 'sudo apt-get update'
            upgrade_cmd = 'sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y'
        elif os_type.lower() in ['rhel', 'centos', 'redhat']:
            update_cmd = 'sudo yum check-update || true'
            upgrade_cmd = 'sudo yum update -y'
        else:
            return False, f"Unsupported OS type: {os_type}"
        
        # Run update
        self.log(f"Updating package list on {server_name}")
        result = self.run_ssh_command(server_name, update_cmd, timeout=600)
        if not result['success'] and result['returncode'] != 100:  # yum returns 100 if updates available
            self.log(f"Package update failed on {server_name}: {result['stderr']}")
            return False, "Package list update failed"
        
        # Run upgrade
        self.log(f"Installing updates on {server_name}")
        result = self.run_ssh_command(server_name, upgrade_cmd, timeout=3600)
        if not result['success']:
            self.log(f"Package upgrade failed on {server_name}: {result['stderr']}")
            return False, "Package upgrade failed"
        
        # Check if reboot required
        if os_type.lower() in ['ubuntu', 'debian']:
            reboot_check = '[ -f /var/run/reboot-required ] && echo "yes" || echo "no"'
        else:
            reboot_check = 'needs-restarting -r > /dev/null 2>&1 && echo "no" || echo "yes"'
        
        result = self.run_ssh_command(server_name, reboot_check)
        needs_reboot = result['success'] and result['stdout'].strip() == 'yes'
        
        if needs_reboot:
            self.log(f"Reboot required for {server_name}")
            # In production, you might schedule a reboot or handle it differently
        
        self.log(f"Patching completed successfully for {server_name}")
        return True, "Patching completed successfully"
    
    def patch_by_quarter(self, quarter):
        """Patch all servers scheduled for a specific quarter"""
        servers = self.read_servers()
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        results = []
        for server in servers:
            # Check if server is scheduled for this quarter
            patch_date_key = f'{quarter} Patch Date'
            if patch_date_key not in server:
                continue
                
            scheduled_date = server[patch_date_key]
            if not scheduled_date or scheduled_date > current_date:
                continue
            
            server_name = server.get('Server Name', '')
            os_type = server.get('Operating System', 'ubuntu')
            
            self.log(f"Processing {server_name} for {quarter}")
            success, message = self.patch_server(server_name, os_type)
            
            results.append({
                'server': server_name,
                'success': success,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    def generate_report(self, results):
        """Generate a simple report"""
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total - successful
        
        report = f"""
Patching Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================

Summary:
- Total Servers: {total}
- Successful: {successful}
- Failed: {failed}
- Success Rate: {(successful/total*100) if total > 0 else 0:.1f}%

Details:
"""
        for result in results:
            status = "SUCCESS" if result['success'] else "FAILED"
            report += f"\n{result['server']}: {status} - {result['message']}"
        
        return report

# Example usage
if __name__ == "__main__":
    # Create sample servers.csv if it doesn't exist
    if not os.path.exists('servers.csv'):
        with open('servers.csv', 'w') as f:
            f.write('Server Name,Operating System,Q1 Patch Date,Q2 Patch Date,Q3 Patch Date,Q4 Patch Date\n')
            f.write('web01.example.com,ubuntu,2024-01-15,2024-04-15,2024-07-15,2024-10-15\n')
            f.write('db01.example.com,rhel,2024-01-16,2024-04-16,2024-07-16,2024-10-16\n')
    
    engine = MinimalPatchingEngine()
    
    # Example: Patch a single server
    if len(sys.argv) > 1:
        server = sys.argv[1]
        success, message = engine.patch_server(server)
        print(f"Result: {message}")
    else:
        # Example: Patch all Q1 servers
        results = engine.patch_by_quarter('Q1')
        report = engine.generate_report(results)
        print(report)
        
        # Save report
        with open('patch_report.txt', 'w') as f:
            f.write(report)