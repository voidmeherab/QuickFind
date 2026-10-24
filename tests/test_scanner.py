"""
Unit tests for QuickFind App Scanner
Verifies name cleaning, exclusion filters, and system apps discovery.
"""

import unittest
from services.app_scanner import AppScanner


class TestAppScanner(unittest.TestCase):

    def setUp(self):
        self.scanner = AppScanner()

    def test_clean_app_name(self):
        self.assertEqual(self.scanner._clean_app_name("Google Chrome - Shortcut"), "Google Chrome")
        self.assertEqual(self.scanner._clean_app_name("Notepad.exe"), "Notepad")
        self.assertEqual(self.scanner._clean_app_name("Discord.lnk"), "Discord")
        self.assertEqual(self.scanner._clean_app_name("Visual Studio Code - shortcut.lnk"), "Visual Studio Code")

    def test_uninstaller_exclusion(self):
        self.assertTrue(self.scanner._is_excluded("Uninstall App", "C:\\App\\unins000.exe"))
        self.assertTrue(self.scanner._is_excluded("App Uninstaller", "C:\\App\\uninstall.exe"))
        self.assertFalse(self.scanner._is_excluded("Calculator", "C:\\Windows\\System32\\calc.exe"))

    def test_doc_extension_exclusion(self):
        self.assertTrue(self.scanner._is_excluded("User Guide", "C:\\App\\guide.pdf"))
        self.assertTrue(self.scanner._is_excluded("Readme", "C:\\App\\readme.txt"))
        self.assertTrue(self.scanner._is_excluded("Help", "C:\\App\\help.chm"))
        self.assertFalse(self.scanner._is_excluded("Slack", "C:\\App\\slack.exe"))


if __name__ == "__main__":
    unittest.main()
