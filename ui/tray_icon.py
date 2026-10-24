"""
QuickFind System Tray Icon (PySide6)
Provides background operation, context menu, settings access, and clean application exit.
"""

from typing import Optional

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
    from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from config import APP_NAME, APP_VERSION


if PYSIDE6_AVAILABLE:

    class QuickFindTrayIcon(QSystemTrayIcon):
        """System tray icon and context menu."""

        request_open = Signal()
        request_settings = Signal()
        request_refresh = Signal()
        request_exit = Signal()

        def __init__(self, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self._init_icon()
            self._build_menu()
            self.activated.connect(self._on_tray_activated)

        def _init_icon(self) -> None:
            """Generate or set the system tray icon."""
            icon = self._generate_tray_icon()
            self.setIcon(icon)
            self.setToolTip(f"{APP_NAME} — Press Ctrl+F to open")

        def _generate_tray_icon(self) -> QIcon:
            """Generate a crisp dark/cyan vector icon for the system tray."""
            pix = QPixmap(32, 32)
            pix.fill(Qt.transparent)

            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)

            # Outer rounded square
            painter.setBrush(QColor("#121418"))
            painter.setPen(QColor("#00c2cb"))
            painter.drawRoundedRect(2, 2, 28, 28, 7, 7)

            # Inner Q letter
            painter.setPen(QColor("#00c2cb"))
            font = QFont("Segoe UI", 13, QFont.Bold)
            painter.setFont(font)
            painter.drawText(pix.rect(), Qt.AlignCenter, "Q")
            painter.end()

            return QIcon(pix)

        def _build_menu(self) -> None:
            """Construct the right-click tray context menu."""
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu {
                    background-color: #171920;
                    border: 1px solid #2d323f;
                    border-radius: 8px;
                    padding: 6px;
                    color: #f3f4f6;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 13px;
                }
                QMenu::item {
                    padding: 7px 24px 7px 12px;
                    border-radius: 5px;
                }
                QMenu::item:selected {
                    background-color: #242936;
                    color: #00c2cb;
                }
                QMenu::separator {
                    height: 1px;
                    background-color: #262a35;
                    margin: 4px 6px;
                }
            """)

            open_action = menu.addAction(f"Open {APP_NAME}")
            open_action.triggered.connect(self.request_open.emit)

            menu.addSeparator()

            refresh_action = menu.addAction("Refresh App Index")
            refresh_action.triggered.connect(self.request_refresh.emit)

            settings_action = menu.addAction("Settings...")
            settings_action.triggered.connect(self.request_settings.emit)

            menu.addSeparator()

            about_action = menu.addAction(f"About {APP_NAME}")
            about_action.triggered.connect(self._show_about)

            exit_action = menu.addAction("Exit")
            exit_action.triggered.connect(self.request_exit.emit)

            self.setContextMenu(menu)

        def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
            """Handle tray click events (left click opens launcher)."""
            if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
                self.request_open.emit()

        def _show_about(self) -> None:
            """Show lightweight about notification."""
            self.showMessage(
                APP_NAME,
                f"Version {APP_VERSION}\nModern animated Windows application launcher.\nPress Ctrl+F anytime to search.",
                QSystemTrayIcon.Information,
                3000
            )
