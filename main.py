"""
QuickFind — Premium Animated Windows Application Launcher
Application Entry Point and Lifecycle Coordinator.
"""

import sys
import os
import threading

# Add current directory to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from config import APP_NAME, APP_VERSION
from storage.settings import SettingsManager
from storage.history_db import HistoryDB
from services.icon_extractor import IconExtractor
from services.app_scanner import AppScanner
from services.search_engine import SearchEngine
from core.single_instance import SingleInstanceManager
from core.hotkey import GlobalHotkeyManager
from core.app_launcher import AppLauncher


def run_qt_app(
    settings: SettingsManager,
    history_db: HistoryDB,
    search_engine: SearchEngine,
    scanner: AppScanner,
    launcher: AppLauncher,
    single_inst: SingleInstanceManager
) -> None:
    """Run the PySide6 modern animated launcher."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject, Signal, Slot
    from ui.search_window import SearchWindow
    from ui.tray_icon import QuickFindTrayIcon
    from ui.settings_dialog import SettingsDialog

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Thread-safe signal dispatcher for cross-thread hotkey callbacks
    class HotkeyDispatcher(QObject):
        triggered = Signal()
        remote_show = Signal()

    dispatcher = HotkeyDispatcher()

    # Search Window
    search_win = SearchWindow(
        search_engine=search_engine,
        app_launcher=launcher,
        settings=settings
    )
    dispatcher.triggered.connect(search_win.show_launcher)
    dispatcher.remote_show.connect(search_win.show_launcher)

    # Tray Icon
    tray = QuickFindTrayIcon()
    tray.request_open.connect(search_win.show_launcher)
    tray.request_refresh.connect(lambda: threading.Thread(target=_scan_and_update, daemon=True).start())

    # Settings Dialog
    settings_dialog = None

    def open_settings():
        nonlocal settings_dialog
        if not settings_dialog:
            settings_dialog = SettingsDialog(
                settings=settings,
                on_rescan=lambda: _scan_and_update(blocking=True),
                parent=None
            )
            settings_dialog.settings_saved.connect(_on_settings_updated)
        settings_dialog.show()
        settings_dialog.raise_()
        settings_dialog.activateWindow()

    tray.request_settings.connect(open_settings)
    tray.show()

    # Global Hotkey Manager
    hotkey_str = settings.get("global_shortcut", "Ctrl+F")
    hotkey_enabled = settings.get("enable_global_shortcut", True)

    hotkey_mgr = GlobalHotkeyManager(
        hotkey_str=hotkey_str,
        on_trigger=dispatcher.triggered.emit
    )

    if hotkey_enabled:
        started = hotkey_mgr.start()
        if not started:
            print(f"[QuickFind] Warning: {hotkey_mgr.get_last_error()}", file=sys.stderr)

    def _on_settings_updated():
        nonlocal hotkey_str
        new_hk = settings.get("global_shortcut", "Ctrl+F")
        new_enabled = settings.get("enable_global_shortcut", True)
        if new_enabled:
            if new_hk != hotkey_mgr.hotkey_str or not hotkey_mgr._is_running:
                hotkey_mgr.update_hotkey(new_hk)
        else:
            hotkey_mgr.stop()
        if hasattr(search_win, 'shortcut_badge') and search_win.shortcut_badge:
            search_win.shortcut_badge.setText(new_hk)

    def _scan_and_update(blocking: bool = False) -> int:
        print("[QuickFind] Scanning installed applications...")
        apps = scanner.scan_all()
        search_engine.set_apps(apps)
        print(f"[QuickFind] Successfully indexed {len(apps)} applications.")
        return len(apps)

    # Exit handler
    def cleanup_and_exit():
        tray.hide()
        hotkey_mgr.stop()
        single_inst.release()
        app.quit()

    tray.request_exit.connect(cleanup_and_exit)

    # Initial async application scan
    scan_thread = threading.Thread(target=_scan_and_update, daemon=True)
    scan_thread.start()

    print(f"[QuickFind] Running in background. Press {hotkey_str} to activate.")
    sys.exit(app.exec())


def run_tk_app(
    settings: SettingsManager,
    history_db: HistoryDB,
    search_engine: SearchEngine,
    scanner: AppScanner,
    launcher: AppLauncher,
    single_inst: SingleInstanceManager
) -> None:
    """Run standard-library Tkinter dark launcher (fallback mode)."""
    from ui.tk_fallback import TkSearchWindow

    tk_win = TkSearchWindow(
        search_engine=search_engine,
        app_launcher=launcher,
        settings=settings
    )

    hotkey_str = settings.get("global_shortcut", "Ctrl+F")
    hotkey_enabled = settings.get("enable_global_shortcut", True)

    def on_hotkey():
        # Dispatch to Tk thread
        try:
            tk_win.root.after(0, tk_win.show)
        except Exception:
            pass

    hotkey_mgr = GlobalHotkeyManager(
        hotkey_str=hotkey_str,
        on_trigger=on_hotkey
    )

    if hotkey_enabled:
        hotkey_mgr.start()

    def _scan_and_update():
        print("[QuickFind] Scanning installed applications...")
        apps = scanner.scan_all()
        search_engine.set_apps(apps)
        print(f"[QuickFind] Successfully indexed {len(apps)} applications.")

    scan_thread = threading.Thread(target=_scan_and_update, daemon=True)
    scan_thread.start()

    # Hide initially
    tk_win.hide()

    print(f"[QuickFind] Running in background (Tk mode). Press {hotkey_str} to activate.")
    try:
        tk_win.root.mainloop()
    finally:
        hotkey_mgr.stop()
        single_inst.release()


def main():
    """Application main entry point."""
    print("=" * 60)
    print(f" {APP_NAME} v{APP_VERSION} — Starting Launcher")
    print("=" * 60)

    # 1. Single Instance Check
    single_inst = SingleInstanceManager()
    if single_inst.is_already_running():
        print("[QuickFind] Another instance is already running. Signaling existing instance...")
        single_inst.signal_existing_instance()
        sys.exit(0)

    # 2. Initialize Components
    settings = SettingsManager()
    history_db = HistoryDB()
    icon_extractor = IconExtractor()
    scanner = AppScanner(icon_extractor=icon_extractor)
    search_engine = SearchEngine(history_db=history_db)
    launcher = AppLauncher(history_db=history_db)

    # 3. Check for PySide6
    try:
        import PySide6
        has_pyside6 = True
    except ImportError:
        has_pyside6 = False

    if has_pyside6:
        run_qt_app(settings, history_db, search_engine, scanner, launcher, single_inst)
    else:
        print("[QuickFind] PySide6 not installed. Using standard library Tkinter mode.")
        print("[QuickFind] To enable full animated HUD, run: pip install PySide6")
        run_tk_app(settings, history_db, search_engine, scanner, launcher, single_inst)


if __name__ == "__main__":
    main()
