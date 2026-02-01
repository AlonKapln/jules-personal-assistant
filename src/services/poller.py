import logging
from src.config import config
from src.services.google_suite import google_suite
from src.services.brain import brain
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Poller:
    def __init__(self):
        self.notified_email_ids = set()
        self.notified_event_ids = set()
        # Clean caches occasionally? For now, we assume memory is plenty for IDs.

    def poll_emails(self):
        """Checks for new important emails. Returns a list of alert strings."""
        alerts = []
        try:
            # check unread emails
            emails = google_suite.list_unread_emails(limit=10)
            if not emails:
                return []

            use_ai = config.get_setting("ai_email_filtering", True)

            for email in emails:
                if email['id'] in self.notified_email_ids:
                    continue

                is_important = False
                reason = ""

                if use_ai:
                    is_important, reason = brain.analyze_email_importance(
                        email['subject'], email['sender'], email['snippet']
                    )
                else:
                    # Simple filtering: Check if 'Important' label exists?
                    # The list_unread_emails doesn't return labels.
                    # Let's simple check if it is unread (which it is) and maybe some keyword?
                    # For V1 simple mode, let's just alert on ALL unread emails if AI is off,
                    # or maybe just assume the user uses Gmail's filters.
                    # Let's say: Simple mode = Notify everything.
                    is_important = True
                    reason = "New unread email."

                if is_important:
                    alerts.append(
                        f"📧 **Important Email**\nFrom: {email['sender']}\nSubject: {email['subject']}\nReason: {reason}\n[Open]({email['link']})"
                    )
                    self.notified_email_ids.add(email['id'])
                else:
                    # If analyzed and not important, still mark as 'seen' by the poller so we don't re-analyze
                    self.notified_email_ids.add(email['id'])

            return alerts
        except Exception as e:
            logger.error(f"Error polling emails: {e}")
            return []

    def poll_calendar(self):
        """Checks for upcoming events. Returns a list of alert strings."""
        alerts = []
        try:
            # Check events in next 30 minutes
            events = google_suite.list_upcoming_events(hours=0.5)

            for event in events:
                if event['id'] in self.notified_event_ids:
                    continue

                # We could add logic to only notify if start time is within X minutes
                # But list_upcoming_events(0.5) implies they are starting soon.

                start_str = event['start'] # ISO string
                # Simple parsing for display
                try:
                    dt = datetime.fromisoformat(start_str)
                    time_display = dt.strftime("%H:%M")
                except:
                    time_display = start_str

                alerts.append(
                    f"📅 **Upcoming Event**\n{event['summary']}\nAt: {time_display}\n[Link]({event['link']})"
                )
                self.notified_event_ids.add(event['id'])

            return alerts
        except Exception as e:
            logger.error(f"Error polling calendar: {e}")
            return []

poller = Poller()
