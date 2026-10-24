"""
Unit tests for QuickFind Hotkey Parser
Verifies modifier parsing and virtual key mapping.
"""

import unittest
from core.hotkey import GlobalHotkeyManager, MOD_CONTROL, MOD_ALT, MOD_SHIFT, VK_MAP


class TestHotkeyManager(unittest.TestCase):

    def setUp(self):
        self.manager = GlobalHotkeyManager()

    def test_parse_ctrl_f(self):
        mods, vk = self.manager.parse_hotkey("Ctrl+F")
        self.assertTrue(mods & MOD_CONTROL)
        self.assertEqual(vk, ord("F"))

    def test_parse_alt_space(self):
        mods, vk = self.manager.parse_hotkey("Alt+Space")
        self.assertTrue(mods & MOD_ALT)
        self.assertEqual(vk, VK_MAP["SPACE"])

    def test_parse_ctrl_shift_f(self):
        mods, vk = self.manager.parse_hotkey("Ctrl+Shift+F")
        self.assertTrue(mods & MOD_CONTROL)
        self.assertTrue(mods & MOD_SHIFT)
        self.assertEqual(vk, ord("F"))


if __name__ == "__main__":
    unittest.main()
