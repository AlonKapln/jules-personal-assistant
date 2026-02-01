import logging
import asyncio
import sys
from telegram import Update, Bot
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, Application

# 1. Setup Logging immediately to capture startup errors
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG, # Changed to DEBUG to trace responsiveness issues
    handlers=[
        logging.FileHandler("kernel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 2. Add Global Exception Hook
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

logger.info("Initializing Kernel Bot...")

# 3. Safe Imports
try:
    from src.config import config
    from src.services.brain import brain
    from src.services.poller import poller
except Exception as e:
    logger.critical(f"Failed to import dependencies: {e}", exc_info=True)
    sys.exit(1)

# Global variable for access control
ALLOWED_USER_IDS = []

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong! Kernel is running.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am Kernel, your personal AI assistant. I can manage your emails, calendar, and tasks. How can I help you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "You can ask me things like:\n"
        "- 'Schedule a meeting with John tomorrow at 2pm'\n"
        "- 'Read my unread emails'\n"
        "- 'Remind me to buy milk'\n"
        "- 'Send an email to boss@example.com saying I will be late'\n"
        "\nI also check your emails and calendar in the background!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        logger.debug(f"Received message from user_id: {user_id}")

        # Security check
        if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
            logger.warning(f"Unauthorized access attempt by {user_id}")
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return

        # Indicate processing
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        user_text = update.message.text
        logger.info(f"Processing message: {user_text}")

        # Process with Brain
        response = await asyncio.get_running_loop().run_in_executor(None, brain.process_user_intent, user_text)

        logger.info("Response generated.")
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await update.message.reply_text("I encountered an error while processing your message.")

async def polling_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check for updates."""
    # Reload settings to pick up any changes from Dashboard
    config.reload_settings()

    if not ALLOWED_USER_IDS:
        return

    chat_id = ALLOWED_USER_IDS[0]

    # Run polling in executor to avoid blocking the event loop
    email_alerts = await asyncio.get_running_loop().run_in_executor(None, poller.poll_emails)
    for alert in email_alerts:
        await context.bot.send_message(chat_id=chat_id, text=alert, parse_mode='Markdown')

    calendar_alerts = await asyncio.get_running_loop().run_in_executor(None, poller.poll_calendar)
    for alert in calendar_alerts:
        await context.bot.send_message(chat_id=chat_id, text=alert, parse_mode='Markdown')


def run_bot():
    global ALLOWED_USER_IDS

    # Process configuration securely inside the run function
    raw_allowed_ids = config.get_secret("allowed_telegram_user_ids", [])
    ALLOWED_USER_IDS = []

    if isinstance(raw_allowed_ids, int):
        ALLOWED_USER_IDS = [raw_allowed_ids]
    elif isinstance(raw_allowed_ids, list):
        for uid in raw_allowed_ids:
            try:
                ALLOWED_USER_IDS.append(int(uid))
            except (ValueError, TypeError):
                logger.warning(f"Invalid user ID in configuration: {uid}")
    else:
        logger.warning(f"Invalid format for allowed_telegram_user_ids: {type(raw_allowed_ids)}. expected list or int.")

    if not ALLOWED_USER_IDS:
        logger.warning("No allowed Telegram user IDs configured in secrets.json. Anyone can use this bot!")
    else:
        logger.info(f"Bot restricted to {len(ALLOWED_USER_IDS)} users.")

    token = config.get_secret("telegram_bot_token")
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("Telegram Bot Token is missing. Please set it in secrets.json")
        return

    try:
        application = ApplicationBuilder().token(token).build()

        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('help', help_command))
        application.add_handler(CommandHandler('ping', ping))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

        # Add background job
        job_queue = application.job_queue
        if job_queue:
            # Check every minute (or config interval)
            interval = config.get_setting("email_check_interval_minutes", 5) * 60
            job_queue.run_repeating(polling_job, interval=interval, first=10)
            logger.info(f"Polling job scheduled every {interval} seconds.")

        logger.info("Bot is running... (Press Ctrl+C to stop)")
        application.run_polling()
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}", exc_info=True)

if __name__ == '__main__':
    run_bot()
