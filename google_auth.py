import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)

def create_event(summary, description, start_time, end_time, calendar_id="primary"):
    service = get_calendar_service()
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "Asia/Ho_Chi_Minh"},
        "end": {"dateTime": end_time, "timeZone": "Asia/Ho_Chi_Minh"},
    }
    event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return event.get("htmlLink")
