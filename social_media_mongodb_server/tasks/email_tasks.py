# social_media_mongodb_server/tasks/email_tasks.py
"""
Celery app for email tasks.

Usage:
  celery -A social_media_mongodb_server.tasks.email_tasks.celery_app worker --loglevel=info
"""

import os
from celery import Celery
from celery.utils.log import get_task_logger
from typing import Optional
from dotenv import load_dotenv

# load .env for local dev
load_dotenv = None
try:
    from dotenv import load_dotenv as _ld
    _ld()
    load_dotenv = _ld
except Exception:
    pass

logger = get_task_logger(__name__)

CELERY_BROKER = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND = os.getenv("CELERY_RESULT_BACKEND", os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"))

celery_app = Celery(
    "social_media_email_tasks",
    broker=CELERY_BROKER,
    backend=CELERY_BACKEND,
)

# Optional: configure Celery defaults (adjust as needed)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,
    worker_concurrency=4,
    task_time_limit=60,  # seconds
)

# Import the actual (blocking) send function
from ..utils.sendgrid_utils import send_email_sync  # blocking
# Fallback to a sane local path if env not present
DEFAULT_ATTACHMENT = os.getenv(
    "UPLOADED_FILE_PATH",
    "/mnt/data/99122be6-e5c4-4dd5-bcdb-804c3d8e3f53.png"
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def send_comment_notification(self, to_email: str, subject: str, html_content: str, plain_text: Optional[str] = None, attachment_path: Optional[str] = None):
    """
    Celery task to send an email via SendGrid synchronously (inside worker).
    Retries a few times on exception.
    """
    try:
        # If no attachment specified, use default dev path if exists.
        att = attachment_path or DEFAULT_ATTACHMENT
        logger.info("Sending email to %s (attachment=%s)", to_email, att)
        status, body = send_email_sync(to_email, subject, html_content, plain_text, att)
        logger.info("SendGrid response: %s", status)
        return {"status": status, "body": str(body)}
    except Exception as exc:
        logger.exception("Failed to send email to %s: %s", to_email, exc)
        # Retry on transient errors
        try:
            raise self.retry(exc=exc)
        except Exception:
            # If retry fails (max retries reached), propagate the error to result backend for inspection
            raise
