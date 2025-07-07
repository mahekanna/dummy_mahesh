#!/usr/bin/env python3
"""
Automated Reports Scheduler
Sends weekly and monthly admin reports automatically
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.admin_manager import AdminManager
from utils.logger import Logger

class AutomatedReports:
    def __init__(self):
        self.logger = Logger('automated_reports')
        self.admin_manager = AdminManager()
    
    def should_send_weekly_report(self):
        """Check if it's time to send weekly report (Mondays)"""
        return datetime.now().weekday() == 0  # Monday is 0
    
    def should_send_monthly_report(self):
        """Check if it's time to send monthly report (1st of month)"""
        return datetime.now().day == 1
    
    def run_scheduled_reports(self):
        """Run scheduled weekly and monthly reports"""
        try:
            current_time = datetime.now()
            self.logger.info(f"Running scheduled reports check at {current_time}")
            
            # Check for weekly report (Mondays)
            if self.should_send_weekly_report():
                self.logger.info("Sending weekly report...")
                if self.admin_manager.send_weekly_report():
                    self.logger.info("Weekly report sent successfully")
                else:
                    self.logger.error("Failed to send weekly report")
            
            # Check for monthly report (1st of month)
            if self.should_send_monthly_report():
                self.logger.info("Sending monthly report...")
                if self.admin_manager.send_monthly_report():
                    self.logger.info("Monthly report sent successfully")
                else:
                    self.logger.error("Failed to send monthly report")
            
            # If neither condition is met
            if not (self.should_send_weekly_report() or self.should_send_monthly_report()):
                self.logger.info("No scheduled reports to send today")
                
        except Exception as e:
            self.logger.error(f"Error in scheduled reports: {e}")
    
    def force_weekly_report(self):
        """Force send weekly report regardless of schedule"""
        try:
            self.logger.info("Force sending weekly report...")
            if self.admin_manager.send_weekly_report():
                self.logger.info("Weekly report sent successfully")
                return True
            else:
                self.logger.error("Failed to send weekly report")
                return False
        except Exception as e:
            self.logger.error(f"Error sending weekly report: {e}")
            return False
    
    def force_monthly_report(self):
        """Force send monthly report regardless of schedule"""
        try:
            self.logger.info("Force sending monthly report...")
            if self.admin_manager.send_monthly_report():
                self.logger.info("Monthly report sent successfully")
                return True
            else:
                self.logger.error("Failed to send monthly report")
                return False
        except Exception as e:
            self.logger.error(f"Error sending monthly report: {e}")
            return False

if __name__ == "__main__":
    reporter = AutomatedReports()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "weekly":
            reporter.force_weekly_report()
        elif command == "monthly":
            reporter.force_monthly_report()
        elif command == "check":
            reporter.run_scheduled_reports()
        else:
            print("Usage: python automated_reports.py [weekly|monthly|check]")
            print("  weekly  - Force send weekly report")
            print("  monthly - Force send monthly report")
            print("  check   - Run scheduled check (normal operation)")
    else:
        # Default behavior - run scheduled check
        reporter.run_scheduled_reports()