"""
Timezone Handler for Linux Patching Automation
Handles timezone conversions and SNMP-based timezone detection
"""

import pytz
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import os

from .logger import get_logger

class TimezoneHandler:
    """Comprehensive timezone handling with SNMP support"""
    
    def __init__(self):
        self.logger = get_logger('timezone_handler')
        
        # Common timezone mappings
        self.common_timezones = {
            'EST': 'America/New_York',
            'CST': 'America/Chicago',
            'MST': 'America/Denver',
            'PST': 'America/Los_Angeles',
            'EDT': 'America/New_York',
            'CDT': 'America/Chicago',
            'MDT': 'America/Denver',
            'PDT': 'America/Los_Angeles',
            'UTC': 'UTC',
            'GMT': 'Europe/London',
            'IST': 'Asia/Kolkata',
            'CEST': 'Europe/Berlin',
            'CET': 'Europe/Berlin',
            'JST': 'Asia/Tokyo',
            'AEST': 'Australia/Sydney',
            'AEDT': 'Australia/Sydney',
            'ACDT': 'Australia/Adelaide',
            'ACST': 'Australia/Darwin',
            'AWST': 'Australia/Perth',
            'NZST': 'Pacific/Auckland',
            'NZDT': 'Pacific/Auckland',
            'BST': 'Europe/London',
            'CAT': 'Africa/Johannesburg',
            'EAT': 'Africa/Nairobi',
            'WAT': 'Africa/Lagos',
            'MSK': 'Europe/Moscow',
            'HKT': 'Asia/Hong_Kong',
            'KST': 'Asia/Seoul',
            'SGT': 'Asia/Singapore'
        }
        
        # Reverse mapping for abbreviation lookup
        self.timezone_abbreviations = {}
        for abbr, tz in self.common_timezones.items():
            if tz not in self.timezone_abbreviations:
                self.timezone_abbreviations[tz] = []
            self.timezone_abbreviations[tz].append(abbr)
        
        # UTC offset to timezone mapping
        self.offset_to_timezone = {
            -12: 'Etc/GMT+12',
            -11: 'Etc/GMT+11',
            -10: 'Pacific/Honolulu',  # HST
            -9: 'America/Anchorage',  # AKST
            -8: 'America/Los_Angeles',  # PST
            -7: 'America/Denver',  # MST
            -6: 'America/Chicago',  # CST
            -5: 'America/New_York',  # EST
            -4: 'America/Halifax',  # AST
            -3: 'America/Sao_Paulo',
            -2: 'Etc/GMT+2',
            -1: 'Atlantic/Azores',
            0: 'Europe/London',  # GMT/UTC
            1: 'Europe/Paris',  # CET
            2: 'Europe/Athens',  # EET
            3: 'Europe/Moscow',
            4: 'Asia/Dubai',
            5: 'Asia/Karachi',
            5.5: 'Asia/Kolkata',  # IST
            6: 'Asia/Dhaka',
            7: 'Asia/Bangkok',
            8: 'Asia/Singapore',
            9: 'Asia/Tokyo',  # JST
            9.5: 'Australia/Darwin',  # ACST
            10: 'Australia/Sydney',  # AEST
            11: 'Pacific/Noumea',
            12: 'Pacific/Auckland',  # NZST
            13: 'Pacific/Tongatapu'
        }
        
        self.logger.info("Timezone handler initialized")
    
    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime from one timezone to another"""
        try:
            # Normalize timezone names
            from_tz = self.get_canonical_timezone(from_tz)
            to_tz = self.get_canonical_timezone(to_tz)
            
            # Get timezone objects
            from_timezone = pytz.timezone(from_tz)
            to_timezone = pytz.timezone(to_tz)
            
            # Localize if naive datetime
            if dt.tzinfo is None:
                dt = from_timezone.localize(dt)
            
            # Convert timezone
            converted_dt = dt.astimezone(to_timezone)
            
            self.logger.debug(f"Converted {dt} from {from_tz} to {to_tz}: {converted_dt}")
            return converted_dt
            
        except Exception as e:
            self.logger.error(f"Timezone conversion failed: {e}")
            return dt
    
    def get_canonical_timezone(self, timezone_str: str) -> str:
        """Convert a timezone abbreviation to a canonical timezone name"""
        if timezone_str in self.common_timezones:
            return self.common_timezones[timezone_str]
        
        # Check if it's already a canonical name
        try:
            pytz.timezone(timezone_str)
            return timezone_str
        except pytz.exceptions.UnknownTimeZoneError:
            # Return UTC as fallback
            self.logger.warning(f"Unknown timezone: {timezone_str}, defaulting to UTC")
            return 'UTC'
    
    def get_timezone_abbreviation(self, timezone_str: str, date: Optional[datetime] = None) -> str:
        """Get the timezone abbreviation for a timezone"""
        if timezone_str in self.common_timezones.keys():
            return timezone_str
        
        timezone_str = self.get_canonical_timezone(timezone_str)
        
        try:
            tz = pytz.timezone(timezone_str)
            
            # Use the provided date or current date to determine if DST is in effect
            if date is None:
                date = datetime.now()
            
            # Get the timezone info for the given date
            localized_dt = tz.localize(datetime(date.year, date.month, date.day))
            
            # Try to find the abbreviation in our mapping
            if timezone_str in self.timezone_abbreviations:
                abbreviations = self.timezone_abbreviations[timezone_str]
                
                # If only one abbreviation exists, return it
                if len(abbreviations) == 1:
                    return abbreviations[0]
                
                # Check if DST is in effect
                is_dst = localized_dt.dst().total_seconds() != 0
                
                # For timezones with both standard and daylight saving time abbreviations
                for abbr in abbreviations:
                    if (is_dst and abbr.endswith('DT')) or (not is_dst and abbr.endswith('ST')):
                        return abbr
                
                # If no matching DST/ST abbreviation found, return the first one
                return abbreviations[0]
            
            # Get abbreviation from timezone object
            return localized_dt.strftime('%Z')
            
        except Exception as e:
            self.logger.error(f"Failed to get timezone abbreviation: {e}")
            return timezone_str
    
    def get_current_time_in_timezone(self, timezone_str: str) -> datetime:
        """Get current time in specified timezone"""
        try:
            timezone_str = self.get_canonical_timezone(timezone_str)
            tz = pytz.timezone(timezone_str)
            return datetime.now(tz)
        except Exception as e:
            self.logger.error(f"Failed to get current time in timezone: {e}")
            return datetime.now(pytz.UTC)
    
    def validate_timezone(self, timezone_str: str) -> bool:
        """Validate if timezone string is valid"""
        try:
            timezone_str = self.get_canonical_timezone(timezone_str)
            pytz.timezone(timezone_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    def fetch_server_timezone_snmp(self, server_name: str, community: str = 'public',
                                  timeout: int = 30) -> Tuple[str, str]:
        """
        Fetch server timezone using SNMP
        
        Returns:
            Tuple containing (timezone_canonical, timezone_abbreviation)
        """
        try:
            self.logger.debug(f"Fetching timezone for {server_name} via SNMP")
            
            # Use snmpwalk to get system time MIB
            # OID: .1.3.6.1.2.1.25.1.2.0 (hrSystemDate)
            cmd = ['snmpwalk', '-v2c', '-c', community, server_name, '.1.3.6.1.2.1.25.1.2.0']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode != 0:
                self.logger.warning(f"SNMP query failed for {server_name}: {result.stderr}")
                return self._fetch_timezone_alternate(server_name)
            
            # Parse UTC offset from the result
            # Example output: HOST-RESOURCES-MIB::hrSystemDate.0 = STRING: 2023-5-20,10:23:44.0,+10:0
            output = result.stdout.strip()
            self.logger.debug(f"SNMP response: {output}")
            
            utc_offset_match = re.search(r'([+-])(\d+):(\d+)$', output)
            
            if not utc_offset_match:
                self.logger.warning(f"Could not parse UTC offset from SNMP response: {output}")
                return self._fetch_timezone_alternate(server_name)
            
            sign = -1 if utc_offset_match.group(1) == '-' else 1
            hours_offset = sign * int(utc_offset_match.group(2))
            minutes_offset = int(utc_offset_match.group(3))
            
            # Convert UTC offset to timezone
            canonical_tz = self._get_timezone_from_offset(hours_offset, minutes_offset)
            
            # Get current abbreviation for this timezone
            now = datetime.now()
            tz_abbr = self.get_timezone_abbreviation(canonical_tz, now)
            
            self.logger.info(f"Detected timezone for {server_name}: {canonical_tz} ({tz_abbr})")
            return canonical_tz, tz_abbr
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"SNMP timeout for {server_name}")
            return self._fetch_timezone_alternate(server_name)
        except Exception as e:
            self.logger.error(f"SNMP timezone detection failed for {server_name}: {e}")
            return self._fetch_timezone_alternate(server_name)
    
    def _fetch_timezone_alternate(self, server_name: str) -> Tuple[str, str]:
        """Alternate method to fetch timezone using SSH"""
        try:
            self.logger.debug(f"Attempting SSH timezone detection for {server_name}")
            
            # Try to get timezone from the system using SSH
            cmd = ['ssh', '-o', 'ConnectTimeout=30', '-o', 'StrictHostKeyChecking=no', 
                   server_name, 'timedatectl status 2>/dev/null | grep "Time zone" || cat /etc/timezone 2>/dev/null || date +%Z']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                self.logger.debug(f"SSH timezone response: {output}")
                
                # Try to parse timedatectl output
                # Example: "Time zone: America/New_York (EDT, -0400)"
                tz_match = re.search(r'Time zone:\s+([^\s]+)\s+\(([^,\s]+)', output)
                
                if tz_match:
                    canonical_tz = tz_match.group(1)
                    tz_abbr = tz_match.group(2)
                    self.logger.info(f"SSH detected timezone for {server_name}: {canonical_tz} ({tz_abbr})")
                    return canonical_tz, tz_abbr
                
                # Try to parse timezone file content
                lines = output.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Check if it's a timezone name
                        if self.validate_timezone(line):
                            tz_abbr = self.get_timezone_abbreviation(line)
                            self.logger.info(f"SSH detected timezone for {server_name}: {line} ({tz_abbr})")
                            return line, tz_abbr
                        
                        # Check if it's an abbreviation
                        if line in self.common_timezones:
                            canonical_tz = self.common_timezones[line]
                            self.logger.info(f"SSH detected timezone for {server_name}: {canonical_tz} ({line})")
                            return canonical_tz, line
            
            # Last resort - try to determine from date command
            cmd = ['ssh', '-o', 'ConnectTimeout=30', '-o', 'StrictHostKeyChecking=no',
                   server_name, 'date', '+%Z %z']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    tz_abbr = parts[0]
                    offset = parts[1]
                    
                    # Parse offset (+0400 format)
                    if len(offset) >= 5:
                        sign = -1 if offset[0] == '-' else 1
                        hours_offset = sign * int(offset[1:3])
                        minutes_offset = int(offset[3:5])
                        
                        canonical_tz = self._get_timezone_from_offset(hours_offset, minutes_offset)
                        self.logger.info(f"SSH detected timezone for {server_name} via date: {canonical_tz} ({tz_abbr})")
                        return canonical_tz, tz_abbr
            
            # Default fallback
            self.logger.warning(f"Could not determine timezone for {server_name}, defaulting to UTC")
            return 'UTC', 'UTC'
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"SSH timeout for {server_name}")
            return 'UTC', 'UTC'
        except Exception as e:
            self.logger.error(f"SSH timezone detection failed for {server_name}: {e}")
            return 'UTC', 'UTC'
    
    def _get_timezone_from_offset(self, hours: int, minutes: int) -> str:
        """Try to determine timezone from UTC offset"""
        # Handle half-hour offsets
        total_offset = hours + (minutes / 60)
        
        if total_offset in self.offset_to_timezone:
            return self.offset_to_timezone[total_offset]
        
        # If not found in the map, use Etc/GMT format
        # Note: Etc/GMT offsets have inverted signs compared to normal UTC offsets
        if hours >= 0:
            return f'Etc/GMT-{abs(hours)}'
        else:
            return f'Etc/GMT+{abs(hours)}'
    
    def get_timezone_info(self, timezone_str: str) -> Dict[str, any]:
        """Get comprehensive timezone information"""
        try:
            canonical_tz = self.get_canonical_timezone(timezone_str)
            tz = pytz.timezone(canonical_tz)
            now = datetime.now(tz)
            
            info = {
                'canonical_name': canonical_tz,
                'abbreviation': self.get_timezone_abbreviation(canonical_tz),
                'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'utc_offset': now.strftime('%z'),
                'is_dst': now.dst().total_seconds() != 0,
                'dst_offset': str(now.dst()),
                'localized_name': now.strftime('%Z'),
                'common_abbreviations': self.timezone_abbreviations.get(canonical_tz, [])
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get timezone info: {e}")
            return {
                'canonical_name': timezone_str,
                'abbreviation': timezone_str,
                'current_time': 'Unknown',
                'utc_offset': 'Unknown',
                'is_dst': False,
                'dst_offset': 'Unknown',
                'localized_name': timezone_str,
                'common_abbreviations': []
            }
    
    def list_all_timezones(self) -> List[str]:
        """List all available timezones"""
        return pytz.all_timezones
    
    def list_common_timezones(self) -> List[str]:
        """List common timezones"""
        return pytz.common_timezones
    
    def search_timezones(self, query: str) -> List[str]:
        """Search for timezones matching query"""
        query = query.lower()
        matches = []
        
        # Search in common timezones
        for tz in pytz.common_timezones:
            if query in tz.lower():
                matches.append(tz)
        
        # Search in abbreviations
        for abbr, canonical in self.common_timezones.items():
            if query in abbr.lower():
                matches.append(f"{canonical} ({abbr})")
        
        return sorted(set(matches))
    
    def get_timezone_for_coordinates(self, latitude: float, longitude: float) -> str:
        """Get timezone for geographical coordinates (requires timezonefinder)"""
        try:
            from timezonefinder import TimezoneFinder
            
            tf = TimezoneFinder()
            timezone = tf.timezone_at(lat=latitude, lng=longitude)
            
            if timezone:
                return timezone
            else:
                self.logger.warning(f"Could not find timezone for coordinates ({latitude}, {longitude})")
                return 'UTC'
                
        except ImportError:
            self.logger.warning("timezonefinder not installed, cannot get timezone for coordinates")
            return 'UTC'
        except Exception as e:
            self.logger.error(f"Failed to get timezone for coordinates: {e}")
            return 'UTC'
    
    def calculate_patch_window(self, server_timezone: str, patch_date: str, 
                             patch_time: str, duration_hours: int = 4) -> Dict[str, str]:
        """Calculate patch window in different timezones"""
        try:
            # Parse patch date and time
            patch_datetime = datetime.strptime(f"{patch_date} {patch_time}", '%Y-%m-%d %H:%M')
            
            # Get server timezone
            server_tz = pytz.timezone(self.get_canonical_timezone(server_timezone))
            
            # Localize patch datetime to server timezone
            patch_start = server_tz.localize(patch_datetime)
            patch_end = patch_start + timedelta(hours=duration_hours)
            
            # Convert to various timezones
            utc_start = patch_start.astimezone(pytz.UTC)
            utc_end = patch_end.astimezone(pytz.UTC)
            
            local_tz = pytz.timezone('America/New_York')  # Default to EST
            local_start = patch_start.astimezone(local_tz)
            local_end = patch_end.astimezone(local_tz)
            
            return {
                'server_timezone': server_timezone,
                'server_start': patch_start.strftime('%Y-%m-%d %H:%M %Z'),
                'server_end': patch_end.strftime('%Y-%m-%d %H:%M %Z'),
                'utc_start': utc_start.strftime('%Y-%m-%d %H:%M %Z'),
                'utc_end': utc_end.strftime('%Y-%m-%d %H:%M %Z'),
                'local_start': local_start.strftime('%Y-%m-%d %H:%M %Z'),
                'local_end': local_end.strftime('%Y-%m-%d %H:%M %Z'),
                'duration_hours': duration_hours
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate patch window: {e}")
            return {
                'server_timezone': server_timezone,
                'error': str(e)
            }
    
    def get_business_hours(self, timezone_str: str, start_hour: int = 9, 
                          end_hour: int = 17) -> Dict[str, str]:
        """Get business hours in specified timezone"""
        try:
            canonical_tz = self.get_canonical_timezone(timezone_str)
            tz = pytz.timezone(canonical_tz)
            
            today = datetime.now(tz).date()
            
            business_start = tz.localize(datetime.combine(today, datetime.min.time().replace(hour=start_hour)))
            business_end = tz.localize(datetime.combine(today, datetime.min.time().replace(hour=end_hour)))
            
            return {
                'timezone': canonical_tz,
                'business_start': business_start.strftime('%H:%M %Z'),
                'business_end': business_end.strftime('%H:%M %Z'),
                'utc_start': business_start.astimezone(pytz.UTC).strftime('%H:%M %Z'),
                'utc_end': business_end.astimezone(pytz.UTC).strftime('%H:%M %Z')
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get business hours: {e}")
            return {
                'timezone': timezone_str,
                'error': str(e)
            }
    
    def is_business_hours(self, timezone_str: str, check_time: datetime = None,
                         start_hour: int = 9, end_hour: int = 17) -> bool:
        """Check if current time is within business hours"""
        try:
            canonical_tz = self.get_canonical_timezone(timezone_str)
            tz = pytz.timezone(canonical_tz)
            
            if check_time is None:
                check_time = datetime.now(tz)
            elif check_time.tzinfo is None:
                check_time = tz.localize(check_time)
            else:
                check_time = check_time.astimezone(tz)
            
            hour = check_time.hour
            weekday = check_time.weekday()  # Monday is 0, Sunday is 6
            
            # Check if it's a weekday (Monday-Friday)
            if weekday >= 5:  # Saturday or Sunday
                return False
            
            # Check if it's within business hours
            return start_hour <= hour < end_hour
            
        except Exception as e:
            self.logger.error(f"Failed to check business hours: {e}")
            return False
    
    def save_timezone_cache(self, cache_file: str):
        """Save timezone cache to file"""
        try:
            cache_data = {
                'common_timezones': self.common_timezones,
                'timezone_abbreviations': self.timezone_abbreviations,
                'offset_to_timezone': self.offset_to_timezone,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.logger.info(f"Timezone cache saved to {cache_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save timezone cache: {e}")
    
    def load_timezone_cache(self, cache_file: str):
        """Load timezone cache from file"""
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                self.common_timezones.update(cache_data.get('common_timezones', {}))
                self.timezone_abbreviations.update(cache_data.get('timezone_abbreviations', {}))
                self.offset_to_timezone.update(cache_data.get('offset_to_timezone', {}))
                
                self.logger.info(f"Timezone cache loaded from {cache_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load timezone cache: {e}")

# Example usage
if __name__ == "__main__":
    # Example of using the timezone handler
    tz_handler = TimezoneHandler()
    
    # Test timezone conversion
    now = datetime.now()
    est_time = tz_handler.convert_timezone(now, 'UTC', 'EST')
    print(f"Current time in EST: {est_time}")
    
    # Test timezone validation
    print(f"Is 'America/New_York' valid? {tz_handler.validate_timezone('America/New_York')}")
    print(f"Is 'Invalid/Timezone' valid? {tz_handler.validate_timezone('Invalid/Timezone')}")
    
    # Test timezone info
    info = tz_handler.get_timezone_info('America/New_York')
    print(f"Timezone info: {json.dumps(info, indent=2)}")
    
    # Test search
    matches = tz_handler.search_timezones('new')
    print(f"Timezones matching 'new': {matches[:5]}")
    
    # Test business hours
    business_hours = tz_handler.get_business_hours('America/New_York')
    print(f"Business hours in NY: {business_hours}")
    
    print(f"Is it business hours now? {tz_handler.is_business_hours('America/New_York')}")
    
    # Test SNMP timezone detection (would need actual server)
    # canonical_tz, tz_abbr = tz_handler.fetch_server_timezone_snmp('localhost')
    # print(f"Server timezone: {canonical_tz} ({tz_abbr})")
    
    print("Timezone handler testing completed!")