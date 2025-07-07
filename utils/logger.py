# utils/logger.py
import logging
import os
from datetime import datetime
from config.settings import Config

class Logger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
        if not self.logger.handlers:
            # Create logs directory if it doesn't exist
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            
            # Set up file handler
            log_file = os.path.join(Config.LOG_DIR, f"{name}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Set up console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Add handlers to logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.DEBUG)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def debug(self, message: str):
        self.logger.debug(message)
