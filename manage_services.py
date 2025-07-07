#!/usr/bin/env python3
"""
Service management script for Linux Patching Automation System
"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.venv_python = self.base_dir / "venv" / "bin" / "python"
        self.services = {
            'web': {
                'command': [str(self.venv_python), 'web_portal/app.py'],
                'description': 'Web Dashboard',
                'port': 5001,
                'pidfile': 'web.pid'
            },
            'monitor': {
                'command': [str(self.venv_python), 'monitor.py'],
                'description': 'Patching Monitor',
                'port': None,
                'pidfile': 'monitor.pid'
            }
        }
        
    def check_venv(self):
        """Check if virtual environment exists"""
        if not self.venv_python.exists():
            print("ERROR: Virtual environment not found!")
            print("Please run: ./install.sh first")
            return False
        return True
    
    def get_service_status(self, service_name):
        """Get status of a service"""
        pidfile = self.base_dir / f"{self.services[service_name]['pidfile']}"
        
        if not pidfile.exists():
            return "stopped", None
        
        try:
            with open(pidfile, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is running
            os.kill(pid, 0)
            return "running", pid
        except (OSError, ValueError):
            # Process not running, clean up pid file
            pidfile.unlink(missing_ok=True)
            return "stopped", None
    
    def start_service(self, service_name):
        """Start a service"""
        if not self.check_venv():
            return False
            
        service = self.services[service_name]
        status, pid = self.get_service_status(service_name)
        
        if status == "running":
            print(f"RUNNING: {service['description']} is already running (PID: {pid})")
            return True
        
        try:
            print(f"STARTING: {service['description']}...")
            
            # Start the service
            process = subprocess.Popen(
                service['command'],
                cwd=self.base_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Write PID file
            pidfile = self.base_dir / service['pidfile']
            with open(pidfile, 'w') as f:
                f.write(str(process.pid))
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if it's still running
            if process.poll() is None:
                # For web services, also check if the port is responding
                if service['port']:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    try:
                        result = sock.connect_ex(('localhost', service['port']))
                        sock.close()
                        if result == 0:
                            print(f"SUCCESS: {service['description']} started successfully (PID: {process.pid})")
                            print(f"URL: http://localhost:{service['port']}")
                            return True
                        else:
                            print(f"WARNING: {service['description']} process started but port {service['port']} not ready yet")
                            print(f"STARTING: Service is starting... (PID: {process.pid})")
                            return True
                    except Exception:
                        print(f"WARNING: {service['description']} process started but port check failed")
                        print(f"✅ Service is starting... (PID: {process.pid})")
                        return True
                else:
                    print(f"SUCCESS: {service['description']} started successfully (PID: {process.pid})")
                    return True
            else:
                print(f"ERROR: {service['description']} failed to start")
                pidfile.unlink(missing_ok=True)
                return False
                
        except Exception as e:
            print(f"ERROR starting {service['description']}: {e}")
            return False
    
    def stop_service(self, service_name):
        """Stop a service"""
        service = self.services[service_name]
        status, pid = self.get_service_status(service_name)
        
        if status == "stopped":
            print(f"STOPPED: {service['description']} is already stopped")
            return True
        
        try:
            print(f"STOPPING: {service['description']} (PID: {pid})...")
            
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to stop
            for _ in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(1)
                except OSError:
                    break
            else:
                # Force kill if it doesn't stop
                print("Force killing process...")
                os.kill(pid, signal.SIGKILL)
            
            # Clean up PID file
            pidfile = self.base_dir / service['pidfile']
            pidfile.unlink(missing_ok=True)
            
            print(f"SUCCESS: {service['description']} stopped successfully")
            return True
            
        except Exception as e:
            print(f"ERROR stopping {service['description']}: {e}")
            return False
    
    def status_all(self):
        """Show status of all services"""
        print("Service Status:")
        print("=" * 50)
        
        for service_name, service_info in self.services.items():
            status, pid = self.get_service_status(service_name)
            
            if status == "running":
                status_icon = "[RUNNING]"
                status_text = f"Running (PID: {pid})"
            else:
                status_icon = "[STOPPED]"
                status_text = "Stopped"
            
            print(f"{status_icon} {service_info['description']:<20} {status_text}")
            
            if service_info['port'] and status == "running":
                print(f"   URL: http://localhost:{service_info['port']}")
        
        print()
    
    def start_all(self):
        """Start all services"""
        print("Starting all services...")
        success = True
        
        for service_name in self.services:
            if not self.start_service(service_name):
                success = False
        
        if success:
            print("\nSUCCESS: All services started successfully!")
            self.status_all()
        else:
            print("\nERROR: Some services failed to start")
        
        return success
    
    def stop_all(self):
        """Stop all services"""
        print("Stopping all services...")
        success = True
        
        for service_name in self.services:
            if not self.stop_service(service_name):
                success = False
        
        if success:
            print("\nSUCCESS: All services stopped successfully!")
        else:
            print("\nERROR: Some services failed to stop")
        
        return success

def main():
    manager = ServiceManager()
    
    if len(sys.argv) < 2:
        print("Linux Patching Automation - Service Manager")
        print("=" * 50)
        print("Usage: python manage_services.py <command> [service]")
        print()
        print("Commands:")
        print("  status                 Show status of all services")
        print("  start <service|all>    Start a service or all services")
        print("  stop <service|all>     Stop a service or all services")
        print("  restart <service|all>  Restart a service or all services")
        print()
        print("Services:")
        for name, info in manager.services.items():
            print(f"  {name:<10} {info['description']}")
        print()
        return
    
    command = sys.argv[1].lower()
    service = sys.argv[2] if len(sys.argv) > 2 else None
    
    if command == "status":
        manager.status_all()
    
    elif command == "start":
        if service == "all" or service is None:
            manager.start_all()
        elif service in manager.services:
            manager.start_service(service)
        else:
            print(f"ERROR: Unknown service: {service}")
    
    elif command == "stop":
        if service == "all" or service is None:
            manager.stop_all()
        elif service in manager.services:
            manager.stop_service(service)
        else:
            print(f"ERROR: Unknown service: {service}")
    
    elif command == "restart":
        if service == "all" or service is None:
            manager.stop_all()
            time.sleep(2)
            manager.start_all()
        elif service in manager.services:
            manager.stop_service(service)
            time.sleep(2)
            manager.start_service(service)
        else:
            print(f"ERROR: Unknown service: {service}")
    
    else:
        print(f"ERROR: Unknown command: {command}")

if __name__ == "__main__":
    main()