import json
import os
import sys
import requests

def check_secrets():
    print("--- Diagnostic Tool ---")
    if not os.path.exists('secrets.json'):
        print("❌ 'secrets.json' not found in current directory.")
        return False

    print("✅ 'secrets.json' found.")

    try:
        with open('secrets.json', 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("❌ 'secrets.json' contains invalid JSON.")
        return False

    print("✅ JSON is valid.")

    token = data.get('telegram_bot_token')
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ 'telegram_bot_token' is missing or default.")
        return False

    print(f"ℹ️  Token found: {token[:5]}...{token[-5:]}")

    # Test connectivity
    try:
        print("🔄 Testing connection to Telegram API...")
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"✅ SUCCESS: Connected as @{bot_info['result']['username']}")
            else:
                print(f"❌ Telegram API returned error: {bot_info}")
        elif response.status_code == 401:
            print("❌ Unauthorized: The token is invalid.")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

    # Check allowed_ids
    allowed = data.get('allowed_telegram_user_ids')
    if allowed is None:
        print("⚠️  'allowed_telegram_user_ids' is missing. The bot will warn but might run.")
    elif isinstance(allowed, list):
        print(f"✅ 'allowed_telegram_user_ids' is a list with {len(allowed)} entries.")
    elif isinstance(allowed, int):
        print("ℹ️  'allowed_telegram_user_ids' is a single integer. The bot will handle this.")
    else:
        print(f"⚠️  'allowed_telegram_user_ids' has unexpected type: {type(allowed)}.")

    print("\n--- End of Diagnostic ---")
    return True

if __name__ == "__main__":
    check_secrets()
