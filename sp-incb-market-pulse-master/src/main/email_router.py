"""
Email API Endpoints
Manage email configuration and send reports
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr
import email_service
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["Email"])


class SMTPConfig(BaseModel):
    """SMTP configuration"""
    host: str
    port: int = 587
    use_tls: bool = True
    username: str
    password: Optional[str] = None  # Optional to allow partial updates
    from_email: EmailStr
    from_name: str = "Market Pulse System"


class EmailRecipients(BaseModel):
    """Email recipients"""
    to_emails: List[EmailStr]
    cc_emails: Optional[List[EmailStr]] = []
    bcc_emails: Optional[List[EmailStr]] = []


class EmailTemplates(BaseModel):
    """Email templates"""
    subject: str
    body_html: str
    body_text: Optional[str] = ""


class EmailSettings(BaseModel):
    """Email behavior settings"""
    is_active: bool = False
    send_on_automation: bool = False
    send_on_manual_upload: bool = False
    attach_output_file: bool = True
    attach_excluded_file: bool = False


class EmailConfigUpdate(BaseModel):
    """Update email configuration"""
    smtp_config: Optional[SMTPConfig] = None
    recipients: Optional[EmailRecipients] = None
    templates: Optional[EmailTemplates] = None
    settings: Optional[EmailSettings] = None


class SendEmailRequest(BaseModel):
    """Manual email send request"""
    to_emails: Optional[List[EmailStr]] = None  # If None, use config
    subject: Optional[str] = None
    body: Optional[str] = None
    attach_output_file: bool = True


@router.get("/config")
async def get_email_configuration():
    """
    Get current email configuration (password masked)
    
    Returns:
        {
            "smtp_config": {...},
            "recipients": {...},
            "templates": {...},
            "settings": {...}
        }
    """
    try:
        config = email_service.get_email_config()
        return config
    except Exception as e:
        logger.error(f"Error getting email config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_email_configuration(config_update: EmailConfigUpdate):
    """
    Update email configuration
    
    Args:
        config_update: Configuration updates
    
    Returns:
        Updated configuration
    """
    try:
        config_data = config_update.model_dump(exclude_none=True)
        updated_config = email_service.update_email_config(config_data, updated_by="admin")
        
        return {
            "message": "Email configuration updated successfully",
            "config": updated_config
        }
    except Exception as e:
        logger.error(f"Error updating email config: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test")
async def test_email_configuration():
    """
    Test SMTP connection with current configuration
    
    Returns:
        {
            "success": true/false,
            "message": "Connection status"
        }
    """
    try:
        result = email_service.test_email_connection()
        return result
    except Exception as e:
        logger.error(f"Error testing email config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_manual_email(request: SendEmailRequest):
    """
    Send manual email report
    
    Args:
        request: Email send parameters
    
    Returns:
        {
            "success": true/false,
            "message": "Send status"
        }
    """
    try:
        config = email_service.load_email_config()
        
        # Use configured recipients if not specified
        to_emails = request.to_emails or config.get('recipients', {}).get('to_emails', [])
        
        if not to_emails:
            raise HTTPException(
                status_code=400,
                detail="No recipient email addresses specified or configured"
            )
        
        # Use configured template if not specified
        templates = config.get('templates', {})
        subject = request.subject or templates.get('subject', 'Market Pulse Report')
        body_html = request.body or templates.get('body_html', '')
        body_text = templates.get('body_text', '')
        
        # Prepare attachments
        attachment_paths = []
        if request.attach_output_file:
            output_file = os.path.join(
                os.path.dirname(__file__),
                'Processed_Colors_Output.xlsx'
            )
            if os.path.exists(output_file):
                attachment_paths.append(output_file)
        
        # Send email
        result = email_service.send_email(
            to_emails=to_emails,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            attachment_paths=attachment_paths,
            sent_by="admin"
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('message'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_email_logs(limit: int = 50):
    """
    Get email send history
    
    Args:
        limit: Maximum number of logs to return (default 50)
    
    Returns:
        {
            "logs": [...],
            "count": 10
        }
    """
    try:
        logs = email_service.get_email_logs(limit)
        return {
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting email logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-report")
async def send_automation_report(report_data: Dict):
    """
    Send automated report email (called by cron automation)
    
    Args:
        report_data: Report variables for template rendering
    
    Returns:
        {
            "success": true/false,
            "message": "Send status"
        }
    """
    try:
        config = email_service.load_email_config()
        settings = config.get('settings', {})
        
        # Check if email sending on automation is enabled
        if not settings.get('send_on_automation', False):
            return {
                "success": False,
                "message": "Email sending on automation is disabled"
            }
        
        # Prepare attachments
        attachment_paths = []
        
        if settings.get('attach_output_file', True):
            output_file = os.path.join(
                os.path.dirname(__file__),
                'Processed_Colors_Output.xlsx'
            )
            if os.path.exists(output_file):
                attachment_paths.append(output_file)
        
        # Send report
        result = email_service.send_report_email(
            report_data=report_data,
            attachment_paths=attachment_paths
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending automation report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
