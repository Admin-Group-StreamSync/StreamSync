"""
Analytics Email Service Module.

Handles email construction and transmission using standard smtplib.
Sends analytics reports with PDF attachments to platform managers.
"""
import logging
import os
import smtplib
import threading
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_report_email(platform_name, recipient_email, pdf_bytes, filename=None):
    """
    Send platform report PDF via SMTP using smtplib.

    Args:
        platform_name (str): The name of the platform (e.g. 'CinePlus').
        recipient_email (str): The recipient's email address.
        pdf_bytes (bytes): The compiled PDF report as bytes.
        filename (str, optional): Custom filename for the PDF attachment.

    Raises:
        ValueError: If SMTP credentials are not configured.
        Exception: If SMTP connection or email sending fails.
    """
    smtp_host = os.getenv('SMTP_HOSTNAME', 'smtp.gmail.com')
    smtp_port_str = os.getenv('SMTP_TSL_PORT', '587')
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASSWORD')

    if not smtp_user or not smtp_pass:
        logger.error("SMTP credentials (SMTP_USER/SMTP_PASSWORD) are not set in the environment variables.")
        raise ValueError("SMTP credentials are not configured in environment variables.")

    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        logger.warning(f"Invalid SMTP port '{smtp_port_str}', defaulting to 587.")
        smtp_port = 587

    logger.info(f"Constructing email for {recipient_email} regarding platform {platform_name}...")
    # Build MIME Message
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = f"Reporte Estadístico - {platform_name}"

    body = f"""Hola,

        Adjunto encontrarás el reporte estadístico de analíticas de la plataforma {platform_name} en formato PDF.

        Este es un envío automático generado por StreamSync.

        Saludos cordiales,
        El equipo de StreamSync.
    """
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Attach PDF if bytes are provided
    if pdf_bytes:
        if not filename:
            filename = f"reporte_dashboard_{platform_name}.pdf"
        
        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(attachment)

    # Send via SMTP
    try:
        logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port}...")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        server.starttls()
        logger.info("SMTP connection established. Logging in...")
        server.login(smtp_user, smtp_pass)
        
        logger.info(f"Sending email to {recipient_email}...")
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {recipient_email} for platform {platform_name}.")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email} via SMTP: {str(e)}")
        raise


def send_report_email_async(platform_name, recipient_email, pdf_bytes, filename=None):
    """
    Wrapper to send the platform report email in a background thread to prevent blocking.

    Args:
        platform_name (str): The name of the platform.
        recipient_email (str): The recipient's email address.
        pdf_bytes (bytes): The compiled PDF report as bytes.
        filename (str, optional): Custom filename for the PDF attachment.
    """
    thread = threading.Thread(
        target=send_report_email,
        args=(platform_name, recipient_email, pdf_bytes, filename),
        daemon=True
    )
    thread.start()
    logger.info(f"Started background email sending thread to {recipient_email} for platform {platform_name}.")
