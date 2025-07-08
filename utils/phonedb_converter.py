# utils/phonedb_converter.py
import subprocess
import re
import logging
from typing import Optional, Dict, List
from utils.logger import Logger

class PhonedbConverter:
    """
    Convert email addresses to Linux usernames using phonedb command
    """
    
    def __init__(self):
        self.logger = Logger('phonedb_converter')
        self._username_cache = {}  # Cache for performance
        
    def email_to_username(self, email: str) -> Optional[str]:
        """
        Convert email address to Linux username using phonedb
        
        Args:
            email: Email address (e.g., firstname.lastname@company.com)
            
        Returns:
            Linux username or None if not found
        """
        if not email or '@' not in email:
            return None
            
        # Check cache first
        if email in self._username_cache:
            return self._username_cache[email]
        
        try:
            # Extract the part before @ for phonedb lookup
            email_prefix = email.split('@')[0]
            
            # Run phonedb command: phonedb firstname.lastname | tail -1 | awk '{print $NF}'
            cmd = f"phonedb {email_prefix} | tail -1 | awk '{{print $NF}}'"
            
            self.logger.debug(f"Running phonedb command for {email}: {cmd}")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                username = result.stdout.strip()
                
                # Validate username format (alphanumeric + dots/hyphens)
                if self._is_valid_username(username):
                    self._username_cache[email] = username
                    self.logger.info(f"Converted {email} -> {username}")
                    return username
                else:
                    self.logger.warning(f"Invalid username format from phonedb: {username}")
                    return None
            else:
                self.logger.warning(f"Phonedb lookup failed for {email}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Phonedb command timeout for {email}")
            return None
        except Exception as e:
            self.logger.error(f"Error converting {email} to username: {e}")
            return None
    
    def _is_valid_username(self, username: str) -> bool:
        """
        Validate Linux username format
        """
        if not username:
            return False
            
        # Linux username validation: alphanumeric, dots, hyphens, underscores
        # Must start with letter or underscore
        pattern = r'^[a-zA-Z_][a-zA-Z0-9._-]*$'
        return bool(re.match(pattern, username)) and len(username) <= 32
    
    def bulk_convert_emails(self, emails: List[str]) -> Dict[str, Optional[str]]:
        """
        Convert multiple email addresses to usernames
        
        Args:
            emails: List of email addresses
            
        Returns:
            Dictionary mapping email -> username (or None if not found)
        """
        results = {}
        
        for email in emails:
            if email and email.strip():
                username = self.email_to_username(email.strip())
                results[email] = username
            else:
                results[email] = None
                
        return results
    
    def test_phonedb_availability(self) -> bool:
        """
        Test if phonedb command is available
        """
        try:
            result = subprocess.run(
                ['which', 'phonedb'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.logger.info("Phonedb command is available")
                return True
            else:
                self.logger.warning("Phonedb command not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing phonedb availability: {e}")
            return False
    
    def clear_cache(self):
        """Clear the username cache"""
        self._username_cache.clear()
        self.logger.info("Username cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'cached_entries': len(self._username_cache),
            'cache_size_bytes': sum(len(k) + len(v or '') for k, v in self._username_cache.items())
        }
    
    def manual_username_mapping(self, email: str, username: str):
        """
        Manually add email -> username mapping (for testing or overrides)
        """
        if self._is_valid_username(username):
            self._username_cache[email] = username
            self.logger.info(f"Manual mapping added: {email} -> {username}")
        else:
            self.logger.error(f"Invalid username format: {username}")
    
    def validate_email_format(self, email: str) -> bool:
        """
        Validate email format before conversion
        """
        if not email:
            return False
            
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def get_domain_from_email(self, email: str) -> Optional[str]:
        """
        Extract domain from email address
        """
        if not email or '@' not in email:
            return None
        return email.split('@')[1]
    
    def is_company_email(self, email: str, company_domains: List[str] = None) -> bool:
        """
        Check if email belongs to company domains
        """
        if not company_domains:
            company_domains = ['company.com', 'corp.company.com']
            
        domain = self.get_domain_from_email(email)
        return domain in company_domains if domain else False