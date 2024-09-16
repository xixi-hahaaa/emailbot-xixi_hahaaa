# EmailEvent Class

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from query import load_query
from datetime import datetime

class GmailEvent:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self):
        self.creds = None
        self.service = None

    def authenticate(self):
        # Check if token.json file exists
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        # Check if credentials are not valid or expired
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    self.creds = None
            if not self.creds or not self.creds.valid:
                # If credentials are still invalid, run the flow to get new credentials
                flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the new credentials
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        self.service = build('gmail', 'v1', credentials=self.creds)

    def __search_email(self, query):
        """Search for emails based on a query and return the snippet with the sent date."""
        result = self.service.users().messages().list(userId='me', q=query).execute()
        messages = result.get('messages', [])
        
        if not messages:
            return None
        
        # Get the first message i.e. most recent email
        message = self.service.users().messages().get(userId='me', id=messages[0]['id']).execute()
        
        # Extract the snippet and internalDate
        snippet = message['snippet']
        internal_date = message['internalDate']
        
        # Convert internalDate
        sent_date = datetime.fromtimestamp(int(internal_date) / 1000.0)
        
        return {
            'snippet': snippet,
            'sent_date': sent_date.strftime('%Y-%m-%d') 
        }
    
    
    def check_hydro_bill(self):
        """Check for hydro bill emails."""
        query = None
        json_file = "json/query.json"
        
        # Check if query.json file details exist
        if os.path.exists(json_file):
            queries = load_query(json_file)
            query = queries.get("hydro_bill_query")

        return self.__search_email(query)



