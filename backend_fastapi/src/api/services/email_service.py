import logging
import smtplib
from email.mime.text import MIMEText
from typing import List

from ..core.config import settings

logger = logging.getLogger("email")


# PUBLIC_INTERFACE
def send_email(to: List[str], subject: str, body: str):
    """Send an email if EMAIL_ENABLED is True; logs otherwise."""
    if not settings.EMAIL_ENABLED:
        logger.info("EMAIL_ENABLED is false; would send to %s subject=%s", to, subject)
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = ", ".join(to)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, to, msg.as_string())
