import os
import json
import pickle
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Read client config from env (expects JSON string)
CLIENT_CONFIG_JSON = os.environ.get('GOOGLE_CLIENT_SECRET_JSON')
if not CLIENT_CONFIG_JSON:
    # In local dev you may keep client_secret.json file; load it if env var not set
    if os.path.exists('client_secret.json'):
        with open('client_secret.json', 'r') as f:
            CLIENT_CONFIG = json.load(f)
    else:
        CLIENT_CONFIG = None
else:
    CLIENT_CONFIG = json.loads(CLIENT_CONFIG_JSON)

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
TOKENS_DIR = 'tokens'

import pathlib
pathlib.Path(TOKENS_DIR).mkdir(exist_ok=True)

def credentials_path_for_user(telegram_user_id: int) -> str:
    return os.path.join(TOKENS_DIR, f'credentials_{telegram_user_id}.pickle')

def make_oauth_flow(redirect_uri: str) -> Flow:
    if CLIENT_CONFIG is None:
        raise Exception('Google client config not found. Set GOOGLE_CLIENT_SECRET_JSON env or place client_secret.json')
    # Build a Flow from client config dict
    # CLIENT_CONFIG should be the dict with keys like 'installed' or 'web'
    # We need to pass the correct sub-dict depending on how Google returned it.
    if 'web' in CLIENT_CONFIG:
        client_cfg = CLIENT_CONFIG['web']
    elif 'installed' in CLIENT_CONFIG:
        client_cfg = CLIENT_CONFIG['installed']
    else:
        client_cfg = CLIENT_CONFIG

    flow = Flow.from_client_config({'web': client_cfg}, scopes=SCOPES, redirect_uri=redirect_uri)
    return flow

def save_credentials_for_user(telegram_user_id: int, credentials: Credentials):
    path = credentials_path_for_user(telegram_user_id)
    with open(path, 'wb') as f:
        pickle.dump(credentials, f)

def load_credentials_for_user(telegram_user_id: int):
    path = credentials_path_for_user(telegram_user_id)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            creds = pickle.load(f)
            return creds
    return None

def create_event_for_user(telegram_user_id: int, event_body: dict):
    creds = load_credentials_for_user(telegram_user_id)
    if not creds:
        raise Exception('User chưa cấp quyền Google Calendar')
    # If pickled Credentials, it should be usable directly
    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return event
