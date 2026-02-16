import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file calendar_token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    """Shows basic usage of the Google Calendar API."""
    creds = None
    token_file = 'calendar_token.json'
    creds_file = 'calendar_credentials.json'

    # The file calendar_token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_file):
                print(f"ERROR: {creds_file} not found!")
                print("Please download your OAuth 2.0 Client Secret JSON from Google Cloud Console")
                print(f"and save it as '{creds_file}' in this directory.")
                return

            print("Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            
            # Run local server config
            # Use fixed port to valid redirect URI mismatches if possible
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        print(f"Saving credentials to {token_file}...")
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
            
    print("✅ Authentication successful!")

if __name__ == '__main__':
    main()
