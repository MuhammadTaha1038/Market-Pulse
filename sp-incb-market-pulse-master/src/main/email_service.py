"""
Email Service - SMTP Email Functionality
Handles sending email reports with configurable SMTP settings
"""

import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
EMAIL_CONFIG_FILE = os.path.join(DATA_DIR, 'email_config.json')
EMAIL_LOGS_FILE = os.path.join(DATA_DIR, 'email_logs.json')


def load_email_config() -> Dict:
    """Load email configuration from JSON file"""
    if not os.path.exists(EMAIL_CONFIG_FILE):
        return create_default_config()
    
    try:
        with open(EMAIL_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading email config: {e}")
        return create_default_config()


def save_email_config(config: Dict) -> None:
    """Save email configuration to JSON file"""
    os.makedirs(DATA_DIR, exist_ok=True)
    config['updated_at'] = datetime.now().isoformat()
    
    with open(EMAIL_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def create_default_config() -> Dict:
    """Create default email configuration"""
    return {
        "smtp_config": {
            "host": "",
            "port": 587,
            "use_tls": True,
            "username": "",
            "password": "",
            "from_email": "",
            "from_name": "Market Pulse System"
        },
        "recipients": {
            "to_emails": [],
            "cc_emails": [],
            "bcc_emails": []
        },
        "templates": {
            "subject": "Market Pulse Report - {{date}}",
            "body_html": "<html><body><h2>Market Pulse Processing Report</h2></body></html>",
            "body_text": "Market Pulse Processing Report"
        },
        "settings": {
            "is_active": False,
            "send_on_automation": False,
            "send_on_manual_upload": False,
            "attach_output_file": True,
            "attach_excluded_file": False
        },
        "updated_at": None,
        "updated_by": "system"
    }


def get_email_config() -> Dict:
    """Get email configuration (safe for API response - no password)"""
    config = load_email_config()
    
    # Remove sensitive data for API response
    safe_config = config.copy()
    if 'smtp_config' in safe_config:
        smtp = safe_config['smtp_config'].copy()
        smtp['password'] = '***' if smtp.get('password') else ''
        safe_config['smtp_config'] = smtp
    
    return safe_config


def update_email_config(config_data: Dict, updated_by: str = "admin") -> Dict:
    """
    Update email configuration
    
    Args:
        config_data: New configuration data
        updated_by: User who updated the config
    
    Returns:
        Updated configuration
    """
    current_config = load_email_config()
    
    # Update SMTP config
    if 'smtp_config' in config_data:
        current_config['smtp_config'].update(config_data['smtp_config'])
    
    # Update recipients
    if 'recipients' in config_data:
        current_config['recipients'].update(config_data['recipients'])
    
    # Update templates
    if 'templates' in config_data:
        current_config['templates'].update(config_data['templates'])
    
    # Update settings
    if 'settings' in config_data:
        current_config['settings'].update(config_data['settings'])
    
    current_config['updated_by'] = updated_by
    save_email_config(current_config)
    
    return get_email_config()


def render_template(template: str, variables: Dict) -> str:
    """
    Simple template rendering (replace {{variable}} with values)
    
    Args:
        template: Template string with {{variable}} placeholders
        variables: Dict of variable name -> value
    
    Returns:
        Rendered template string
    """
    result = template
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    return result


def send_email(
    to_emails: List[str],
    subject: str,
    body_html: str,
    body_text: str = "",
    cc_emails: List[str] = None,
    bcc_emails: List[str] = None,
    attachment_paths: List[str] = None,
    sent_by: str = "system"
) -> Dict:
    """
    Send email using configured SMTP settings
    
    Args:
        to_emails: List of recipient email addresses
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (fallback)
        cc_emails: CC recipients
        bcc_emails: BCC recipients
        attachment_paths: List of file paths to attach
        sent_by: User/system sending the email
    
    Returns:
        Dict with status and message
    """
    config = load_email_config()
    smtp_config = config.get('smtp_config', {})
    
    # Validate configuration
    if not smtp_config.get('host') or not smtp_config.get('username'):
        log_email_attempt(to_emails, subject, 'failed', 'SMTP configuration incomplete', sent_by)
        return {
            "success": False,
            "message": "Email configuration is incomplete. Please configure SMTP settings first."
        }
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{smtp_config.get('from_name', 'Market Pulse')} <{smtp_config.get('from_email')}>"
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)
        
        # Attach body parts
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))
        
        # Attach files
        if attachment_paths:
            for file_path in attachment_paths:
                if os.path.exists(file_path):
                    attach_file(msg, file_path)
        
        # Combine all recipients
        all_recipients = to_emails.copy()
        if cc_emails:
            all_recipients.extend(cc_emails)
        if bcc_emails:
            all_recipients.extend(bcc_emails)
        
        # Send email
        server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        server.set_debuglevel(0)
        
        if smtp_config.get('use_tls', True):
            server.starttls()
        
        server.login(smtp_config['username'], smtp_config['password'])
        server.send_message(msg)
        server.quit()
        
        # Log success
        log_email_attempt(
            to_emails,
            subject,
            'sent',
            f"Email sent successfully to {len(all_recipients)} recipient(s)",
            sent_by,
            attachment_paths
        )
        
        logger.info(f"✅ Email sent successfully to {len(all_recipients)} recipient(s)")
        
        return {
            "success": True,
            "message": f"Email sent successfully to {len(all_recipients)} recipient(s)"
        }
        
    except smtplib.SMTPAuthenticationError:
        error_msg = "SMTP authentication failed. Please check username and password."
        log_email_attempt(to_emails, subject, 'failed', error_msg, sent_by)
        logger.error(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        log_email_attempt(to_emails, subject, 'failed', error_msg, sent_by)
        logger.error(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}
        
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        log_email_attempt(to_emails, subject, 'failed', error_msg, sent_by)
        logger.error(f"❌ {error_msg}")
        return {"success": False, "message": error_msg}


def attach_file(msg: MIMEMultipart, file_path: str):
    """
    Attach file to email message
    
    Args:
        msg: Email message object
        file_path: Path to file to attach
    """
    try:
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={filename}'
            )
            msg.attach(part)
    except Exception as e:
        logger.error(f"Failed to attach file {file_path}: {e}")


def test_email_connection() -> Dict:
    """
    Test SMTP connection and configuration
    
    Returns:
        Dict with success status and message
    """
    config = load_email_config()
    smtp_config = config.get('smtp_config', {})
    
    if not smtp_config.get('host') or not smtp_config.get('username'):
        return {
            "success": False,
            "message": "SMTP configuration incomplete"
        }
    
    try:
        server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        server.set_debuglevel(0)
        
        if smtp_config.get('use_tls', True):
            server.starttls()
        
        server.login(smtp_config['username'], smtp_config['password'])
        server.quit()
        
        return {
            "success": True,
            "message": "SMTP connection successful"
        }
        
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": "SMTP authentication failed. Check username/password."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }


def send_report_email(
    report_data: Dict,
    attachment_paths: List[str] = None
) -> Dict:
    """
    Send automated report email with configured templates
    
    Args:
        report_data: Dict containing report variables (date, time, total_processed, etc.)
        attachment_paths: Optional list of file paths to attach
    
    Returns:
        Dict with success status and message
    """
    config = load_email_config()
    
    # Check if email is active
    if not config.get('settings', {}).get('is_active', False):
        return {
            "success": False,
            "message": "Email functionality is disabled"
        }
    
    recipients = config.get('recipients', {})
    to_emails = recipients.get('to_emails', [])
    
    if not to_emails:
        return {
            "success": False,
            "message": "No recipient email addresses configured"
        }
    
    # Render templates
    templates = config.get('templates', {})
    subject = render_template(templates.get('subject', 'Market Pulse Report'), report_data)
    body_html = render_template(templates.get('body_html', ''), report_data)
    body_text = render_template(templates.get('body_text', ''), report_data)
    
    # Send email
    return send_email(
        to_emails=to_emails,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        cc_emails=recipients.get('cc_emails', []),
        bcc_emails=recipients.get('bcc_emails', []),
        attachment_paths=attachment_paths,
        sent_by="automation"
    )


def log_email_attempt(
    to_emails: List[str],
    subject: str,
    status: str,
    message: str = "",
    sent_by: str = "system",
    attachment_paths: List[str] = None
):
    """
    Log email send attempt
    
    Args:
        to_emails: Recipient email addresses
        subject: Email subject
        status: 'sent', 'failed', 'pending'
        message: Status message or error
        sent_by: User/system that sent the email
        attachment_paths: Attached files
    """
    try:
        # Load existing logs
        if os.path.exists(EMAIL_LOGS_FILE):
            with open(EMAIL_LOGS_FILE, 'r', encoding='utf-8') as f:
                logs_data = json.load(f)
        else:
            logs_data = {"logs": [], "next_id": 1}
        
        # Create log entry
        log_entry = {
            "id": logs_data['next_id'],
            "to_emails": to_emails,
            "subject": subject,
            "status": status,
            "message": message,
            "sent_by": sent_by,
            "sent_at": datetime.now().isoformat(),
            "attachments": [os.path.basename(p) for p in (attachment_paths or [])]
        }
        
        logs_data['logs'].insert(0, log_entry)  # Most recent first
        logs_data['next_id'] += 1
        
        # Keep only last 100 logs
        logs_data['logs'] = logs_data['logs'][:100]
        
        # Save logs
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(EMAIL_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to log email attempt: {e}")


def get_email_logs(limit: int = 50) -> List[Dict]:
    """
    Get email send logs
    
    Args:
        limit: Maximum number of logs to return
    
    Returns:
        List of email log entries
    """
    if not os.path.exists(EMAIL_LOGS_FILE):
        return []
    
    try:
        with open(EMAIL_LOGS_FILE, 'r', encoding='utf-8') as f:
            logs_data = json.load(f)
        return logs_data.get('logs', [])[:limit]
    except Exception as e:
        logger.error(f"Error loading email logs: {e}")
        return []
