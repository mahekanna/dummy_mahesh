#!/usr/bin/env python3
# scripts/csv_analyzer.py
"""
CSV Analyzer Tool - Analyze and validate CSV files for Linux Patching Automation

This tool helps users understand how their CSV files will be processed
and provides recommendations for field mapping.
"""

import sys
import argparse
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_handler import CSVHandler
from utils.logger import Logger

def main():
    parser = argparse.ArgumentParser(
        description="Analyze CSV files for Linux Patching Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 csv_analyzer.py /path/to/servers.csv
  python3 csv_analyzer.py --report /path/to/servers.csv
  python3 csv_analyzer.py --sample /path/to/servers.csv
  python3 csv_analyzer.py --validate /path/to/servers.csv
        """
    )
    
    parser.add_argument('csv_file', help='Path to CSV file to analyze')
    parser.add_argument('--report', action='store_true', 
                       help='Generate detailed field mapping report')
    parser.add_argument('--sample', action='store_true',
                       help='Show sample data with field mapping')
    parser.add_argument('--validate', action='store_true',
                       help='Validate CSV data and show any issues')
    parser.add_argument('--supported', action='store_true',
                       help='Show all supported field mappings')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress info messages')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    # Initialize CSV handler with specified file
    csv_handler = CSVHandler(args.csv_file)
    
    if not args.quiet:
        print(f"Analyzing CSV file: {args.csv_file}")
        print("=" * 60)
    
    # Basic analysis
    analysis = csv_handler.analyze_csv_structure()
    
    if 'error' in analysis:
        print(f"Error analyzing CSV: {analysis['error']}")
        sys.exit(1)
    
    # Basic summary
    print(f"CSV File Analysis Summary:")
    print(f"- Total columns: {analysis['total_headers']}")
    print(f"- Mapped to standard fields: {analysis['mapped_fields']}")
    print(f"- Sample rows analyzed: {len(analysis['sample_data'])}")
    
    # Required fields check
    required_status = analysis['required_fields_present']
    print(f"- Required fields:")
    for field, present in required_status.items():
        status = "✓" if present else "✗"
        print(f"  {status} {field}")
    
    if args.supported:
        print("\n" + "=" * 60)
        print("All Supported Field Mappings:")
        print("=" * 60)
        
        supported = csv_handler.get_supported_fields()
        for standard_field, variants in supported.items():
            print(f"\n{standard_field}:")
            for variant in variants:
                print(f"  - '{variant}'")
    
    if args.report:
        print("\n" + "=" * 60)
        print(csv_handler.get_field_mapping_report())
    
    if args.sample:
        print("\n" + "=" * 60)
        print("Sample Data with Field Mapping:")
        print("=" * 60)
        
        # Read a few servers with field normalization
        servers = csv_handler.read_servers(normalize_fields=True)
        
        if servers:
            print(f"\nFirst server (normalized fields):")
            print("-" * 40)
            for field, value in servers[0].items():
                display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"  {field}: {display_value}")
            
            if len(servers) > 1:
                print(f"\nNote: File contains {len(servers)} total servers")
        else:
            print("No server data found")
    
    if args.validate:
        print("\n" + "=" * 60)
        print("Data Validation:")
        print("=" * 60)
        
        servers = csv_handler.read_servers(normalize_fields=True)
        
        if not servers:
            print("✗ No servers found in CSV")
            sys.exit(1)
        
        total_servers = len(servers)
        valid_servers = 0
        issues_found = []
        
        for i, server in enumerate(servers, 1):
            # Basic validation
            server_name = server.get('server_name', '').strip()
            primary_owner = server.get('primary_owner', '').strip()
            
            server_issues = []
            
            if not server_name:
                server_issues.append("Missing server name")
            
            if not primary_owner:
                server_issues.append("Missing primary owner")
            elif '@' not in primary_owner:
                server_issues.append(f"Primary owner should be email: {primary_owner}")
            
            # Check for linux_user mapping
            primary_linux_user = server.get('primary_linux_user', '').strip()
            if primary_owner and not primary_linux_user:
                server_issues.append("Missing primary_linux_user (may need phonedb conversion)")
            
            if server_issues:
                issues_found.append(f"Row {i} ({server_name or 'unnamed'}): {', '.join(server_issues)}")
            else:
                valid_servers += 1
        
        print(f"Validation Results:")
        print(f"- Total servers: {total_servers}")
        print(f"- Valid servers: {valid_servers}")
        print(f"- Servers with issues: {len(issues_found)}")
        
        if issues_found:
            print(f"\nIssues Found:")
            print("-" * 20)
            for issue in issues_found[:10]:  # Show first 10 issues
                print(f"  • {issue}")
            
            if len(issues_found) > 10:
                print(f"  ... and {len(issues_found) - 10} more issues")
        else:
            print("\n✓ All servers passed validation!")
    
    # Recommendations
    if not args.quiet:
        print("\n" + "=" * 60)
        print("Recommendations:")
        print("=" * 60)
        
        if not all(required_status.values()):
            print("• Required fields are missing - CSV import may fail")
            print("• Consider renaming columns or adding custom field mappings")
        
        if analysis.get('unmapped_headers'):
            print("• Some headers were not mapped to standard fields")
            print("• These will be preserved as additional data")
        
        missing_linux_users = False
        if analysis['sample_data']:
            for row in analysis['sample_data']:
                if row.get('primary_owner') and not row.get('primary_linux_user'):
                    missing_linux_users = True
                    break
        
        if missing_linux_users:
            print("• Consider running phonedb conversion to populate linux_user fields")
            print("• Use: python3 -c \"from utils.master_csv_sync import MasterCSVSync; MasterCSVSync().force_username_conversion()\"")
        
        if analysis['mapped_fields'] == analysis['total_headers']:
            print("• ✓ All fields successfully mapped - CSV is ready for import!")

if __name__ == "__main__":
    main()