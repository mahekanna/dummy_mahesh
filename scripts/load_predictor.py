# scripts/load_predictor.py
import os
import json
import subprocess
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from utils.csv_handler import CSVHandler
from utils.logger import Logger
from config.settings import Config

class SmartLoadPredictor:
    def __init__(self):
        self.csv_handler = CSVHandler()
        self.logger = Logger('smart_load_predictor')
        
        # Configuration for load analysis
        self.ANALYSIS_DAYS = 30        # Analyze last 30 days
        self.LOW_LOAD_THRESHOLD = 20   # CPU % threshold for low load
        self.HIGH_LOAD_THRESHOLD = 70  # CPU % threshold for high load
        self.MINIMAL_PROCESSES = 50    # Process count threshold for minimal activity
        
        # Historical data storage
        self.historical_data_file = 'logs/server_load_history.json'
        
    def analyze_server_load_patterns(self, server_name):
        """Analyze historical load patterns for a specific server"""
        try:
            self.logger.info(f"Analyzing load patterns for {server_name}")
            
            # Collect current system metrics
            current_metrics = self.collect_current_metrics(server_name)
            
            # Analyze historical patterns
            historical_patterns = self.analyze_historical_data(server_name)
            
            # Predict optimal patching windows
            optimal_windows = self.predict_optimal_windows(current_metrics, historical_patterns)
            
            # Generate recommendation
            recommendation = self.generate_load_recommendation(server_name, optimal_windows, current_metrics)
            
            # Store analysis for future reference
            self.store_analysis_results(server_name, {
                'timestamp': datetime.now().isoformat(),
                'current_metrics': current_metrics,
                'optimal_windows': optimal_windows,
                'recommendation': recommendation
            })
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error analyzing load for {server_name}: {e}")
            return self.get_default_recommendation()
    
    def collect_current_metrics(self, server_name):
        """Collect current system metrics (simulated for demo)"""
        # In production, this would connect to the actual server
        # For demo, we'll simulate realistic metrics
        
        import random
        current_hour = datetime.now().hour
        
        # Simulate realistic load patterns based on time of day
        if 9 <= current_hour <= 17:  # Business hours
            base_cpu = random.uniform(40, 80)
            base_processes = random.randint(150, 300)
            active_users = random.randint(10, 50)
        elif 18 <= current_hour <= 22:  # Evening
            base_cpu = random.uniform(20, 50)
            base_processes = random.randint(100, 200)
            active_users = random.randint(2, 15)
        else:  # Night/early morning
            base_cpu = random.uniform(5, 25)
            base_processes = random.randint(50, 120)
            active_users = random.randint(0, 5)
        
        metrics = {
            'cpu_usage': round(base_cpu, 2),
            'memory_usage': round(random.uniform(30, 85), 2),
            'process_count': base_processes,
            'active_users': active_users,
            'network_connections': random.randint(20, 200),
            'disk_io': round(random.uniform(5, 40), 2),
            'load_average': round(base_cpu / 100 * 4, 2),  # Simulate load average
            'collection_time': datetime.now().isoformat()
        }
        
        self.logger.info(f"Current metrics for {server_name}: CPU={metrics['cpu_usage']}%, "
                        f"Processes={metrics['process_count']}, Users={metrics['active_users']}")
        
        return metrics
    
    def analyze_historical_data(self, server_name):
        """Analyze historical load data to identify patterns"""
        try:
            # Load historical data
            historical_data = self.load_historical_data()
            server_history = historical_data.get(server_name, [])
            
            if not server_history:
                self.logger.warning(f"No historical data found for {server_name}, using default patterns")
                return self.generate_default_patterns()
            
            # Analyze patterns by hour of day and day of week
            hourly_patterns = defaultdict(list)
            daily_patterns = defaultdict(list)
            
            for record in server_history[-self.ANALYSIS_DAYS:]:  # Last N days
                try:
                    timestamp = datetime.fromisoformat(record['timestamp'])
                    hour = timestamp.hour
                    weekday = timestamp.weekday()  # 0=Monday, 6=Sunday
                    
                    hourly_patterns[hour].append(record['cpu_usage'])
                    daily_patterns[weekday].append(record['cpu_usage'])
                except (KeyError, ValueError) as e:
                    continue
            
            # Calculate average load by hour and day
            avg_hourly_load = {
                hour: sum(loads) / len(loads) if loads else 50
                for hour, loads in hourly_patterns.items()
            }
            
            avg_daily_load = {
                day: sum(loads) / len(loads) if loads else 50
                for day, loads in daily_patterns.items()
            }
            
            patterns = {
                'hourly_averages': avg_hourly_load,
                'daily_averages': avg_daily_load,
                'low_load_hours': [h for h, load in avg_hourly_load.items() if load < self.LOW_LOAD_THRESHOLD],
                'high_load_hours': [h for h, load in avg_hourly_load.items() if load > self.HIGH_LOAD_THRESHOLD],
                'analysis_period_days': len(server_history)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing historical data: {e}")
            return self.generate_default_patterns()
    
    def generate_default_patterns(self):
        """Generate default load patterns when no historical data is available"""
        return {
            'hourly_averages': {
                hour: 20 if hour < 8 or hour > 20 else 60  # Low load outside business hours
                for hour in range(24)
            },
            'daily_averages': {
                day: 45 if day < 5 else 25  # Lower load on weekends
                for day in range(7)
            },
            'low_load_hours': [0, 1, 2, 3, 4, 5, 6, 20, 21, 22, 23],
            'high_load_hours': [9, 10, 11, 14, 15, 16],
            'analysis_period_days': 0
        }
    
    def predict_optimal_windows(self, current_metrics, historical_patterns):
        """Predict optimal patching windows based on load analysis"""
        optimal_windows = []
        
        # Get low load hours from historical patterns
        low_load_hours = historical_patterns.get('low_load_hours', [20, 21, 22, 23])
        
        # Filter for evening/night hours suitable for patching
        evening_hours = [h for h in low_load_hours if 18 <= h <= 23]
        
        if not evening_hours:
            evening_hours = [20, 21, 22]  # Default to 8-10 PM
        
        # Create time windows with confidence scores
        for hour in evening_hours:
            avg_load = historical_patterns['hourly_averages'].get(hour, 50)
            
            # Calculate confidence score (lower load = higher confidence)
            confidence = max(0, 100 - avg_load) / 100
            
            optimal_windows.append({
                'hour': hour,
                'time_slot': f"{hour:02d}:00",
                'avg_historical_load': avg_load,
                'confidence_score': round(confidence, 2),
                'recommendation': self.get_window_recommendation(avg_load)
            })
        
        # Sort by confidence score (best windows first)
        optimal_windows.sort(key=lambda w: w['confidence_score'], reverse=True)
        
        return optimal_windows[:3]  # Return top 3 windows
    
    def get_window_recommendation(self, avg_load):
        """Get recommendation text based on average load"""
        if avg_load < self.LOW_LOAD_THRESHOLD:
            return "Excellent - Low system load"
        elif avg_load < 40:
            return "Good - Moderate system load"
        elif avg_load < self.HIGH_LOAD_THRESHOLD:
            return "Fair - Elevated system load"
        else:
            return "Poor - High system load"
    
    def generate_load_recommendation(self, server_name, optimal_windows, current_metrics):
        """Generate final recommendation for server patching"""
        if not optimal_windows:
            return self.get_default_recommendation()
        
        best_window = optimal_windows[0]
        
        recommendation = {
            'server_name': server_name,
            'recommended_time': best_window['time_slot'],
            'confidence_level': 'High' if best_window['confidence_score'] > 0.7 else 'Medium' if best_window['confidence_score'] > 0.4 else 'Low',
            'reasoning': [],
            'alternative_times': [w['time_slot'] for w in optimal_windows[1:3]],
            'risk_factors': [],
            'mitigation_steps': []
        }
        
        # Add reasoning
        if best_window['confidence_score'] > 0.7:
            recommendation['reasoning'].append(f"Historical data shows consistently low load at {best_window['time_slot']}")
        
        if current_metrics['active_users'] < 5:
            recommendation['reasoning'].append("Currently low user activity")
        else:
            recommendation['risk_factors'].append(f"Currently {current_metrics['active_users']} active users")
        
        if current_metrics['cpu_usage'] < self.LOW_LOAD_THRESHOLD:
            recommendation['reasoning'].append("Current CPU usage is low")
        elif current_metrics['cpu_usage'] > self.HIGH_LOAD_THRESHOLD:
            recommendation['risk_factors'].append("Current CPU usage is high")
        
        # Add mitigation steps if needed
        if recommendation['risk_factors']:
            recommendation['mitigation_steps'].extend([
                "Monitor system load before patching",
                "Consider postponing if critical processes are running",
                "Ensure backup systems are available"
            ])
        
        return recommendation
    
    def get_default_recommendation(self):
        """Get default recommendation when analysis fails"""
        return {
            'server_name': 'Unknown',
            'recommended_time': '22:00',
            'confidence_level': 'Low',
            'reasoning': ['Default evening patching window'],
            'alternative_times': ['21:00', '23:00'],
            'risk_factors': ['No historical data available'],
            'mitigation_steps': ['Monitor system during patching', 'Have rollback plan ready']
        }
    
    def load_historical_data(self):
        """Load historical server load data"""
        try:
            if os.path.exists(self.historical_data_file):
                with open(self.historical_data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load historical data: {e}")
        
        return {}
    
    def analyze_all_servers(self, quarter):
        """Analyze load patterns for all servers in the given quarter"""
        try:
            from utils.csv_handler import CSVHandler
            csv_handler = CSVHandler()
            servers = csv_handler.read_servers()
            
            recommendations = []
            
            for server in servers:
                server_name = server['Server Name']
                try:
                    recommendation = self.analyze_server_load_patterns(server_name)
                    recommendations.append({
                        'server_name': server_name,
                        'recommendation': recommendation
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {server_name}: {e}")
                    continue
            
            self.logger.info(f"Generated load analysis for {len(recommendations)} servers")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error analyzing all servers: {e}")
            return []
    
    def store_analysis_results(self, server_name, analysis_data):
        """Store analysis results for historical reference"""
        try:
            # Load existing data
            historical_data = self.load_historical_data()
            
            # Initialize server data if not exists
            if server_name not in historical_data:
                historical_data[server_name] = []
            
            # Add new analysis
            historical_data[server_name].append(analysis_data)
            
            # Keep only recent data (last 60 days)
            cutoff_date = datetime.now() - timedelta(days=60)
            historical_data[server_name] = [
                record for record in historical_data[server_name]
                if datetime.fromisoformat(record['timestamp']) > cutoff_date
            ]
            
            # Ensure logs directory exists
            os.makedirs(os.path.dirname(self.historical_data_file), exist_ok=True)
            
            # Save updated data
            with open(self.historical_data_file, 'w') as f:
                json.dump(historical_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Could not store analysis results: {e}")
    
    def analyze_all_servers(self, quarter):
        """Analyze load patterns for all servers and generate recommendations"""
        servers = self.csv_handler.read_servers()
        recommendations = {}
        
        self.logger.info("Starting load analysis for all servers")
        
        for server in servers:
            server_name = server['Server Name']
            
            # Skip if server already has approved schedule
            approval_status = server.get(f'Q{quarter} Approval Status', 'Pending')
            if approval_status == 'Approved':
                continue
            
            try:
                recommendation = self.analyze_server_load_patterns(server_name)
                recommendations[server_name] = recommendation
                
                # Update server with recommended time if no schedule exists
                if not server.get(f'Q{quarter} Patch Time'):
                    server[f'Q{quarter} Patch Time'] = recommendation['recommended_time']
                    self.logger.info(f"Updated {server_name} with recommended time: {recommendation['recommended_time']}")
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {server_name}: {e}")
                continue
        
        # Save updated servers
        if recommendations:
            self.csv_handler.write_servers(servers)
            self.generate_load_analysis_report(recommendations)
        
        return recommendations
    
    def generate_load_analysis_report(self, recommendations):
        """Generate comprehensive load analysis report"""
        self.logger.info("=== LOAD ANALYSIS REPORT ===")
        self.logger.info(f"Analyzed {len(recommendations)} servers")
        
        # Count by confidence level
        confidence_counts = Counter(rec['confidence_level'] for rec in recommendations.values())
        
        self.logger.info(f"Confidence levels: High={confidence_counts.get('High', 0)}, "
                        f"Medium={confidence_counts.get('Medium', 0)}, "
                        f"Low={confidence_counts.get('Low', 0)}")
        
        # Group by recommended time
        time_distribution = Counter(rec['recommended_time'] for rec in recommendations.values())
        
        self.logger.info("Recommended time distribution:")
        for time_slot, count in sorted(time_distribution.items()):
            self.logger.info(f"  {time_slot}: {count} servers")
        
        # High confidence recommendations
        high_confidence = [
            (name, rec) for name, rec in recommendations.items() 
            if rec['confidence_level'] == 'High'
        ]
        
        if high_confidence:
            self.logger.info(f"\nHigh confidence recommendations ({len(high_confidence)} servers):")
            for server_name, rec in high_confidence:
                self.logger.info(f"  {server_name}: {rec['recommended_time']} - {', '.join(rec['reasoning'])}")
        
        # Servers with risk factors
        risky_servers = [
            (name, rec) for name, rec in recommendations.items() 
            if rec['risk_factors']
        ]
        
        if risky_servers:
            self.logger.info(f"\nServers requiring attention ({len(risky_servers)} servers):")
            for server_name, rec in risky_servers:
                self.logger.info(f"  {server_name}: {', '.join(rec['risk_factors'])}")
        
        self.logger.info("=== END LOAD ANALYSIS REPORT ===")
    
    def simulate_historical_data(self, server_name, days=30):
        """Simulate historical data for testing purposes"""
        historical_data = self.load_historical_data()
        
        if server_name not in historical_data:
            historical_data[server_name] = []
        
        # Generate simulated data for the last N days
        for day_offset in range(days):
            timestamp = datetime.now() - timedelta(days=day_offset)
            
            # Simulate realistic daily patterns
            for hour in range(0, 24, 3):  # Every 3 hours
                record_time = timestamp.replace(hour=hour, minute=0, second=0)
                
                # Simulate load based on hour and server type
                if 'web' in server_name.lower():
                    base_load = 60 if 9 <= hour <= 17 else 25
                elif 'db' in server_name.lower():
                    base_load = 70 if 10 <= hour <= 16 else 30
                else:
                    base_load = 50 if 8 <= hour <= 18 else 20
                
                import random
                cpu_usage = max(5, min(95, base_load + random.uniform(-15, 15)))
                
                record = {
                    'timestamp': record_time.isoformat(),
                    'cpu_usage': round(cpu_usage, 2),
                    'memory_usage': round(random.uniform(30, 80), 2),
                    'process_count': random.randint(80, 250),
                    'active_users': random.randint(0, 20) if 8 <= hour <= 20 else random.randint(0, 3)
                }
                
                historical_data[server_name].append(record)
        
        # Save simulated data
        self.store_analysis_results(server_name, {'simulated': True})
        self.logger.info(f"Generated {days * 8} simulated data points for {server_name}")
        
        return historical_data[server_name]