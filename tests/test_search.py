"""
Unit tests for QuickFind Search Engine
Verifies prefix matching, acronym matching, exact matching, and ranking logic.
"""

import unittest
from services.app_scanner import AppEntry
from services.search_engine import SearchEngine


class MockHistoryDB:
    def get_all_stats(self):
        return {
            "google chrome|c:\\chrome.exe": (50, 100000.0),
            "calculator|c:\\calc.exe": (10, 50000.0)
        }

    def record_launch(self, app_id):
        pass


class TestSearchEngine(unittest.TestCase):

    def setUp(self):
        self.history_db = MockHistoryDB()
        self.engine = SearchEngine(history_db=self.history_db)

        self.apps = [
            AppEntry(name="Google Chrome", target_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            AppEntry(name="Visual Studio Code", target_path=r"C:\Users\User\AppData\Local\Programs\Microsoft VS Code\Code.exe"),
            AppEntry(name="Calculator", target_path=r"C:\Windows\System32\calc.exe"),
            AppEntry(name="Notepad", target_path=r"C:\Windows\System32\notepad.exe"),
            AppEntry(name="Command Prompt", target_path=r"C:\Windows\System32\cmd.exe"),
            AppEntry(name="Windows PowerShell", target_path=r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"),
            AppEntry(name="Spotify", target_path=r"C:\Users\User\AppData\Roaming\Spotify\Spotify.exe"),
            AppEntry(name="Steam", target_path=r"C:\Program Files (x86)\Steam\steam.exe"),
        ]
        self.engine.set_apps(self.apps)

    def test_exact_match(self):
        results = self.engine.search("notepad", max_results=5)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].app.name, "Notepad")
        self.assertGreaterEqual(results[0].score, 1000.0)

    def test_prefix_match(self):
        results = self.engine.search("calc", max_results=5)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].app.name, "Calculator")
        self.assertGreaterEqual(results[0].score, 900.0)

    def test_acronym_match(self):
        results = self.engine.search("vsc", max_results=5)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].app.name, "Visual Studio Code")

    def test_word_boundary_match(self):
        results = self.engine.search("code", max_results=5)
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].app.name, "Visual Studio Code")

    def test_case_insensitivity(self):
        res1 = self.engine.search("CHROME")
        res2 = self.engine.search("chrome")
        self.assertEqual(res1[0].app.name, res2[0].app.name)

    def test_empty_query(self):
        results = self.engine.search("", max_results=3)
        self.assertEqual(len(results), 3)

    def test_no_matches(self):
        results = self.engine.search("xyznonexistent123")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
