"""Core package for QuickFind."""
from core.hotkey import GlobalHotkeyManager
from core.single_instance import SingleInstanceManager
from core.app_launcher import AppLauncher

__all__ = ["GlobalHotkeyManager", "SingleInstanceManager", "AppLauncher"]
