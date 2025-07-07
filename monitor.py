#!/usr/bin/env python3

import time
import sys
import os
from datetime import datetime, timedelta
from utils.logger import Logger
from utils.csv_handler import CSVHandler
from scripts.step3_prechecks import PreCheckHandler
from scripts.step4_scheduler import PatchScheduler
from config.settings import Config

class PatchingMonitor:
    def __init__(self):
        self.logger = Logger('monitor')
        self.csv_handler = CSVHandler()
        self.precheck_handler = PreCheckHandler()
        self.scheduler = PatchScheduler()
        
    def run_monitor(self):
        """Continuous monitoring loop"""
        self.logger.info("Starting patching monitor...")
        
        while True:
            try:
                current_quarter = Config.get_current_quarter()
                
                # Run pre-checks for servers due in next 5 hours
                self.precheck_handler.run_prechecks(current_quarter)
                
                # Schedule patches for servers due in next 3 hours
                self.scheduler.schedule_patches(current_quarter)
                
                # Sleep for 15 minutes
                time.sleep(900)
                
            except KeyboardInterrupt:
                self.logger.info("Monitor stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                time.sleep(60)  # Sleep 1 minute on error

if __name__ == "__main__":
    monitor = PatchingMonitor()
    monitor.run_monitor()
