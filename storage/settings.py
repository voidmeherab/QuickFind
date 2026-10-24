"""
QuickFind Settings Storage
Manages saving and loading user preferences to/from JSON.
"""

import json
import os
import sys
import winreg
from typing import Any, Dict
from config import DEFAULT_SETTINGS, get_user_data_dir, APP_NAME

SETTINGS_FILE = os.path.join(get_user_data_dir(), "settings.json")
STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


class SettingsManager:
    """Handles persistent configuration with atomic writes and registry startup integration."""

    def __init__(self, filepath: str = SETTINGS_FILE):
        self.filepath = filepath
        self._data: Dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        """Load settings from JSON file. If missing or invalid, load defaults."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self._data.update(loaded)
            except Exception as e:
                print(f"[QuickFind] Error loading settings: {e}. Using defaults.", file=sys.stderr)
        else:
            self.save()

    def save(self) -> None:
        """Save current settings to JSON file atomically."""
        try:
            temp_path = self.filepath + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
            os.rename(temp_path, self.filepath)
        except Exception as e:
            print(f"[QuickFind] Error saving settings: {e}", file=sys.stderr)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a setting value."""
        return self._data.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and persist immediately."""
        self._data[key] = value
        self.save()

        # Handle launch at startup change
        if key == "launch_at_startup":
            self.apply_startup_setting(bool(value))

    def apply_startup_setting(self, enable: bool) -> bool:
        """Register or unregister the app in the Windows Run registry key."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    if getattr(sys, 'frozen', False):
                        exe_path = sys.executable
                    else:
                        exe_path = f'"{sys.executable}" "{os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")}"'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            print(f"[QuickFind] Failed to update startup registry key: {e}", file=sys.stderr)
            return False
