#!/usr/bin/env python3

import os
import sys
import datetime
import pytz
import argparse
import csv
from pprint import pprint

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Config
from utils.timezone_handler import TimezoneHandler
from utils.csv_handler import CSVHandler

def verify_quarter_system():
    """Verify that the quarter system is properly defined"""
    print("\n=== Quarter System Verification ===\n")
    
    # Check quarters definition
    print("Quarter definitions:")
    for quarter, details in Config.QUARTERS.items():
        print(f"  Q{quarter}: {details['name']} - Months: {details['months']}")
    
    # Verify each month is assigned to a quarter
    all_months = []
    for quarter, details in Config.QUARTERS.items():
        all_months.extend(details['months'])
    
    all_months.sort()
    expected_months = list(range(1, 13))
    
    if all_months == expected_months:
        print("\nSUCCESS: All months (1-12) are assigned to a quarter")
    else:
        print("\nERROR: Not all months are assigned to a quarter!")
        print(f"  Missing months: {set(expected_months) - set(all_months)}")
        print(f"  Duplicate months: {[m for m in all_months if all_months.count(m) > 1]}")
    
    # Test get_current_quarter function
    print("\nTesting quarter determination for each month:")
    
    # Save original now() function
    original_now = datetime.datetime.now
    
    try:
        # Override now() for testing
        test_months = {}
        
        for month in range(1, 13):
            # Mock current month
            test_date = datetime.datetime(2025, month, 15)
            datetime.datetime.now = lambda: test_date
            
            # Get quarter
            quarter = Config.get_current_quarter()
            test_months[month] = quarter
            print(f"  Month {month} -> Quarter {quarter}")
        
        # Verify quarters match definition
        success = True
        for month in range(1, 13):
            quarter = test_months[month]
            if month not in Config.QUARTERS[quarter]['months']:
                print(f"\n❌ Month {month} assigned to Q{quarter} but not in quarter definition!")
                success = False
        
        if success:
            print("\nSUCCESS: All months correctly mapped to quarters")
        
    finally:
        # Restore original now() function
        datetime.datetime.now = original_now

def verify_timezone_handling():
    """Verify that timezone handling is working correctly"""
    print("\n=== Timezone Handling Verification ===\n")
    
    tz_handler = TimezoneHandler()
    
    # Test canonical timezone mapping
    print("Testing canonical timezone mapping:")
    test_abbrs = ['EST', 'PST', 'IST', 'CEST', 'UTC']
    
    for abbr in test_abbrs:
        canonical = tz_handler.get_canonical_timezone(abbr)
        print(f"  {abbr} -> {canonical}")
    
    # Test timezone conversion
    print("\nTesting timezone conversion:")
    test_date = datetime.datetime(2025, 1, 15, 12, 0)  # Noon on Jan 15, 2025
    
    conversions = [
        ('UTC', 'America/New_York'),
        ('America/Los_Angeles', 'America/New_York'),
        ('Asia/Kolkata', 'Europe/London'),
        ('UTC', 'Asia/Tokyo')
    ]
    
    for from_tz, to_tz in conversions:
        converted = tz_handler.convert_timezone(test_date, from_tz, to_tz)
        print(f"  {test_date} {from_tz} -> {converted} {to_tz}")
    
    # Test timezone abbreviation
    print("\nTesting timezone abbreviation lookup:")
    
    # Test both standard time and daylight saving time
    winter_date = datetime.datetime(2025, 1, 15)  # January (standard time)
    summer_date = datetime.datetime(2025, 7, 15)  # July (daylight saving time)
    
    test_zones = [
        'America/New_York',
        'America/Los_Angeles',
        'Europe/London',
        'Australia/Sydney'
    ]
    
    for zone in test_zones:
        winter_abbr = tz_handler.get_timezone_abbreviation(zone, winter_date)
        summer_abbr = tz_handler.get_timezone_abbreviation(zone, summer_date)
        print(f"  {zone}: Winter={winter_abbr}, Summer={summer_abbr}")

def verify_csv_data():
    """Verify that server CSV data has correct quarter dates"""
    print("\n=== Server CSV Data Verification ===\n")
    
    try:
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers()
        
        print(f"Found {len(servers)} servers in CSV file")
        
        if len(servers) == 0:
            print("ERROR: No servers found in CSV!")
            return
        
        # Check quarter fields
        missing_fields = []
        for quarter in Config.QUARTERS.keys():
            date_field = f'Q{quarter} Patch Date'
            time_field = f'Q{quarter} Patch Time'
            
            # Check if any server has these fields
            date_exists = any(date_field in server for server in servers)
            time_exists = any(time_field in server for server in servers)
            
            if not date_exists:
                missing_fields.append(date_field)
            if not time_exists:
                missing_fields.append(time_field)
        
        if missing_fields:
            print(f"ERROR: Missing quarter fields in CSV: {missing_fields}")
        else:
            print("SUCCESS: All quarter date and time fields present in CSV")
        
        # Sample a few servers
        print("\nSample server data:")
        for i, server in enumerate(servers[:3]):  # Show first 3 servers
            print(f"\nServer {i+1}: {server.get('Server Name', 'Unknown')}")
            print(f"  Timezone: {server.get('Server Timezone', 'Unknown')}")
            
            for quarter in Config.QUARTERS.keys():
                date_field = f'Q{quarter} Patch Date'
                time_field = f'Q{quarter} Patch Time'
                
                date = server.get(date_field, 'Not set')
                time = server.get(time_field, 'Not set')
                
                print(f"  Q{quarter}: {date} {time}")
            
            print(f"  Status: {server.get('Current Quarter Patching Status', 'Unknown')}")
    
    except Exception as e:
        print(f"ERROR reading CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description='Verify Linux patching automation setup')
    parser.add_argument('--quarters', action='store_true', help='Verify quarter system')
    parser.add_argument('--timezones', action='store_true', help='Verify timezone handling')
    parser.add_argument('--csv', action='store_true', help='Verify CSV data')
    parser.add_argument('--all', action='store_true', help='Run all verifications')
    
    args = parser.parse_args()
    
    # If no specific option provided, run all
    if not any([args.quarters, args.timezones, args.csv, args.all]):
        args.all = True
    
    # Print header
    print("=" * 50)
    print("Linux Patching Automation Verification Tool")
    print("=" * 50)
    
    # Run verifications
    if args.quarters or args.all:
        verify_quarter_system()
    
    if args.timezones or args.all:
        verify_timezone_handling()
    
    if args.csv or args.all:
        verify_csv_data()
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    main()
