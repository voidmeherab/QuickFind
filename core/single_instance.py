"""
Single Instance Manager
Ensures only one instance of QuickFind runs in the background.
Brings the existing window to the front if another instance is launched.
"""

import sys
import ctypes
from ctypes import wintypes
from typing import Optional, Callable

# Constants
ERROR_ALREADY_EXISTS = 183
HWND_BROADCAST = 0xFFFF

MUTEX_NAME = "Global\\QuickFind_SingleInstance_Mutex"
MSG_NAME = "QuickFind_Show_Window_Message"


class SingleInstanceManager:
    """Manages single-instance mutex and cross-process wake-up signaling."""

    def __init__(self, mutex_name: str = MUTEX_NAME, on_remote_show: Optional[Callable[[], None]] = None):
        self.mutex_name = mutex_name
        self.on_remote_show = on_remote_show
        self.mutex_handle: Optional[wintypes.HANDLE] = None
        self.custom_msg_id: int = 0
        self._is_primary = False

        self._register_message()

    def _register_message(self) -> None:
        """Register the custom Windows message for cross-instance communication."""
        try:
            self.custom_msg_id = ctypes.windll.user32.RegisterWindowMessageW(MSG_NAME)
        except Exception as e:
            print(f"[QuickFind] Error registering custom message: {e}", file=sys.stderr)

    def is_already_running(self) -> bool:
        """
        Check if another instance is already running.
        Returns True if already running, False if this is the primary instance.
        """
        try:
            self.mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, self.mutex_name)
            last_err = ctypes.windll.kernel32.GetLastError()

            if last_err == ERROR_ALREADY_EXISTS:
                self._is_primary = False
                return True

            self._is_primary = True
            return False
        except Exception as e:
            print(f"[QuickFind] Error creating mutex: {e}", file=sys.stderr)
            return False

    def signal_existing_instance(self) -> None:
        """Signal the existing instance to reveal its window and focus."""
        if self.custom_msg_id:
            try:
                ctypes.windll.user32.PostMessageW(HWND_BROADCAST, self.custom_msg_id, 0, 0)
            except Exception as e:
                print(f"[QuickFind] Error signaling existing instance: {e}", file=sys.stderr)

    def release(self) -> None:
        """Release the mutex handle on application exit."""
        if self.mutex_handle and self._is_primary:
            try:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
            except Exception:
                pass
            self.mutex_handle = None
