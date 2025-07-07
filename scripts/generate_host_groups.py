#!/usr/bin/env python3
"""
Generate server groups configuration based on actual CSV host groups
"""

import json
import os
import sys
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.csv_handler import CSVHandler
from config.settings import Config

def analyze_host_groups():
    """Analyze actual host groups from CSV data"""
    csv_handler = CSVHandler()
    servers = csv_handler.read_servers()
    
    # Count servers by host group
    host_group_counts = defaultdict(int)
    host_group_servers = defaultdict(list)
    
    for server in servers:
        host_group = server.get('host_group', 'unknown')
        if host_group:
            host_group_counts[host_group] += 1
            host_group_servers[host_group].append(server['Server Name'])
    
    return host_group_counts, host_group_servers

def generate_server_groups_config():
    """Generate server groups configuration based on actual CSV data"""
    host_group_counts, host_group_servers = analyze_host_groups()
    
    print("🔍 Analyzing actual host groups from CSV...")
    print("\nFound host groups:")
    for group, count in host_group_counts.items():
        print(f"  {group}: {count} servers")
        sample_servers = host_group_servers[group][:3]  # Show first 3
        print(f"    Examples: {', '.join(sample_servers)}")
        if len(host_group_servers[group]) > 3:
            print(f"    ... and {len(host_group_servers[group]) - 3} more")
        print()
    
    # Generate dynamic configuration based on actual host groups
    server_groups_config = {
        "server_groups": {},
        "load_balancing": {
            "max_servers_per_hour": 5,
            "min_gap_between_critical": 60,
            "preferred_start_time": "20:00",
            "max_duration_hours": 6
        }
    }
    
    # Define scheduling priorities based on typical server types
    priority_mapping = {
        'db_servers': 1,      # Database servers - highest priority (most critical)
        'web_servers': 2,     # Web servers - high priority
        'app_servers': 3,     # Application servers - medium priority
        'dev_servers': 4,     # Development servers - lower priority
        'test_servers': 5,    # Test servers - lowest priority
    }
    
    # Define max concurrent based on server type criticality
    concurrency_mapping = {
        'db_servers': 2,      # Database servers - very limited concurrency
        'web_servers': 4,     # Web servers - moderate concurrency
        'app_servers': 3,     # Application servers - moderate concurrency
        'dev_servers': 6,     # Development servers - higher concurrency
        'test_servers': 8,    # Test servers - highest concurrency
    }
    
    # Define scheduling windows based on server types
    window_mapping = {
        'db_servers': '21:00-02:00',     # Database - late night maintenance
        'web_servers': '20:00-01:00',    # Web servers - evening maintenance
        'app_servers': '19:00-23:00',    # App servers - early evening
        'dev_servers': '18:00-23:59',    # Dev servers - flexible timing
        'test_servers': '18:00-23:59',   # Test servers - flexible timing
    }
    
    # Generate configuration for each actual host group
    for group_name, count in host_group_counts.items():
        # Determine priority (default to 5 if not in mapping)
        priority = priority_mapping.get(group_name, 5)
        
        # Determine concurrency (default based on server count)
        max_concurrent = concurrency_mapping.get(group_name, min(3, max(1, count // 2)))
        
        # Determine scheduling window
        scheduling_window = window_mapping.get(group_name, '20:00-23:00')
        
        # Create friendly display name
        display_name = group_name.replace('_', ' ').title()
        
        # Generate description
        description = f"{display_name} ({count} servers) - Automatically configured based on CSV data"
        
        server_groups_config["server_groups"][group_name] = {
            "name": display_name,
            "description": description,
            "priority": priority,
            "max_concurrent": max_concurrent,
            "scheduling_window": scheduling_window,
            "patterns": [],  # Not needed since we use exact host_group matching
            "host_groups": [group_name],  # Exact match for this host group
            "server_count": count,
            "auto_generated": True
        }
    
    return server_groups_config

def save_generated_config(config):
    """Save the generated configuration"""
    config_path = os.path.join(Config.CONFIG_DIR, 'server_groups.json')
    
    # Create backup of existing config if it exists
    if os.path.exists(config_path):
        backup_path = config_path + '.backup'
        os.rename(config_path, backup_path)
        print(f"📁 Backed up existing config to {backup_path}")
    
    # Save new configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"✅ Generated server groups configuration saved to {config_path}")

def main():
    print("🚀 Generating Server Groups Configuration from CSV Data")
    print("=" * 60)
    
    try:
        # Generate configuration
        config = generate_server_groups_config()
        
        # Save configuration
        save_generated_config(config)
        
        print("\n📋 Generated Configuration Summary:")
        print("-" * 40)
        for group_name, group_config in config["server_groups"].items():
            print(f"✅ {group_config['name']}")
            print(f"   Priority: {group_config['priority']}")
            print(f"   Max Concurrent: {group_config['max_concurrent']}")
            print(f"   Scheduling Window: {group_config['scheduling_window']}")
            print(f"   Server Count: {group_config['server_count']}")
            print()
        
        print("SUCCESS: Server groups configuration generated successfully!")
        print("\nNext steps:")
        print("1. Review the generated configuration")
        print("2. Restart the web portal to see the new groups")
        print("3. Test the intelligent scheduling with real host groups")
        
    except Exception as e:
        print(f"ERROR: Error generating configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()