# utils/email_sender.py
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import Config
from utils.logger import Logger

class EmailSender:
    def __init__(self):
        self.use_sendmail = Config.USE_SENDMAIL
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_use_tls = Config.SMTP_USE_TLS
        self.username = Config.SMTP_USERNAME
        self.password = Config.SMTP_PASSWORD
        self.logger = Logger('email_sender')
    
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email notification"""
        if self.use_sendmail:
            return self._send_email_sendmail(to_email, subject, body, is_html)
        else:
            return self._send_email_smtp(to_email, subject, body, is_html)
    
    def _send_email_sendmail(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email using sendmail command"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Find sendmail command (try common locations)
            sendmail_cmd = None
            for path in ['/usr/sbin/sendmail', '/usr/bin/sendmail', '/sbin/sendmail']:
                try:
                    subprocess.run([path, '-V'], capture_output=True, check=True, timeout=5)
                    sendmail_cmd = path
                    break
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            if not sendmail_cmd:
                raise Exception("sendmail command not found")
            
            # Use sendmail command
            process = subprocess.Popen(
                [sendmail_cmd, '-t'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=msg.as_string())
            
            if process.returncode == 0:
                self.logger.info(f"Email sent successfully to {to_email} via sendmail")
                return True
            else:
                self.logger.error(f"Sendmail failed for {to_email}: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send email via sendmail to {to_email}: {e}")
            return False
    
    def _send_email_smtp(self, to_email: str, subject: str, body: str, is_html: bool = False) -> bool:
        """Send email using SMTP server"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.smtp_use_tls:
                server.starttls()  # Enable security
            
            if self.password:  # Only login if password is provided
                server.login(self.username, self.password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.username, to_email, text)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
            return False
    
    def send_bulk_email(self, recipients: list, subject: str, body: str, is_html: bool = False) -> dict:
        """Send email to multiple recipients"""
        results = {'success': [], 'failed': []}
        
        for recipient in recipients:
            if self.send_email(recipient, subject, body, is_html):
                results['success'].append(recipient)
            else:
                results['failed'].append(recipient)
        
        return results
