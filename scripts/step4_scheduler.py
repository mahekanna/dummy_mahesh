# scripts/step4_scheduler.py
import subprocess
import pytz
from datetime import datetime, timedelta
from utils.csv_handler import CSVHandler
from utils.timezone_handler import TimezoneHandler
from utils.logger import Logger
from config.settings import Config

class PatchScheduler:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.timezone_handler = TimezoneHandler()
        self.logger = Logger('scheduler')
    
    def schedule_patches(self, quarter):
        """Schedule patches for servers due in the next 3 hours"""
        target_time = datetime.now() + timedelta(hours=Config.SCHEDULE_HOURS_BEFORE)
        servers = self.csv_handler.read_servers()
        
        for server in servers:
            # Only schedule patches for approved servers
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            if approval_status == 'Approved' and self.is_server_due_for_scheduling(server, target_time, quarter):
                self.logger.info(f"Scheduling patches for {server['Server Name']} (Approved)")
                self.schedule_server_patch(server, quarter)
            elif approval_status != 'Approved' and self.is_server_due_for_scheduling(server, target_time, quarter):
                self.logger.warning(f"Skipping patch scheduling for {server['Server Name']} - not approved (Status: {approval_status})")
    
    def is_server_due_for_scheduling(self, server, target_time, quarter):
        """Check if server patch should be scheduled now"""
        patch_date_str = server.get(f'Q{quarter} Patch Date')
        patch_time_str = server.get(f'Q{quarter} Patch Time')
        server_timezone = server.get('Server Timezone', 'UTC')
        
        if not patch_date_str or not patch_time_str:
            return False
        
        try:
            # Convert server time to UTC for comparison
            local_dt_str = f"{patch_date_str} {patch_time_str}"
            local_dt = datetime.strptime(local_dt_str, '%Y-%m-%d %H:%M')
            
            # Convert to UTC
            scheduled_dt_utc = self.timezone_handler.convert_timezone(
                local_dt, server_timezone, 'UTC'
            )
            
            # Check if target time is within 1 hour of the scheduling window
            time_diff = abs((scheduled_dt_utc - target_time).total_seconds())
            return time_diff <= 3600  # Within 1 hour
            
        except Exception as e:
            self.logger.error(f"Error parsing datetime for {server['Server Name']}: {e}")
            return False
    
    def schedule_server_patch(self, server, quarter):
        """Schedule patch for individual server"""
        server_name = server['Server Name']
        patch_date_str = server.get(f'Q{quarter} Patch Date')
        patch_time_str = server.get(f'Q{quarter} Patch Time')
        server_timezone = server.get('Server Timezone', 'UTC')
        
        try:
            # Calculate exact execution time
            local_dt_str = f"{patch_date_str} {patch_time_str}"
            local_dt = datetime.strptime(local_dt_str, '%Y-%m-%d %H:%M')
            
            # Get current timezone abbreviation for display
            tz_abbr = self.timezone_handler.get_timezone_abbreviation(server_timezone, local_dt)
            
            # Create at job
            success = self.create_at_job(server_name, local_dt, server_timezone)
            
            if success:
                self.logger.info(f"Scheduled patch for {server_name} at {local_dt} {tz_abbr}")
            else:
                # Try alternative method if at job fails
                success = self.create_cron_job_alternative(server_name, local_dt, server_timezone)
                if success:
                    self.logger.info(f"Scheduled patch for {server_name} using cron at {local_dt} {tz_abbr}")
                else:
                    self.logger.error(f"Failed to schedule patch for {server_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to schedule patch for {server_name}: {e}")
    
    def create_at_job(self, server_name, patch_datetime, server_timezone):
        """Create at job for patch execution"""
        try:
            # Convert to local server time for the at command
            # Format time for at command
            at_time = patch_datetime.strftime('%H:%M %Y-%m-%d')
            
            # Create the at job command
            at_command = f'bash {os.path.dirname(os.path.dirname(__file__))}/bash_scripts/patch_execution.sh {server_name}'
            
            # Use echo to pipe command to at
            process = subprocess.Popen(
                ['at', at_time],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=at_command)
            
            if process.returncode == 0:
                self.logger.info(f"AT job created for {server_name}: {stdout.strip()}")
                return True
            else:
                self.logger.error(f"Failed to create AT job for {server_name}: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception creating AT job for {server_name}: {e}")
            return False
    
    def create_cron_job_alternative(self, server_name, patch_datetime, server_timezone):
        """Alternative method using cron for scheduling"""
        try:
            cron_time = patch_datetime.strftime('%M %H %d %m *')
            script_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cron_command = f'bash {script_path}/bash_scripts/patch_execution.sh {server_name}'
            
            # Add to crontab
            current_crontab = subprocess.run(
                ['crontab', '-l'], 
                capture_output=True, text=True
            ).stdout
            
            new_cron_entry = f"{cron_time} {cron_command} # Patch job for {server_name}\n"
            
            if new_cron_entry not in current_crontab:
                updated_crontab = current_crontab + new_cron_entry
                
                process = subprocess.Popen(
                    ['crontab', '-'],
                    stdin=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=updated_crontab)
                
                return process.returncode == 0
            else:
                # Entry already exists
                return True
                
        except Exception as e:
            self.logger.error(f"Exception creating cron job for {server_name}: {e}")
            return False
