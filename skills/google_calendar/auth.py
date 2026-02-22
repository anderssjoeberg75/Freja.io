import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes required for the skill
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_credentials(token_path='calendar_token.json', creds_path='calendar_credentials.json'):
    """
    Retrieves valid user credentials from storage.
    Refreshes them if expired.
    """
    creds = None
    # If credentials.json doesn't exist, try to build it from the settings database
    if not os.path.exists(creds_path):
        from app.core.config import get_credential
        db_creds = get_credential("GOOGLE_CALENDAR_CREDENTIALS")
        if db_creds:
            try:
                with open(creds_path, 'w') as f:
                    f.write(db_creds)
                print(f"Restored {creds_path} from database settings.")
            except Exception as e:
                print(f"Failed to restore {creds_path} from DB: {e}")

    # Token file stores the user's access and refresh tokens
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                return None
        else:
            return None
            
    return creds
