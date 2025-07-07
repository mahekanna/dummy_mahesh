#!/usr/bin/env python3
"""
Production Service Management Script for Linux Patching Automation System
Manages systemd services for the deployed production system
"""

import subprocess
import sys
import os
import time
import argparse

class ProductionServiceManager:
    def __init__(self):
        self.services = {
            'portal': {
                'service_name': 'patching-portal',
                'description': 'Linux Patching Web Portal',
                'port': 5001
            },
            'monitor': {
                'service_name': 'patching-monitor', 
                'description': 'Linux Patching Monitor Service',
                'port': None
            }
        }
        
    def run_command(self, command, capture_output=True):
        """Run a system command"""
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            else:
                result = subprocess.run(command, shell=True)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
    
    def get_service_status(self, service_name):
        """Get systemd service status"""
        service = self.services[service_name]['service_name']
        success, stdout, stderr = self.run_command(f"systemctl is-active {service}")
        
        if success and stdout == "active":
            return "running"
        elif stdout == "inactive":
            return "stopped"
        elif stdout == "failed":
            return "failed"
        else:
            return "unknown"
    
    def start_service(self, service_name):
        """Start a systemd service"""
        service = self.services[service_name]['service_name']
        description = self.services[service_name]['description']
        
        print(f"Starting {description}...")
        success, stdout, stderr = self.run_command(f"sudo systemctl start {service}")
        
        if success:
            # Wait a moment and check if it's actually running
            time.sleep(2)
            status = self.get_service_status(service_name)
            if status == "running":
                print(f"SUCCESS: {description} started successfully")
                return True
            else:
                print(f"ERROR: {description} failed to start properly")
                return False
        else:
            print(f"ERROR: Failed to start {description}")
            if stderr:
                print(f"Error: {stderr}")
            return False
    
    def stop_service(self, service_name):
        """Stop a systemd service"""
        service = self.services[service_name]['service_name']
        description = self.services[service_name]['description']
        
        status = self.get_service_status(service_name)
        if status == "stopped":
            print(f"STOPPED: {description} is already stopped")
            return True
            
        print(f"Stopping {description}...")
        success, stdout, stderr = self.run_command(f"sudo systemctl stop {service}")
        
        if success:
            print(f"SUCCESS: {description} stopped successfully")
            return True
        else:
            print(f"ERROR: Failed to stop {description}")
            if stderr:
                print(f"Error: {stderr}")
            return False
    
    def restart_service(self, service_name):
        """Restart a systemd service"""
        service = self.services[service_name]['service_name']
        description = self.services[service_name]['description']
        
        print(f"Restarting {description}...")
        success, stdout, stderr = self.run_command(f"sudo systemctl restart {service}")
        
        if success:
            # Wait a moment and check if it's running
            time.sleep(2)
            status = self.get_service_status(service_name)
            if status == "running":
                print(f"SUCCESS: {description} restarted successfully")
                return True
            else:
                print(f"ERROR: {description} failed to restart properly")
                return False
        else:
            print(f"ERROR: Failed to restart {description}")
            if stderr:
                print(f"Error: {stderr}")
            return False
    
    def status_all(self):
        """Show status of all services"""
        print("Production Service Status:")
        print("=" * 50)
        
        for service_name, config in self.services.items():
            description = config['description']
            status = self.get_service_status(service_name)
            
            if status == "running":
                status_text = "RUNNING"
                if config['port']:
                    status_text += f" (Port {config['port']})"
            elif status == "stopped":
                status_text = "STOPPED"
            elif status == "failed":
                status_text = "FAILED"
            else:
                status_text = "UNKNOWN"
            
            print(f"  {description:<30} {status_text}")
        
        print()
        
        # Show web portal access info if it's running
        if self.get_service_status('portal') == "running":
            success, hostname, _ = self.run_command("hostname -f")
            if success:
                print(f"Web Portal Access: http://{hostname}:5001")
            else:
                print("Web Portal Access: http://localhost:5001")
            print("Default login: admin / admin")
            print()
    
    def start_all(self):
        """Start all services"""
        print("Starting all production services...")
        print()
        
        success_count = 0
        for service_name in self.services.keys():
            if self.start_service(service_name):
                success_count += 1
            print()
        
        if success_count == len(self.services):
            print("SUCCESS: All services started successfully!")
        else:
            print("ERROR: Some services failed to start")
        
        print()
        self.status_all()
    
    def stop_all(self):
        """Stop all services"""
        print("Stopping all production services...")
        
        success_count = 0
        for service_name in self.services.keys():
            if self.stop_service(service_name):
                success_count += 1
        
        print()
        if success_count == len(self.services):
            print("SUCCESS: All services stopped successfully!")
        else:
            print("ERROR: Some services failed to stop")
    
    def restart_all(self):
        """Restart all services"""
        print("Restarting all production services...")
        print()
        
        success_count = 0
        for service_name in self.services.keys():
            if self.restart_service(service_name):
                success_count += 1
            print()
        
        if success_count == len(self.services):
            print("SUCCESS: All services restarted successfully!")
        else:
            print("ERROR: Some services failed to restart")
        
        print()
        self.status_all()
    
    def enable_services(self):
        """Enable services to start on boot"""
        print("Enabling services for automatic startup...")
        
        for service_name, config in self.services.items():
            service = config['service_name']
            description = config['description']
            
            success, stdout, stderr = self.run_command(f"sudo systemctl enable {service}")
            if success:
                print(f"SUCCESS: {description} enabled for auto-start")
            else:
                print(f"ERROR: Failed to enable {description}")
        print()
    
    def show_logs(self, service_name, lines=50):
        """Show service logs"""
        if service_name not in self.services:
            print(f"ERROR: Unknown service '{service_name}'")
            print(f"Available services: {', '.join(self.services.keys())}")
            return
        
        service = self.services[service_name]['service_name']
        description = self.services[service_name]['description']
        
        print(f"Last {lines} lines of {description} logs:")
        print("=" * 60)
        
        success, stdout, stderr = self.run_command(f"sudo journalctl -u {service} -n {lines} --no-pager")
        if success:
            print(stdout)
        else:
            print(f"ERROR: Failed to get logs for {description}")
            if stderr:
                print(f"Error: {stderr}")

def main():
    parser = argparse.ArgumentParser(description='Manage Linux Patching Automation production services')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'enable', 'logs'], 
                       help='Action to perform')
    parser.add_argument('--service', choices=['portal', 'monitor'], 
                       help='Specific service to manage (default: all)')
    parser.add_argument('--lines', type=int, default=50, 
                       help='Number of log lines to show (for logs action)')
    
    args = parser.parse_args()
    
    manager = ProductionServiceManager()
    
    if args.action == 'status':
        manager.status_all()
    
    elif args.action == 'enable':
        manager.enable_services()
    
    elif args.action == 'logs':
        if not args.service:
            print("ERROR: --service is required for logs action")
            print("Available services: portal, monitor")
            sys.exit(1)
        manager.show_logs(args.service, args.lines)
    
    elif args.service:
        # Single service action
        if args.action == 'start':
            manager.start_service(args.service)
        elif args.action == 'stop':
            manager.stop_service(args.service)
        elif args.action == 'restart':
            manager.restart_service(args.service)
    
    else:
        # All services action
        if args.action == 'start':
            manager.start_all()
        elif args.action == 'stop':
            manager.stop_all()
        elif args.action == 'restart':
            manager.restart_all()

if __name__ == "__main__":
    main()