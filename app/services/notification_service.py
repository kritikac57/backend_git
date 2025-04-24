# app/services/notification_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_ngo_notification(ngo_email: str, ngo_name: str, donation_id: int, donation_title: str, donor_name: str):
    """
    Send email notification to NGO when a donation is assigned to them
    """
    try:
        # Create email
        message = MIMEMultipart()
        message["From"] = settings.EMAIL_FROM
        message["To"] = ngo_email
        message["Subject"] = f"New Donation Assignment - {donation_title}"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>New Donation Assignment</h2>
            <p>Hello {ngo_name},</p>
            <p>A new donation has been assigned to your organization:</p>
            <ul>
                <li><strong>Donation ID:</strong> {donation_id}</li>
                <li><strong>Title:</strong> {donation_title}</li>
                <li><strong>Donor:</strong> {donor_name}</li>
            </ul>
            <p>Please log in to your account to view the details and contact the donor.</p>
            <p>Thank you for your valuable service!</p>
            <p>Best regards,<br>The DonationApp Team</p>
        </body>
        </html>
        """
        
        message.attach(MIMEText(body, "html"))
        
        # Connect to SMTP server and send email
        if settings.EMAIL_ENABLED:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                
                server.send_message(message)
                
            logger.info(f"Notification sent to NGO {ngo_name} (ID: {ngo_email}) for donation {donation_id}")
        else:
            # Log email content in development mode
            logger.info(f"Email notification would be sent to {ngo_email}")
            logger.info(f"Subject: {message['Subject']}")
            logger.info(f"Body: {body}")
            
    except Exception as e:
        logger.error(f"Failed to send notification to NGO: {str(e)}")