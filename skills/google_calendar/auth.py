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
