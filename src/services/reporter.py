import logging
from src.services.google_suite import google_suite
from src.services.brain import brain

logger = logging.getLogger(__name__)

class Reporter:
    def __init__(self):
        pass

    def generate_report(self, part_of_day: str):
        """Generates a summary report for the user."""
        try:
            logger.info(f"Generating {part_of_day} report...")

            # Fetch data
            emails = google_suite.list_unread_emails(limit=10)
            tasks = google_suite.list_tasks(limit=10)
            events = google_suite.list_upcoming_events(hours=12)

            # Construct context for the Brain
            context = f"""
            You are generating a {part_of_day} report for the user.

            Unread Emails (last 10):
            {emails}

            Upcoming Tasks:
            {tasks}

            Upcoming Events (next 12h):
            {events}

            Please summarize this information into a concise and helpful report.
            Highlight important items.
            If there are no emails, tasks, or events, mention that the user is clear.
            Structure it nicely with Markdown.
            """

            # Use Brain to generate the text
            # We use a direct generation request to the model
            if brain.model:
                response = brain.model.generate_content(context)
                return response.text
            else:
                return "Brain is offline. Cannot generate report."

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return "Failed to generate report due to an error."

reporter = Reporter()
