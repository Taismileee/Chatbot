# google_calendar.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "service_account.json"  # nhớ upload file này lên Railway

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=creds)
    return service

def add_event(summary, start_time, end_time, timezone="Asia/Ho_Chi_Minh"):
    service = get_calendar_service()
    event = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": timezone},
        "end": {"dateTime": end_time, "timeZone": timezone},
    }
    event = service.events().insert(calendarId="primary", body=event).execute()
    return event
