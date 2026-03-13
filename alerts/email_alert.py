"""
alerts/email_alert.py
=====================
Async SMTP Email notifier.
"""

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional
import mimetypes
import asyncio
from concurrent.futures import ThreadPoolExecutor

import config

logger = logging.getLogger(__name__)

# Run slow SMTP blocking operations inside a thread pool
_executor = ThreadPoolExecutor(max_workers=2)

class EmailNotifier:
    @staticmethod
    async def send(subject: str, message: str, image_path: Optional[str] = None):
        if not config.EMAIL_ENABLED:
            return

        if not all([config.EMAIL_FROM, config.EMAIL_PASSWORD, config.EMAIL_TO]):
            logger.error("[Email] Enabled but credentials missing.")
            return

        loop = asyncio.get_running_loop()
        # Non-blocking SMTP handoff
        await loop.run_in_executor(
            _executor, 
            EmailNotifier._send_sync, 
            subject, message, image_path
        )

    @staticmethod
    def _send_sync(subject: str, message: str, image_path: Optional[str]):
        msg = EmailMessage()
        msg["Subject"] = f"[CV Pro] {subject}"
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO
        msg.set_content(message)

        if image_path:
            try:
                with open(image_path, "rb") as f:
                    img_data = f.read()
                
                ctype, encoding = mimetypes.guess_type(image_path)
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"
                maintype, subtype = ctype.split("/", 1)
                
                msg.add_attachment(img_data, maintype=maintype, subtype=subtype, filename="alert.jpg")
            except Exception as e:
                logger.error("[Email] Failed to attach image: %s", e)

        try:
            with smtplib.SMTP(config.EMAIL_SMTP_HOST, config.EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
                server.send_message(msg)
            logger.debug("[Email] Alert sent successfully.")
        except Exception as e:
            logger.error("[Email] Exception sending alert: %s", e)
