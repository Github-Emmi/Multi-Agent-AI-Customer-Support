"""
Email service — password reset and notification emails.
Uses aiosmtplib for async sending via Gmail SMTP.
Falls back to dev mode (prints to console) if SMTP is not configured.
"""
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import settings

logger = logging.getLogger(__name__)


async def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """Send a password reset link to the customer's email address."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    subject = "TechMart Electronics — Password Reset Request"
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1e293b; max-width: 520px; margin: auto;">
        <div style="background: #1d4ed8; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
          <h1 style="color: white; margin: 0; font-size: 20px;">TechMart Electronics</h1>
        </div>
        <div style="padding: 24px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px;">
          <h2 style="font-size: 18px;">Password Reset Request</h2>
          <p>We received a request to reset the password for your TechMart account.</p>
          <p>Click the button below to set a new password. This link is valid for <strong>1 hour</strong>.</p>
          <div style="text-align: center; margin: 28px 0;">
            <a href="{reset_url}"
               style="background: #2563eb; color: white; padding: 12px 28px;
                      border-radius: 8px; text-decoration: none; font-weight: bold;">
              Reset My Password
            </a>
          </div>
          <p style="font-size: 13px; color: #64748b;">
            If you didn't request this, you can safely ignore this email.
            Your password will not change.
          </p>
          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
          <p style="font-size: 12px; color: #94a3b8; text-align: center;">
            TechMart Electronics &mdash; support@techmart.com
          </p>
        </div>
      </body>
    </html>
    """

    if not settings.SMTP_USER or not settings.SMTP_PASS:
        logger.warning(
            f"[EMAIL - DEV] Password reset for {to_email}. "
            f"Reset URL: {reset_url}"
        )
        return True  # Dev mode — pretend it was sent

    try:
        import aiosmtplib

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"TechMart Support <{settings.SMTP_USER}>"
        message["To"] = to_email
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            start_tls=True,
        )
        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        return False


async def send_ticket_confirmation_email(
    to_email: str, ticket_id: str, subject: str
) -> bool:
    """Notify the customer that a support ticket has been created."""
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1e293b; max-width: 520px; margin: auto;">
        <div style="background: #1d4ed8; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
          <h1 style="color: white; margin: 0; font-size: 20px;">TechMart Electronics</h1>
        </div>
        <div style="padding: 24px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px;">
          <h2 style="font-size: 18px;">Support Ticket Created</h2>
          <p>Your support ticket has been created and assigned to our team.</p>
          <table style="width: 100%; background: #f8fafc; border-radius: 6px; padding: 12px; border: 1px solid #e2e8f0;">
            <tr><td style="font-size: 13px; color: #64748b; padding: 4px 0;">Ticket ID</td>
                <td style="font-weight: bold; font-size: 14px;">{ticket_id}</td></tr>
            <tr><td style="font-size: 13px; color: #64748b; padding: 4px 0;">Subject</td>
                <td style="font-size: 13px;">{subject}</td></tr>
          </table>
          <p style="margin-top: 16px; font-size: 13px; color: #475569;">
            A TechMart agent will respond within <strong>24 hours</strong>.
            You can reply to this email to add more information.
          </p>
          <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
          <p style="font-size: 12px; color: #94a3b8; text-align: center;">
            TechMart Electronics &mdash; support@techmart.com
          </p>
        </div>
      </body>
    </html>
    """

    if not settings.SMTP_USER or not settings.SMTP_PASS:
        logger.warning(f"[EMAIL - DEV] Ticket {ticket_id} confirmation for {to_email}")
        return True

    try:
        import aiosmtplib

        message = MIMEMultipart("alternative")
        message["Subject"] = f"[{ticket_id}] TechMart Support Ticket Created"
        message["From"] = f"TechMart Support <{settings.SMTP_USER}>"
        message["To"] = to_email
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            start_tls=True,
        )
        return True
    except Exception as exc:
        logger.error(f"Failed to send ticket email to {to_email}: {exc}")
        return False
