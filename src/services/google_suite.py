import os.path
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone

from src.config import config
import logging

logger = logging.getLogger(__name__)

# Scopes required
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]

class GoogleSuite:
    def __init__(self):
        self.creds = None
        self.gmail_service = None
        self.calendar_service = None
        self.tasks_service = None
        self.authenticate()

    def authenticate(self):
        """Authenticates with Google and creates service objects."""
        creds_file = config.get_secret("google_client_secrets_file", "credentials.json")
        token_file = 'token.json'

        if os.path.exists(token_file):
            self.creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    self.creds = None

            if not self.creds:
                if not os.path.exists(creds_file):
                    logger.error(f"Credentials file {creds_file} not found.")
                    return

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                    # run_local_server will open a browser window
                    self.creds = flow.run_local_server(port=0)

                    # Save the credentials for the next run
                    with open(token_file, 'w') as token:
                        token.write(self.creds.to_json())
                except Exception as e:
                    logger.error(f"Authentication flow failed: {e}")
                    return

        try:
            self.gmail_service = build('gmail', 'v1', credentials=self.creds)
            self.calendar_service = build('calendar', 'v3', credentials=self.creds)
            self.tasks_service = build('tasks', 'v1', credentials=self.creds)
            logger.info("Google Services authenticated successfully.")
        except Exception as e:
            logger.error(f"Failed to build services: {e}")

    # --- Gmail Methods ---

    def list_unread_emails(self, limit=10):
        """Lists unread emails from the inbox."""
        if not self.gmail_service: return []

        try:
            results = self.gmail_service.users().messages().list(
                userId='me', labelIds=['UNREAD'], maxResults=limit
            ).execute()
            messages = results.get('messages', [])

            email_data = []
            for msg in messages:
                txt = self.gmail_service.users().messages().get(
                    userId='me', id=msg['id']
                ).execute()

                payload = txt['payload']
                headers = payload.get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
                snippet = txt.get('snippet', '')

                email_data.append({
                    'id': msg['id'],
                    'subject': subject,
                    'sender': sender,
                    'snippet': snippet,
                    'link': f"https://mail.google.com/mail/u/0/#inbox/{msg['id']}"
                })
            return email_data
        except HttpError as error:
            logger.error(f"An error occurred in Gmail list: {error}")
            return []

    def send_email(self, to_email, subject, body):
        """Sends an email."""
        if not self.gmail_service: return False

        try:
            message = EmailMessage()
            message.set_content(body)
            message['To'] = to_email
            message['From'] = 'me' # Gmail API ignores this and uses authenticated user
            message['Subject'] = subject

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': encoded_message}

            self.gmail_service.users().messages().send(
                userId='me', body=create_message
            ).execute()
            logger.info(f"Email sent to {to_email}")
            return True
        except HttpError as error:
            logger.error(f"An error occurred sending email: {error}")
            return False

    def mark_email_as_read(self, msg_id):
        """Removes the UNREAD label from an email."""
        if not self.gmail_service: return False
        try:
            self.gmail_service.users().messages().modify(
                userId='me', id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"Failed to mark email as read: {error}")
            return False

    # --- Calendar Methods ---

    def list_upcoming_events(self, hours=24):
        """Lists events in the next X hours."""
        if not self.calendar_service: return []

        try:
            now = datetime.now(timezone.utc).isoformat()
            # Z is UTC suffix
            end_time = (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()

            events_result = self.calendar_service.events().list(
                calendarId='primary', timeMin=now, timeMax=end_time,
                singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            clean_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                clean_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'link': event.get('htmlLink')
                })
            return clean_events
        except HttpError as error:
            logger.error(f"An error occurred in Calendar list: {error}")
            return []

    def create_event(self, summary, start_time_iso, end_time_iso=None, description=None):
        """Creates a calendar event. Times must be ISO format strings."""
        if not self.calendar_service: return False

        try:
            # If no end time, assume 1 hour
            if not end_time_iso:
                start_dt = datetime.fromisoformat(start_time_iso)
                end_dt = start_dt + timedelta(hours=1)
                end_time_iso = end_dt.isoformat()

            event = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start_time_iso}, # Let Google Calendar interpret timezone (uses calendar default)
                'end': {'dateTime': end_time_iso},
            }

            event = self.calendar_service.events().insert(
                calendarId='primary', body=event
            ).execute()
            logger.info(f"Event created: {event.get('htmlLink')}")
            return event.get('htmlLink')
        except HttpError as error:
            logger.error(f"An error occurred creating event: {error}")
            return None

    # --- Tasks Methods ---

    def add_task(self, title, notes=None, due_date_iso=None):
        """Adds a task to the default list."""
        if not self.tasks_service: return False

        try:
            task = {'title': title, 'notes': notes}
            if due_date_iso:
                # Tasks API requires RFC 3339 timestamp
                task['due'] = due_date_iso

            result = self.tasks_service.tasks().insert(
                tasklist='@default', body=task
            ).execute()
            logger.info(f"Task created: {result.get('title')}")
            return result.get('links', [{}])[0].get('link', 'Task Created')
        except HttpError as error:
            logger.error(f"An error occurred creating task: {error}")
            return None

# Singleton instance
google_suite = GoogleSuite()
