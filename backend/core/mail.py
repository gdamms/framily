import logging
import smtplib
import ssl
from email.message import EmailMessage

from core.config import settings


logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email through the configured SMTP server.

    Raises RuntimeError if SMTP isn't configured; SMTP/network errors propagate.
    """
    if not settings.smtp_enabled:
        raise RuntimeError("SMTP is not configured (SMTP_HOST is empty).")

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM or settings.SMTP_USERNAME
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    security = settings.SMTP_SECURITY.lower()
    context = ssl.create_default_context()

    if security == "ssl":
        smtp = smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT, context=context,
        )
    else:
        smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT)

    with smtp:
        if security == "starttls":
            smtp.starttls(context=context)
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def send_email_safely(to: str, subject: str, body: str) -> None:
    """send_email for background tasks: logs failures instead of raising."""
    try:
        send_email(to, subject, body)
    except Exception:
        logger.exception("Failed to send email to %s", to)
