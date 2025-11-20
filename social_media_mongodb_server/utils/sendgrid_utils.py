# social_media_mongodb_server/utils/sendgrid_utils.py
"""
Blocking SendGrid helper. It is intentionally synchronous because
the official sendgrid client is sync; callers should run this in a thread
(e.g. asyncio.to_thread) to avoid blocking the event loop.
"""

import os
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
from base64 import b64encode
from dotenv import load_dotenv

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Notifier")

if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
    # We don't raise at import time to avoid breaking tests; caller should handle missing config.
    pass

def send_email_sync(to_email: str, subject: str, html_content: str, plain_text: Optional[str] = None, attachment_path: Optional[str] = None):
    """
    Sends an email synchronously via SendGrid.
    - to_email: recipient email address
    - subject: email subject
    - html_content: HTML body
    - plain_text: optional plain text fallback
    - attachment_path: optional local path to attach to the email (string path)
    """
    if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
        # not configured - do nothing (or optionally log)
        raise RuntimeError("SendGrid not configured. Set SENDGRID_API_KEY and SENDGRID_FROM_EMAIL in environment.")

    message = Mail(
        from_email=(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )
    if plain_text:
        message.add_content(Content("text/plain", plain_text))

    # Attach local file if present
    if attachment_path:
        try:
            with open(attachment_path, "rb") as f:
                data = f.read()
            encoded = b64encode(data).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(encoded)
            # file name from path
            attachment.file_name = FileName(attachment_path.split("/")[-1])
            # best-effort mime-type; leave as octet-stream if unknown
            attachment.file_type = FileType("application/octet-stream")
            attachment.disposition = Disposition("attachment")
            message.attachment = attachment
        except Exception:
            # ignore errors attaching file; do not fail the whole send
            pass

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        # optionally return response status and body
        return response.status_code, getattr(response, "body", None)
    except Exception as e:
        # Bubble up error to caller if you want to handle it; in the service we'll swallow/log
        raise
