"""
Email Sender Utility for Linux Patching Automation
Handles all email communications with rich formatting support
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading
import queue
import time
from pathlib import Path

from .logger import get_logger

class EmailSender:
    """Comprehensive email sender with queuing and retry capabilities"""
    
    def __init__(self, smtp_server: str, smtp_port: int = 587, 
                 use_tls: bool = True, use_ssl: bool = False,
                 username: str = '', password: str = '',
                 from_email: str = 'patching@company.com',
                 max_retries: int = 3, retry_delay: int = 60):
        """
        Initialize email sender
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            use_tls: Use TLS encryption
            use_ssl: Use SSL encryption
            username: SMTP username
            password: SMTP password
            from_email: From email address
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.username = username
        self.password = password
        self.from_email = from_email
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Email queue for async sending
        self.email_queue = queue.Queue()
        self.queue_worker_running = False
        self.queue_worker_thread = None
        
        # Statistics
        self.sent_count = 0
        self.failed_count = 0
        self.retry_count = 0
        
        # Logger
        self.logger = get_logger('email_sender')
        
        # Start queue worker
        self.start_queue_worker()
    
    def start_queue_worker(self):
        """Start background queue worker"""
        if not self.queue_worker_running:
            self.queue_worker_running = True
            self.queue_worker_thread = threading.Thread(target=self._queue_worker, daemon=True)
            self.queue_worker_thread.start()
            self.logger.info("Email queue worker started")
    
    def stop_queue_worker(self):
        """Stop background queue worker"""
        if self.queue_worker_running:
            self.queue_worker_running = False
            # Add sentinel to wake up worker
            self.email_queue.put(None)
            if self.queue_worker_thread:
                self.queue_worker_thread.join(timeout=5)
            self.logger.info("Email queue worker stopped")
    
    def _queue_worker(self):
        """Background worker to process email queue"""
        while self.queue_worker_running:
            try:
                # Get email from queue with timeout
                email_data = self.email_queue.get(timeout=5)
                
                # Check for sentinel
                if email_data is None:
                    break
                
                # Send email
                self._send_email_immediate(email_data)
                self.email_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Queue worker error: {e}")
                self.email_queue.task_done()
    
    def send_email(self, to: List[str], subject: str, body: str,
                   cc: List[str] = None, bcc: List[str] = None,
                   attachments: List[str] = None, is_html: bool = False,
                   priority: str = 'normal', async_send: bool = True) -> bool:
        """
        Send email with comprehensive options
        
        Args:
            to: List of recipient emails
            subject: Email subject
            body: Email body
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of file paths to attach
            is_html: Whether body is HTML
            priority: Email priority (low, normal, high)
            async_send: Send asynchronously via queue
            
        Returns:
            bool: True if queued/sent successfully
        """
        try:
            # Validate recipients
            if not to or not isinstance(to, list):
                self.logger.error("Invalid recipient list")
                return False
            
            # Clean up recipient lists
            to = [email.strip() for email in to if email.strip()]
            cc = [email.strip() for email in (cc or []) if email.strip()]
            bcc = [email.strip() for email in (bcc or []) if email.strip()]
            
            if not to:
                self.logger.error("No valid recipients")
                return False
            
            # Prepare email data
            email_data = {
                'to': to,
                'cc': cc,
                'bcc': bcc,
                'subject': subject,
                'body': body,
                'attachments': attachments or [],
                'is_html': is_html,
                'priority': priority,
                'timestamp': datetime.now().isoformat(),
                'retry_count': 0
            }
            
            if async_send:
                # Add to queue
                self.email_queue.put(email_data)
                self.logger.info(f"Email queued: {subject} to {len(to)} recipients")
                return True
            else:
                # Send immediately
                return self._send_email_immediate(email_data)
                
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def _send_email_immediate(self, email_data: Dict[str, Any]) -> bool:
        """Send email immediately with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                # Create message
                msg = self._create_message(email_data)
                
                # Send message
                if self._send_message(msg):
                    self.sent_count += 1
                    self.logger.info(f"Email sent successfully: {email_data['subject']} "
                                   f"to {len(email_data['to'])} recipients")
                    return True
                else:
                    raise Exception("Failed to send message")
                    
            except Exception as e:
                self.logger.error(f"Email send attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    self.retry_count += 1
                    self.logger.info(f"Retrying email send in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    self.failed_count += 1
                    self.logger.error(f"Email send failed after {self.max_retries + 1} attempts")
                    return False
        
        return False
    
    def _create_message(self, email_data: Dict[str, Any]) -> MIMEMultipart:
        """Create email message"""
        msg = MIMEMultipart()
        
        # Set headers
        msg['From'] = self.from_email
        msg['To'] = ', '.join(email_data['to'])
        msg['Subject'] = email_data['subject']
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        if email_data['cc']:
            msg['Cc'] = ', '.join(email_data['cc'])
        
        # Set priority
        priority_map = {
            'low': '5',
            'normal': '3',
            'high': '1'
        }
        msg['X-Priority'] = priority_map.get(email_data['priority'], '3')
        
        # Add custom headers
        msg['X-Mailer'] = 'Linux Patching Automation System'
        msg['X-Generated-By'] = 'Patching Engine v1.0'
        
        # Attach body
        if email_data['is_html']:
            msg.attach(MIMEText(email_data['body'], 'html'))
        else:
            msg.attach(MIMEText(email_data['body'], 'plain'))
        
        # Add attachments
        for attachment_path in email_data['attachments']:
            if os.path.exists(attachment_path):
                self._add_attachment(msg, attachment_path)
            else:
                self.logger.warning(f"Attachment not found: {attachment_path}")
        
        return msg
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add file attachment to message"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            # Get filename
            filename = os.path.basename(file_path)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            self.logger.debug(f"Added attachment: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to add attachment {file_path}: {e}")
    
    def _send_message(self, msg: MIMEMultipart) -> bool:
        """Send email message via SMTP"""
        try:
            # Create SMTP connection
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Login if credentials provided
            if self.username and self.password:
                server.login(self.username, self.password)
            
            # Get all recipients
            recipients = []
            recipients.extend(msg['To'].split(', '))
            if msg['Cc']:
                recipients.extend(msg['Cc'].split(', '))
            if msg['Bcc']:
                recipients.extend(msg['Bcc'].split(', '))
            
            # Send email
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP send failed: {e}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """Send test email to verify configuration"""
        subject = "Test Email - Linux Patching Automation"
        body = f"""
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email from the Linux Patching Automation System.</p>
            <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>From:</strong> {self.from_email}</p>
            <p><strong>SMTP Server:</strong> {self.smtp_server}:{self.smtp_port}</p>
            <p><strong>TLS:</strong> {self.use_tls}</p>
            <p><strong>SSL:</strong> {self.use_ssl}</p>
            <p>If you receive this email, the email configuration is working correctly.</p>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to_email],
            subject=subject,
            body=body,
            is_html=True,
            async_send=False
        )
    
    def send_bulk_email(self, recipients: List[str], subject: str, body: str,
                       is_html: bool = False, batch_size: int = 50) -> Dict[str, int]:
        """Send bulk email in batches"""
        results = {'sent': 0, 'failed': 0}
        
        # Split recipients into batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            
            try:
                if self.send_email(
                    to=batch,
                    subject=subject,
                    body=body,
                    is_html=is_html,
                    async_send=False
                ):
                    results['sent'] += len(batch)
                else:
                    results['failed'] += len(batch)
                    
                # Small delay between batches
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Bulk email batch failed: {e}")
                results['failed'] += len(batch)
        
        return results
    
    def send_notification(self, notification_type: str, data: Dict[str, Any],
                         recipients: List[str]) -> bool:
        """Send notification using templates"""
        try:
            from config.email_templates import EmailTemplates
            
            # Get template based on type
            if notification_type == 'precheck':
                email_data = EmailTemplates.precheck_notification(
                    data.get('servers', []),
                    data.get('quarter', 'Q1')
                )
            elif notification_type == 'patching_started':
                email_data = EmailTemplates.patching_started(
                    data.get('server', ''),
                    data.get('quarter', 'Q1'),
                    data.get('scheduled_time', '')
                )
            elif notification_type == 'patching_completed':
                email_data = EmailTemplates.patching_completed(data)
            elif notification_type == 'approval_request':
                email_data = EmailTemplates.approval_request(
                    data.get('servers', []),
                    data.get('quarter', 'Q1'),
                    data.get('requester', 'system')
                )
            elif notification_type == 'daily_summary':
                email_data = EmailTemplates.daily_summary(data)
            elif notification_type == 'quarterly_report':
                email_data = EmailTemplates.quarterly_report(
                    data.get('quarter', 'Q1'),
                    data
                )
            elif notification_type == 'critical_alert':
                email_data = EmailTemplates.critical_alert(
                    data.get('server', ''),
                    data.get('issue', ''),
                    data.get('details', '')
                )
            elif notification_type == 'rollback':
                email_data = EmailTemplates.rollback_notification(
                    data.get('server', ''),
                    data.get('reason', ''),
                    data.get('status', '')
                )
            else:
                self.logger.error(f"Unknown notification type: {notification_type}")
                return False
            
            return self.send_email(
                to=recipients,
                subject=email_data['subject'],
                body=email_data['body'],
                is_html=email_data['type'] == 'html',
                priority='high' if notification_type == 'critical_alert' else 'normal'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get email statistics"""
        return {
            'sent_count': self.sent_count,
            'failed_count': self.failed_count,
            'retry_count': self.retry_count,
            'queue_size': self.email_queue.qsize(),
            'success_rate': (self.sent_count / (self.sent_count + self.failed_count) * 100) 
                           if (self.sent_count + self.failed_count) > 0 else 0,
            'worker_running': self.queue_worker_running
        }
    
    def clear_queue(self):
        """Clear email queue"""
        try:
            while not self.email_queue.empty():
                self.email_queue.get_nowait()
                self.email_queue.task_done()
            self.logger.info("Email queue cleared")
        except queue.Empty:
            pass
    
    def wait_for_queue_completion(self, timeout: int = 300):
        """Wait for email queue to be processed"""
        try:
            self.email_queue.join()
            self.logger.info("Email queue processing completed")
        except Exception as e:
            self.logger.error(f"Error waiting for queue completion: {e}")
    
    def validate_email_address(self, email: str) -> bool:
        """Validate email address format"""
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_configuration(self) -> List[str]:
        """Validate email configuration"""
        issues = []
        
        if not self.smtp_server:
            issues.append("SMTP server not configured")
        
        if not self.from_email:
            issues.append("From email not configured")
        
        if not self.validate_email_address(self.from_email):
            issues.append("Invalid from email format")
        
        if self.smtp_port <= 0 or self.smtp_port > 65535:
            issues.append("Invalid SMTP port")
        
        if self.use_tls and self.use_ssl:
            issues.append("Cannot use both TLS and SSL")
        
        return issues
    
    def test_smtp_connection(self) -> Dict[str, Any]:
        """Test SMTP connection"""
        result = {
            'success': False,
            'message': '',
            'details': {}
        }
        
        try:
            # Test connection
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context, timeout=30)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Get server info
            result['details']['server_response'] = server.noop()[1].decode('utf-8')
            
            # Test authentication if credentials provided
            if self.username and self.password:
                server.login(self.username, self.password)
                result['details']['authentication'] = 'Success'
            else:
                result['details']['authentication'] = 'Not tested (no credentials)'
            
            server.quit()
            
            result['success'] = True
            result['message'] = 'SMTP connection successful'
            
        except Exception as e:
            result['success'] = False
            result['message'] = str(e)
            result['details']['error'] = str(e)
        
        return result
    
    def create_email_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Create email usage report"""
        # This would need to be implemented with actual data storage
        # For now, return current statistics
        return {
            'period': f"{start_date} to {end_date}",
            'statistics': self.get_statistics(),
            'generated_at': datetime.now().isoformat()
        }
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.stop_queue_worker()

# Utility functions
def create_email_sender(config=None) -> EmailSender:
    """Create email sender with configuration"""
    if config is None:
        from config.settings import Config
        config = Config()
    
    return EmailSender(
        smtp_server=config.SMTP_SERVER,
        smtp_port=config.SMTP_PORT,
        use_tls=config.SMTP_USE_TLS,
        use_ssl=config.SMTP_USE_SSL,
        username=config.SMTP_USERNAME,
        password=config.SMTP_PASSWORD,
        from_email=config.EMAIL_FROM
    )

def send_quick_email(to: str, subject: str, body: str, is_html: bool = False) -> bool:
    """Quick email sending function"""
    sender = create_email_sender()
    result = sender.send_email(
        to=[to],
        subject=subject,
        body=body,
        is_html=is_html,
        async_send=False
    )
    sender.stop_queue_worker()
    return result

# Example usage
if __name__ == "__main__":
    # Example of using the email sender
    sender = EmailSender(
        smtp_server='smtp.gmail.com',
        smtp_port=587,
        use_tls=True,
        username='your_email@gmail.com',
        password='your_app_password',
        from_email='your_email@gmail.com'
    )
    
    # Test configuration
    config_issues = sender.validate_configuration()
    if config_issues:
        print("Configuration issues:")
        for issue in config_issues:
            print(f"  - {issue}")
    
    # Test connection
    connection_test = sender.test_smtp_connection()
    print(f"Connection test: {connection_test}")
    
    # Send test email
    # success = sender.send_test_email('recipient@example.com')
    # print(f"Test email sent: {success}")
    
    # Get statistics
    stats = sender.get_statistics()
    print(f"Statistics: {stats}")
    
    # Clean up
    sender.stop_queue_worker()