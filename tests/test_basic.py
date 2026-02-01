import unittest
import os
import json
from src.config import Config, SETTINGS_FILE

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Backup settings
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                self.backup_settings = f.read()
        else:
            self.backup_settings = None

    def tearDown(self):
        # Restore settings
        if self.backup_settings:
            with open(SETTINGS_FILE, 'w') as f:
                f.write(self.backup_settings)

    def test_load_settings(self):
        c = Config()
        self.assertIsInstance(c.settings, dict)
        self.assertTrue(c.get_setting("email_check_interval_minutes"))

    def test_update_setting(self):
        c = Config()
        c.update_setting("test_key", 123)

        # Verify it updated in memory
        self.assertEqual(c.get_setting("test_key"), 123)

        # Verify it updated in file
        c2 = Config()
        self.assertEqual(c2.get_setting("test_key"), 123)

if __name__ == '__main__':
    unittest.main()
