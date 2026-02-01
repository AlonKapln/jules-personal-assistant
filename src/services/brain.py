import google.generativeai as genai
from src.config import config
from src.services.google_suite import google_suite
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class Brain:
    def __init__(self):
        self.api_key = config.get_secret("gemini_api_key")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._setup_model()
            self.chat = self.model.start_chat(enable_automatic_function_calling=True)
        else:
            logger.warning("Gemini API Key not found. Brain will not function.")
            self.model = None
            self.chat = None

    def _setup_model(self):
        # Define the tools available to the model
        # We wrap google_suite methods to ensure they have good docstrings for the model

        def create_calendar_event(summary: str, start_time_iso: str, end_time_iso: str = None, description: str = None):
            """Creates a new event in the user's primary calendar.

            Args:
                summary: The title of the event.
                start_time_iso: The start time in ISO 8601 format (e.g. '2023-10-27T10:00:00').
                end_time_iso: The end time in ISO 8601 format. If not provided, defaults to 1 hour after start.
                description: A description or body for the event.
            """
            return google_suite.create_event(summary, start_time_iso, end_time_iso, description)

        def add_todo_task(title: str, notes: str = None, due_date_iso: str = None):
            """Adds a new task to the user's Google Tasks.

            Args:
                title: The content of the task.
                notes: Additional details for the task.
                due_date_iso: The due date in ISO 8601 format (RFC 3339).
            """
            return google_suite.add_task(title, notes, due_date_iso)

        def list_todo_tasks(limit: int = 10):
            """Lists the user's tasks from Google Tasks.

            Args:
                limit: The max number of tasks to retrieve (default 10).
            """
            return google_suite.list_tasks(limit)

        def send_email(to_email: str, subject: str, body: str):
            """Sends an email to a specific address.

            Args:
                to_email: The recipient's email address.
                subject: The subject line of the email.
                body: The main content/body of the email.
            """
            return google_suite.send_email(to_email, subject, body)

        def list_unread_emails(limit: int = 5):
            """Lists the most recent unread emails.

            Args:
                limit: The max number of emails to retrieve (default 5).
            """
            return google_suite.list_unread_emails(limit)

        def list_upcoming_events(hours: int = 24):
            """Lists calendar events occurring in the next X hours.

            Args:
                hours: The number of hours to look ahead (default 24).
            """
            return google_suite.list_upcoming_events(hours)

        def get_current_time():
            """Returns the current date and time."""
            return datetime.now().isoformat()

        tools = [
            create_calendar_event,
            add_todo_task,
            list_todo_tasks,
            send_email,
            list_unread_emails,
            list_upcoming_events,
            get_current_time
        ]

        system_instruction = config.get_setting("system_prompt") or ""
        # Append tool usage instructions
        system_instruction += "\n\nYou have access to tools to manage the user's digital life. " \
                              "When asked to schedule or remind, use the appropriate tool. " \
                              "Always check the current time using get_current_time if you need to schedule something relatively (like 'tomorrow')."

        model_name = config.get_setting("gemini_model") or 'gemini-3-flash-preview'
        model = genai.GenerativeModel(
            model_name=model_name,
            tools=tools,
            system_instruction=system_instruction
        )
        return model

    def process_user_intent(self, user_message):
        """Sends user message to Gemini and returns the response."""
        if not self.chat:
            return "I am not connected to my brain (Gemini API Key missing)."

        try:
            # We send the message. Automatic function calling handles the tool execution loop.
            response = self.chat.send_message(user_message)
            return response.text
        except Exception as e:
            logger.error(f"Error processing intent: {e}", exc_info=True)
            return f"I had trouble thinking about that. Error: {e}. Please try again."

    def analyze_email_importance(self, subject, sender, snippet):
        """Analyzes if an email is important."""
        if not self.model: return False, "Brain missing."

        criteria = config.get_setting("importance_criteria")
        prompt = f"""
        Analyze the following email and decide if it is IMPORTANT based on this criteria: "{criteria}".

        Email Subject: {subject}
        Sender: {sender}
        Snippet: {snippet}

        Respond with valid JSON only: {{ "important": boolean, "reason": "short explanation" }}
        """

        try:
            # Use a separate non-chat generation for this stateless task
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            return data.get("important", False), data.get("reason", "No reason provided.")
        except Exception as e:
            logger.error(f"Error analyzing email: {e}")
            return False, "Error in analysis."

# Singleton
brain = Brain()
