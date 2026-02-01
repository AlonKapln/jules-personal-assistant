# Kernel: Your AI Assistant

Kernel is a smart personal assistant that integrates **Telegram**, **Google Gemini**, **Gmail**, **Google Calendar**, and **Google Tasks**.

Runs locally on your machine for privacy and control.

## Features
- **Smart Email Alerts**: Notifies you of important emails (uses AI to filter spam/noise).
- **Calendar Management**: Lists upcoming events and schedules new ones via chat.
- **Task Management**: Adds items to your Google Tasks.
- **Natural Language**: Chat naturally ("Schedule lunch with Mom tomorrow at 1pm") and the bot understands.
- **Dashboard**: A GUI to configure settings, prompts, and filtering.

## Prerequisites
- Python 3.9+
- A Google Cloud Project with Gmail, Calendar, and Tasks APIs enabled.
- A Telegram Bot Token.
- A Google Gemini API Key.

## Setup Guide

### 1. Installation
1. Clone this repository or download the files.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Configuration
1. Rename `secrets.json.example` to `secrets.json`.
2. Open `secrets.json` and fill in your keys:
   - `telegram_bot_token`: Get from @BotFather on Telegram.
   - `gemini_api_key`: Get from Google AI Studio.
   - `allowed_telegram_user_ids`: (Optional) List of your Telegram User IDs (integers). If empty, anyone can talk to your bot!
     - *Tip: Start the bot, send a message, and check logs (or just add a print in `bot.py`) to find your ID.*

### 3. Google Credentials
1. Create a Desktop OAuth 2.0 Client ID in Google Cloud Console.
2. Download the JSON file and rename it to `credentials.json`.
3. Place `credentials.json` in the project root folder.

## Running the Bot

You need to run two processes (in separate terminal tabs):

**1. Run the Bot (The Brain)**
```bash
python main.py bot
```
*On first run, a browser window will open to authorize access to your Google Account.*

**2. Run the Dashboard (The GUI)**
```bash
python main.py dashboard
```
*This will open `http://localhost:8501` in your browser.*

## Customization
Use the Dashboard to:
- Change the bot's "System Prompt" (make it sassy, formal, or concise).
- Toggle AI Email filtering.
- Adjust polling intervals.

## Troubleshooting
- **Authentication Error:** Delete `token.json` and restart the bot to re-login.
- **Bot not replying:** Check `secrets.json` and ensure your User ID is allowed (or list is empty for testing).
