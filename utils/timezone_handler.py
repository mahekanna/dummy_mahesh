# utils/timezone_handler.py
import pytz
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class TimezoneHandler:
    def __init__(self):
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
            'NZDT': 'Pacific/Auckland'
        }
        
        # Inverse mapping for abbreviation lookup
        self.timezone_abbreviations = {}
        for abbr, tz in self.common_timezones.items():
            self.timezone_abbreviations[tz] = self.timezone_abbreviations.get(tz, []) + [abbr]
    
    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime from one timezone to another"""
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
        return converted_dt
    
    def get_canonical_timezone(self, timezone_str: str) -> str:
        """Convert a timezone abbreviation to a canonical timezone name"""
        return self.common_timezones.get(timezone_str, timezone_str)
    
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
            timezone_info = tz.localize(datetime(date.year, date.month, date.day)).tzinfo
            
            # Try to find the abbreviation in our mapping
            if timezone_str in self.timezone_abbreviations:
                abbreviations = self.timezone_abbreviations[timezone_str]
                
                # If only one abbreviation exists, return it
                if len(abbreviations) == 1:
                    return abbreviations[0]
                
                # Check if DST is in effect to determine which abbreviation to use
                is_dst = timezone_info._dst.seconds != 0 if hasattr(timezone_info, '_dst') else False
                
                # For timezones with both standard and daylight saving time abbreviations
                for abbr in abbreviations:
                    if (is_dst and abbr.endswith('DT')) or (not is_dst and abbr.endswith('ST')):
                        return abbr
                
                # If no matching DST/ST abbreviation found, return the first one
                return abbreviations[0]
            
            # If we can't find it in our mapping, try to get it from the tzinfo
            if hasattr(timezone_info, 'tzname'):
                return timezone_info.tzname(date)
            
            # Last resort, return the canonical name
            return timezone_str
            
        except Exception:
            return timezone_str
    
    def get_current_time_in_timezone(self, timezone_str: str) -> datetime:
        """Get current time in specified timezone"""
        timezone_str = self.get_canonical_timezone(timezone_str)
        tz = pytz.timezone(timezone_str)
        return datetime.now(tz)
    
    def validate_timezone(self, timezone_str: str) -> bool:
        """Validate if timezone string is valid"""
        try:
            timezone_str = self.get_canonical_timezone(timezone_str)
            pytz.timezone(timezone_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    def fetch_server_timezone_snmp(self, server_name: str) -> Tuple[str, str]:
        """Fetch server timezone using SNMP
        
        Returns:
            Tuple containing (timezone_canonical, timezone_abbreviation)
        """
        try:
            # Use snmpwalk to get system time MIB
            # OID: .1.3.6.1.2.1.25.1.2.0 (hrSystemDate)
            cmd = ['snmpwalk', '-v2c', '-c', 'public', server_name, '.1.3.6.1.2.1.25.1.2.0']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"SNMP query failed: {result.stderr}")
            
            # Parse UTC offset from the result
            # Example output: HOST-RESOURCES-MIB::hrSystemDate.0 = STRING: 2023-5-20,10:23:44.0,+10:0
            output = result.stdout.strip()
            utc_offset_match = re.search(r'([+-]\d+):(\d+)$', output)
            
            if not utc_offset_match:
                # If we can't parse UTC offset, try another method
                return self._fetch_timezone_alternate(server_name)
            
            hours_offset = int(utc_offset_match.group(1))
            minutes_offset = int(utc_offset_match.group(2))
            
            # Convert UTC offset to timezone
            canonical_tz = self._get_timezone_from_offset(hours_offset, minutes_offset)
            
            # Get current abbreviation for this timezone
            now = datetime.now()
            tz_abbr = self.get_timezone_abbreviation(canonical_tz, now)
            
            return canonical_tz, tz_abbr
            
        except Exception as e:
            # Fallback to alternate method
            return self._fetch_timezone_alternate(server_name)
    
    def _fetch_timezone_alternate(self, server_name: str) -> Tuple[str, str]:
        """Alternate method to fetch timezone using SSH"""
        try:
            # Try to get timezone from the system using SSH
            cmd = ['ssh', server_name, 'timedatectl']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Example output: "Time zone: America/New_York (EDT, -0400)"
                output = result.stdout.strip()
                tz_match = re.search(r'Time zone: ([^\s]+)\s+\(([^\s,]+)', output)
                
                if tz_match:
                    canonical_tz = tz_match.group(1)
                    tz_abbr = tz_match.group(2)
                    return canonical_tz, tz_abbr
            
            # If timedatectl doesn't work, try /etc/timezone
            cmd = ['ssh', server_name, 'cat', '/etc/timezone']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                canonical_tz = result.stdout.strip()
                tz_abbr = self.get_timezone_abbreviation(canonical_tz)
                return canonical_tz, tz_abbr
            
            # Last resort - try to determine from date command
            cmd = ['ssh', server_name, 'date', '+%Z %z']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    tz_abbr = parts[0]
                    offset = parts[1]
                    
                    # Parse offset (+0400 format)
                    if len(offset) >= 5:
                        hours_offset = int(offset[0:3])
                        minutes_offset = int(offset[3:5])
                        
                        canonical_tz = self._get_timezone_from_offset(hours_offset, minutes_offset)
                        return canonical_tz, tz_abbr
            
            # Default fallback
            return 'UTC', 'UTC'
            
        except Exception as e:
            # Default to UTC if all methods fail
            return 'UTC', 'UTC'
    
    def _get_timezone_from_offset(self, hours: int, minutes: int) -> str:
        """Try to determine timezone from UTC offset"""
        # This is a simplified mapping - in reality multiple timezones can have the same offset
        offset_map = {
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
        
        # Handle half-hour offsets
        total_offset = hours + (minutes / 60)
        
        if total_offset in offset_map:
            return offset_map[total_offset]
        
        # If not found in the map, use Etc/GMT format
        # Note: Etc/GMT offsets have inverted signs compared to normal UTC offsets
        if hours >= 0:
            return f'Etc/GMT-{abs(hours)}'
        else:
            return f'Etc/GMT+{abs(hours)}'
