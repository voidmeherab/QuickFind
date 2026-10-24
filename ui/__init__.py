"""UI package for QuickFind."""
try:
    from ui.search_window import SearchWindow, PYSIDE6_AVAILABLE
    from ui.settings_dialog import SettingsDialog
    from ui.tray_icon import QuickFindTrayIcon
except ImportError:
    PYSIDE6_AVAILABLE = False
    SearchWindow = None
    SettingsDialog = None
    QuickFindTrayIcon = None

from ui.tk_fallback import TkSearchWindow

__all__ = [
    "SearchWindow",
    "SettingsDialog",
    "QuickFindTrayIcon",
    "TkSearchWindow",
    "PYSIDE6_AVAILABLE",
]
