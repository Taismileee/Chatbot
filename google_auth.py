# google_auth.py
import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_service_account_email():
    """Read client_email from JSON file for debug."""
    try:
        with open(SERVICE_ACCOUNT_FILE, "r", encoding="utf-8") as f:
            j = json.load(f)
            return j.get("client_email")
    except Exception as e:
        logger.exception("Không đọc được service account JSON: %s", SERVICE_ACCOUNT_FILE)
        return None

def get_calendar_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")

    client_email = get_service_account_email()
    logger.info("Using service account: %s", client_email)

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=creds)
    return service

def create_event(summary, description, start_time_iso, end_time_iso, calendar_id="primary", timezone="Asia/Ho_Chi_Minh"):
    """
    start_time_iso / end_time_iso should be strings like '2025-10-01T10:00:00' (no timezone required
    because we pass 'timeZone' in the event).
    Returns event htmlLink on success, raises Exception on failure with detailed info.
    """
    service = None
    try:
        service = get_calendar_service()
    except Exception as e:
        logger.exception("Lỗi khi khởi tạo Google Calendar service")
        raise

    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time_iso, "timeZone": timezone},
        "end": {"dateTime": end_time_iso, "timeZone": timezone},
    }

    logger.info("Tạo event: calendar_id=%s, body=%s", calendar_id, event_body)
    try:
        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        logger.info("Event created: %s", event.get("htmlLink"))
        return event.get("htmlLink")
    except HttpError as e:
        # Google API error -> include status and content for debugging
        content = None
        try:
            content = e.content.decode() if hasattr(e, 'content') else str(e)
        except Exception:
            content = str(e)
        logger.exception("Google API HttpError: status=%s content=%s", getattr(e, "status_code", "N/A"), content)
        raise Exception(f"Google API HttpError: status={getattr(e,'status_code','N/A')} content={content}") from e
    except Exception as e:
        logger.exception("Lỗi khi gọi Calendar API")
        raise
