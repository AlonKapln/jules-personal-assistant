import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SECRETS_FILE = 'secrets.json'
SETTINGS_FILE = 'settings.json'

class Config:
    def __init__(self):
        self.secrets = self._load_json(SECRETS_FILE)
        self.settings = self._load_json(SETTINGS_FILE)

    def _load_json(self, filepath):
        if not os.path.exists(filepath):
            logger.warning(f"{filepath} not found. Please create it.")
            return {}
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding {filepath}")
            return {}

    def get_secret(self, key, default=None):
        return self.secrets.get(key, default)

    def reload_settings(self):
        self.settings = self._load_json(SETTINGS_FILE)

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def update_setting(self, key, value):
        self.settings[key] = value
        self._save_settings()

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved.")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

# Global config instance
config = Config()
