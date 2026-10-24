"""
Windows Global Hotkey Manager
Registers and listens for system-wide keyboard shortcuts using native Windows APIs
(RegisterHotKey / UnregisterHotKey) on a dedicated background thread.
"""

import sys
import threading
import ctypes
from ctypes import wintypes
from typing import Callable, Optional, Tuple

# Windows Virtual Key & Modifier Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

# Common Virtual Key Codes
VK_MAP = {
    "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45, "F": 0x46,
    "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A, "K": 0x4B, "L": 0x4C,
    "M": 0x4D, "N": 0x4E, "O": 0x4F, "P": 0x50, "Q": 0x51, "R": 0x52,
    "S": 0x53, "T": 0x54, "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58,
    "Y": 0x59, "Z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "SPACE": 0x20, "TAB": 0x09, "ENTER": 0x0D, "ESCAPE": 0x1B,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
}

HOTKEY_ID = 101


class GlobalHotkeyManager:
    """Manages system-wide global shortcut registration and message pumping."""

    def __init__(self, hotkey_str: str = "Ctrl+F", on_trigger: Optional[Callable[[], None]] = None):
        self.hotkey_str = hotkey_str
        self.on_trigger = on_trigger
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._is_running = False
        self._registration_success = False
        self._last_error = ""

    def parse_hotkey(self, hotkey: str) -> Tuple[int, int]:
        """Parse shortcut string (e.g. 'Ctrl+F', 'Alt+Space') into (modifiers, vk_code)."""
        parts = [p.strip().upper() for p in hotkey.split("+")]
        modifiers = MOD_NOREPEAT
        vk = 0

        for part in parts:
            if part in ("CTRL", "CONTROL"):
                modifiers |= MOD_CONTROL
            elif part in ("ALT", "MENU"):
                modifiers |= MOD_ALT
            elif part in ("SHIFT",):
                modifiers |= MOD_SHIFT
            elif part in ("WIN", "WINDOWS", "SUPER"):
                modifiers |= MOD_WIN
            elif part in VK_MAP:
                vk = VK_MAP[part]
            elif len(part) == 1 and part.isalnum():
                vk = ord(part)

        return modifiers, vk

    def start(self) -> bool:
        """Start the background hotkey listener thread."""
        if self._is_running:
            return True

        self._is_running = True
        ready_event = threading.Event()

        self._thread = threading.Thread(
            target=self._msg_loop, args=(ready_event,), daemon=True, name="QuickFind-Hotkey"
        )
        self._thread.start()
        ready_event.wait(timeout=2.0)

        return self._registration_success

    def stop(self) -> None:
        """Unregister hotkey and stop the listener message loop."""
        if not self._is_running:
            return

        self._is_running = False
        if self._thread_id:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._thread_id = None

    def update_hotkey(self, new_hotkey_str: str) -> bool:
        """Change the active hotkey dynamically."""
        self.stop()
        self.hotkey_str = new_hotkey_str
        return self.start()

    def get_last_error(self) -> str:
        """Return the last error message, if any."""
        return self._last_error

    def _msg_loop(self, ready_event: threading.Event) -> None:
        """Windows message pump for WM_HOTKEY events on the dedicated thread."""
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        mods, vk = self.parse_hotkey(self.hotkey_str)
        if not vk:
            self._last_error = f"Invalid key in shortcut: '{self.hotkey_str}'"
            self._registration_success = False
            ready_event.set()
            return

        # Register hotkey on this thread
        res = ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, mods, vk)
        if not res:
            err_code = ctypes.windll.kernel32.GetLastError()
            self._last_error = (
                f"Failed to register hotkey '{self.hotkey_str}' (Windows Error {err_code}). "
                "Another application may already be using this shortcut. "
                "You can change the shortcut in QuickFind Settings."
            )
            print(f"[QuickFind] {self._last_error}", file=sys.stderr)
            self._registration_success = False
            ready_event.set()
            return

        self._registration_success = True
        self._last_error = ""
        ready_event.set()

        msg = wintypes.MSG()
        try:
            while self._is_running:
                # GetMessage blocks until a message arrives, consuming 0% CPU!
                b_ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if b_ret == 0 or b_ret == -1:  # WM_QUIT or error
                    break

                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    if self.on_trigger:
                        try:
                            self.on_trigger()
                        except Exception as e:
                            print(f"[QuickFind] Error in hotkey trigger callback: {e}", file=sys.stderr)

                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)
