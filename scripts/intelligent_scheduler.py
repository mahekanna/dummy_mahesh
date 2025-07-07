# scripts/intelligent_scheduler.py
import calendar
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from utils.csv_handler import CSVHandler
from utils.logger import Logger
from config.settings import Config

class SmartScheduler:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.logger = Logger('smart_scheduler')
        
        # Configuration for smart scheduling
        self.MAX_SERVERS_PER_HOUR = 5  # Maximum servers per hour slot
        self.BASE_PATCHING_HOUR = 20   # 8 PM base time
        self.PATCHING_WINDOW_HOURS = 4 # 4-hour window (8 PM - 12 AM)
        self.TIME_SLOT_MINUTES = 30    # 30-minute increments
        
    def assign_smart_schedules(self, quarter):
        """Smart assignment of Thursday dates and times based on server count and constraints"""
        servers = self.csv_handler.read_servers()
        unscheduled_servers = []
        
        # Find servers without schedules for the quarter
        for server in servers:
            if not server.get(f'Q{quarter} Patch Date'):
                unscheduled_servers.append(server)
        
        if not unscheduled_servers:
            self.logger.info("No unscheduled servers found")
            return
        
        self.logger.info(f"Found {len(unscheduled_servers)} unscheduled servers for Q{quarter}")
        
        # Get available Thursday dates for the quarter
        available_thursdays = self.get_quarter_thursdays(quarter)
        
        # Group servers by criteria for intelligent assignment
        server_groups = self.group_servers_for_scheduling(unscheduled_servers)
        
        # Assign schedules based on groups and load balancing
        schedule_assignments = self.calculate_optimal_assignments(server_groups, available_thursdays)
        
        # Apply the assignments
        assigned_count = self.apply_schedule_assignments(servers, schedule_assignments, quarter)
        
        if assigned_count > 0:
            self.csv_handler.write_servers(servers)
            self.logger.info(f"Intelligently assigned schedules for {assigned_count} servers")
            
            # Generate assignment report
            self.generate_assignment_report(schedule_assignments, quarter)
    
    def get_quarter_thursdays(self, quarter):
        """Get all Thursday dates for the specified quarter"""
        quarter_months = Config.QUARTERS.get(quarter, {}).get('months', [])
        current_year = datetime.now().year
        thursdays = []
        
        for month in quarter_months:
            # Adjust year for Q1 which spans two years
            year = current_year
            if quarter == '1':
                if month in [11, 12]:  # Nov, Dec of current year
                    year = current_year if datetime.now().month >= 11 else current_year - 1
                else:  # Jan of next year
                    year = current_year + 1 if datetime.now().month >= 11 else current_year
            
            # Find all Thursdays in the month
            cal = calendar.monthcalendar(year, month)
            month_thursdays = [
                datetime(year, month, week[calendar.THURSDAY]).date()
                for week in cal
                if week[calendar.THURSDAY] != 0
            ]
            
            # Only include future Thursdays
            today = datetime.now().date()
            future_thursdays = [d for d in month_thursdays if d > today]
            thursdays.extend(future_thursdays)
        
        return sorted(thursdays)
    
    def group_servers_for_scheduling(self, servers):
        """Group servers by scheduling criteria for smart assignment"""
        # Load server groups configuration
        import json
        import os
        
        groups_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'server_groups.json')
        try:
            with open(groups_config_path, 'r') as f:
                config = json.load(f)
                server_groups_config = config['server_groups']
        except FileNotFoundError:
            self.logger.warning("Server groups configuration not found, using default groups")
            server_groups_config = self._get_default_groups()
        
        # Initialize groups from configuration
        groups = {}
        for group_name, group_config in server_groups_config.items():
            groups[group_name] = []
        
        for server in servers:
            server_name = server['Server Name'].lower()
            host_group = server.get('host_group', '')  # Keep original case
            location = server.get('location', '').lower()
            
            # Classify servers based on exact host group matching
            classified = False
            
            for group_name, group_config in server_groups_config.items():
                # Check for exact host group match (preferred method)
                configured_host_groups = group_config.get('host_groups', [])
                if host_group in configured_host_groups:
                    groups[group_name].append(server)
                    classified = True
                    self.logger.info(f"Classified {server['Server Name']} as {group_name} (host_group: {host_group})")
                    break
                
                # Fallback: Check naming patterns if host group doesn't match
                patterns = group_config.get('patterns', [])
                if not classified and patterns:
                    if any(pattern in server_name for pattern in patterns):
                        groups[group_name].append(server)
                        classified = True
                        self.logger.info(f"Classified {server['Server Name']} as {group_name} (pattern match)")
                        break
            
            # If not classified and 'other' group exists, put it there
            if not classified and 'other' in groups:
                groups['other'].append(server)
                self.logger.warning(f"Server {server['Server Name']} with host_group '{host_group}' not classified, using 'other'")
            elif not classified:
                # Create a temporary group for unclassified servers
                if 'unclassified' not in groups:
                    groups['unclassified'] = []
                groups['unclassified'].append(server)
                self.logger.warning(f"Server {server['Server Name']} with host_group '{host_group}' not classified")
        
        return groups
    
    def _get_default_groups(self):
        """Return default server groups if configuration file is missing"""
        return {
            'critical': {
                'patterns': ['prod', 'critical', 'production'],
                'host_groups': ['production', 'critical']
            },
            'database': {
                'patterns': ['db', 'database'],
                'host_groups': ['db_servers', 'database']
            },
            'web': {
                'patterns': ['web'],
                'host_groups': ['web_servers']
            },
            'application': {
                'patterns': ['app', 'application'],
                'host_groups': ['app_servers', 'application']
            },
            'development': {
                'patterns': ['dev', 'test', 'staging'],
                'host_groups': ['development', 'testing']
            },
            'other': {
                'patterns': [],
                'host_groups': []
            }
        }
    
    def calculate_optimal_assignments(self, server_groups, available_thursdays):
        """Calculate optimal date/time assignments with load balancing"""
        assignments = []
        
        # Get priority order from server groups configuration
        # Sort groups by priority (lower number = higher priority)
        groups_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'server_groups.json')
        priority_mapping = {}
        
        try:
            with open(groups_config_path, 'r') as f:
                config = json.load(f)
                for group_name, group_config in config.get('server_groups', {}).items():
                    priority_mapping[group_name] = group_config.get('priority', 5)
        except Exception as e:
            self.logger.warning(f"Could not load group priorities: {e}")
            # Default priorities
            priority_mapping = {group: 3 for group in server_groups.keys()}
        
        # Sort groups by priority (ascending - lower numbers first)
        priority_order = sorted(server_groups.keys(), key=lambda x: priority_mapping.get(x, 5))
        
        # Track server load per time slot
        time_slot_load = defaultdict(int)
        
        # Create time slots for each Thursday
        all_time_slots = []
        for thursday in available_thursdays:
            for hour_offset in range(self.PATCHING_WINDOW_HOURS):
                for minute_offset in [0, 30]:  # 30-minute increments
                    hour = self.BASE_PATCHING_HOUR + hour_offset
                    if hour >= 24:
                        continue
                    
                    time_slot = {
                        'date': thursday,
                        'time': f"{hour:02d}:{minute_offset:02d}",
                        'load': 0
                    }
                    all_time_slots.append(time_slot)
        
        # Assign servers to optimal time slots
        for group_name in priority_order:
            servers = server_groups[group_name]
            
            if not servers:
                continue
                
            self.logger.info(f"Scheduling {len(servers)} {group_name} servers")
            
            # Sort servers within group by additional criteria
            servers = self.sort_servers_within_group(servers, group_name)
            
            for server in servers:
                best_slot = self.find_best_time_slot(all_time_slots, server, group_name)
                
                if best_slot:
                    assignment = {
                        'server': server,
                        'date': best_slot['date'].strftime('%Y-%m-%d'),
                        'time': best_slot['time'],
                        'group': group_name,
                        'reason': self.get_assignment_reason(server, best_slot, group_name)
                    }
                    assignments.append(assignment)
                    
                    # Update slot load
                    best_slot['load'] += 1
                    time_slot_load[f"{best_slot['date']}_{best_slot['time']}"] += 1
                else:
                    self.logger.warning(f"Could not find suitable time slot for {server['Server Name']}")
        
        return assignments
    
    def sort_servers_within_group(self, servers, group_name):
        """Sort servers within a group by priority criteria"""
        if group_name == 'critical':
            # Critical servers: schedule by location to minimize impact
            return sorted(servers, key=lambda s: s.get('location', ''))
        elif group_name == 'database':
            # Database servers: schedule by host group to avoid conflicts
            return sorted(servers, key=lambda s: s.get('host_group', ''))
        else:
            # Other servers: sort by server name for consistency
            return sorted(servers, key=lambda s: s['Server Name'])
    
    def find_best_time_slot(self, time_slots, server, group_name):
        """Find the best available time slot for a server"""
        server_timezone = server.get('Server Timezone', 'UTC')
        
        # Filter available slots (not at capacity)
        available_slots = [
            slot for slot in time_slots 
            if slot['load'] < self.MAX_SERVERS_PER_HOUR
        ]
        
        if not available_slots:
            return None
        
        # Apply group-specific preferences
        if group_name == 'development':
            # Dev servers can be scheduled earlier
            preferred_slots = [s for s in available_slots if s['time'] <= '21:00']
            if preferred_slots:
                available_slots = preferred_slots
        
        elif group_name == 'critical':
            # Critical servers get prime time slots (not too late)
            preferred_slots = [s for s in available_slots if '20:00' <= s['time'] <= '22:00']
            if preferred_slots:
                available_slots = preferred_slots
        
        elif group_name == 'database':
            # Database servers prefer later slots to minimize user impact
            preferred_slots = [s for s in available_slots if s['time'] >= '21:00']
            if preferred_slots:
                available_slots = preferred_slots
        
        # Return slot with lowest current load
        return min(available_slots, key=lambda s: s['load'])
    
    def get_assignment_reason(self, server, time_slot, group_name):
        """Get human-readable reason for the assignment"""
        reasons = []
        
        reasons.append(f"Server type: {group_name}")
        reasons.append(f"Optimal load balancing (slot load: {time_slot['load']})")
        
        if group_name == 'development':
            reasons.append("Early scheduling for dev/test environments")
        elif group_name == 'critical':
            reasons.append("Prime time slot for critical systems")
        elif group_name == 'database':
            reasons.append("Late scheduling to minimize user impact")
        
        return "; ".join(reasons)
    
    def apply_schedule_assignments(self, servers, assignments, quarter):
        """Apply the calculated assignments to the servers"""
        assigned_count = 0
        
        assignment_lookup = {
            assignment['server']['Server Name']: assignment 
            for assignment in assignments
        }
        
        for server in servers:
            server_name = server['Server Name']
            if server_name in assignment_lookup:
                assignment = assignment_lookup[server_name]
                
                server[f'Q{quarter} Patch Date'] = assignment['date']
                server[f'Q{quarter} Patch Time'] = assignment['time']
                
                # Set status to scheduled
                if quarter == Config.get_current_quarter():
                    server['Current Quarter Patching Status'] = 'Scheduled'
                
                assigned_count += 1
                self.logger.info(
                    f"Assigned {server_name}: {assignment['date']} {assignment['time']} "
                    f"({assignment['group']}) - {assignment['reason']}"
                )
        
        return assigned_count
    
    def generate_assignment_report(self, assignments, quarter):
        """Generate a detailed assignment report"""
        self.logger.info("=== INTELLIGENT SCHEDULING REPORT ===")
        self.logger.info(f"Quarter: Q{quarter}")
        self.logger.info(f"Total servers assigned: {len(assignments)}")
        
        # Group by date
        by_date = defaultdict(list)
        for assignment in assignments:
            by_date[assignment['date']].append(assignment)
        
        for date in sorted(by_date.keys()):
            date_assignments = by_date[date]
            self.logger.info(f"\n{date} ({len(date_assignments)} servers):")
            
            # Group by time for this date
            by_time = defaultdict(list)
            for assignment in date_assignments:
                by_time[assignment['time']].append(assignment)
            
            for time in sorted(by_time.keys()):
                time_assignments = by_time[time]
                server_names = [a['server']['Server Name'] for a in time_assignments]
                self.logger.info(f"  {time}: {', '.join(server_names)} ({len(time_assignments)} servers)")
        
        # Group by server type
        by_group = defaultdict(int)
        for assignment in assignments:
            by_group[assignment['group']] += 1
        
        self.logger.info(f"\nBy server type:")
        for group, count in by_group.items():
            self.logger.info(f"  {group}: {count} servers")
        
        self.logger.info("=== END REPORT ===")
    
    def rebalance_existing_schedules(self, quarter):
        """Rebalance existing schedules to optimize load distribution"""
        servers = self.csv_handler.read_servers()
        scheduled_servers = []
        
        # Find servers with existing schedules
        for server in servers:
            if server.get(f'Q{quarter} Patch Date') and server.get(f'Q{quarter} Approval Status', 'Pending') != 'Approved':
                scheduled_servers.append(server)
        
        if len(scheduled_servers) < 2:
            self.logger.info("Not enough scheduled servers to rebalance")
            return
        
        self.logger.info(f"Rebalancing {len(scheduled_servers)} scheduled servers")
        
        # Clear existing schedules for rebalancing
        for server in scheduled_servers:
            server[f'Q{quarter} Patch Date'] = ''
            server[f'Q{quarter} Patch Time'] = ''
        
        # Re-run intelligent scheduling
        self.assign_intelligent_schedules(quarter)