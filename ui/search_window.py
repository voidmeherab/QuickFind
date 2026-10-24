"""
QuickFind Floating Search Window (PySide6)
Implements the animated top-center floating search bar, instant suggestions panel,
arrow key navigation, spring physics entrance/exit, and smooth height unfold animations.
"""

import os
import sys
import ctypes
from typing import Optional, List

try:
    from PySide6.QtCore import (
        Qt, QPoint, QRect, QSize, QPropertyAnimation, QEasingCurve,
        QParallelAnimationGroup, Signal, Slot, QTimer, QEvent
    )
    from PySide6.QtGui import (
        QIcon, QPixmap, QPainter, QColor, QFont, QKeyEvent, QMouseEvent,
        QGuiApplication, QCursor
    )
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
        QListWidget, QListWidgetItem, QFrame, QGraphicsDropShadowEffect,
        QApplication, QSizePolicy
    )
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from config import (
    APP_NAME, SEARCH_BAR_WIDTH, SEARCH_BAR_HEIGHT, SEARCH_BAR_RADIUS,
    RESULT_ITEM_HEIGHT, ANIMATION_DURATION_MS, COLOR_ACCENT,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY
)
from ui.styles import SEARCH_WINDOW_QSS, SEARCH_ICON_SVG
from services.search_engine import SearchEngine, SearchResult
from core.app_launcher import AppLauncher
from storage.settings import SettingsManager


if PYSIDE6_AVAILABLE:

    class ResultItemWidget(QWidget):
        """Custom widget rendering a single application search result with ultra-clean Spotlight/Raycast styling."""

        def __init__(self, result: SearchResult, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.result = result
            self.setFixedHeight(RESULT_ITEM_HEIGHT)

            layout = QHBoxLayout(self)
            layout.setContentsMargins(14, 0, 14, 0)
            layout.setSpacing(14)
            layout.setAlignment(Qt.AlignVCenter)

            # Icon Container (crisp 28x28)
            self.icon_label = QLabel(self)
            self.icon_label.setFixedSize(28, 28)
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setStyleSheet("background: transparent;")

            pixmap = self._load_icon(result.app.icon_path)
            self.icon_label.setPixmap(pixmap)
            layout.addWidget(self.icon_label)

            # Application Name Only (No path, no extra badges)
            self.title_label = QLabel(result.app.name, self)
            self.title_label.setStyleSheet(
                "color: #f1f5f9; font-size: 14.5px; font-weight: 500; background: transparent; letter-spacing: -0.2px;"
            )
            layout.addWidget(self.title_label, 1)

        def _load_icon(self, icon_path: Optional[str]) -> QPixmap:
            """Load cached PNG icon or generate a stylish fallback icon."""
            if icon_path and os.path.exists(icon_path):
                try:
                    pix = QPixmap(icon_path)
                    if not pix.isNull():
                        return pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                except Exception:
                    pass

            # Fallback vector-styled icon
            fallback = QPixmap(28, 28)
            fallback.fill(Qt.transparent)
            painter = QPainter(fallback)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("#1e2638"))
            painter.setPen(QColor(COLOR_ACCENT))
            painter.drawRoundedRect(1, 1, 26, 26, 6, 6)

            painter.setPen(QColor("#ffffff"))
            font = QFont("Segoe UI", 11, QFont.Bold)
            painter.setFont(font)
            initial = (self.result.app.name[:1] if self.result.app.name else "A").upper()
            painter.drawText(QRect(0, 0, 28, 28), Qt.AlignCenter, initial)
            painter.end()
            return fallback


    def force_foreground_window(hwnd: int) -> None:
        """Ensure QuickFind acquires genuine Windows OS foreground focus for immediate typing."""
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Unlock SetForegroundWindow (0x0002 = LSFW_UNLOCK)
            user32.LockSetForegroundWindow(2)

            cur_thread = kernel32.GetCurrentThreadId()
            fg_hwnd = user32.GetForegroundWindow()
            fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0

            if fg_thread and fg_thread != cur_thread:
                user32.AttachThreadInput(cur_thread, fg_thread, True)
                user32.ShowWindow(hwnd, 5)  # SW_SHOW
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.SetFocus(hwnd)
                user32.AttachThreadInput(cur_thread, fg_thread, False)
            else:
                user32.ShowWindow(hwnd, 5)  # SW_SHOW
                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
                user32.SetFocus(hwnd)
        except Exception as e:
            print(f"[QuickFind] Focus error: {e}", file=sys.stderr)


    def set_no_taskbar(hwnd: int) -> None:
        """Ensure WS_EX_TOOLWINDOW is set and WS_EX_APPWINDOW is removed so no taskbar icon appears."""
        try:
            user32 = ctypes.windll.user32
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_APPWINDOW = 0x00040000
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass


    class SearchWindow(QWidget):
        """Top-center floating search bar and suggestions panel with smooth animation dynamics."""

        request_settings = Signal()
        request_refresh = Signal()

        def __init__(
            self,
            search_engine: SearchEngine,
            app_launcher: AppLauncher,
            settings: SettingsManager,
            parent: Optional[QWidget] = None
        ):
            super().__init__(parent)
            self.search_engine = search_engine
            self.app_launcher = app_launcher
            self.settings = settings

            self._is_animating = False
            self._can_blur_hide = False
            self._target_y = 55
            self._current_results: List[SearchResult] = []

            # Background outside click monitor timer
            self.blur_timer = QTimer(self)
            self.blur_timer.setInterval(50)
            self.blur_timer.timeout.connect(self._check_focus_and_outside_click)

            self._init_window()
            self._build_ui()
            self._setup_animations()

        def _init_window(self) -> None:
            """Set window flags and translucency for floating mini application look without taskbar icon."""
            self.setObjectName("root_container")
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool
            )
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setStyleSheet(SEARCH_WINDOW_QSS)

        def _build_ui(self) -> None:
            """Construct search bar, list widget, and layout."""
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(16, 16, 16, 16)
            self.main_layout.setSpacing(10)

            # 1. Search Bar Frame
            self.search_bar_frame = QFrame(self)
            self.search_bar_frame.setObjectName("search_bar_frame")
            self.search_bar_frame.setFixedHeight(SEARCH_BAR_HEIGHT)

            # Drop shadow effect for floating search bar
            bar_shadow = QGraphicsDropShadowEffect(self.search_bar_frame)
            bar_shadow.setBlurRadius(32)
            bar_shadow.setColor(QColor(0, 0, 0, 180))
            bar_shadow.setOffset(0, 8)
            self.search_bar_frame.setGraphicsEffect(bar_shadow)

            bar_layout = QHBoxLayout(self.search_bar_frame)
            bar_layout.setContentsMargins(18, 0, 16, 0)
            bar_layout.setSpacing(14)

            # Glowing Cyan Search Icon
            self.search_icon_label = QLabel(self.search_bar_frame)
            self.search_icon_label.setFixedSize(22, 22)
            self.search_icon_label.setStyleSheet("background: transparent;")
            self._set_svg_icon(self.search_icon_label, SEARCH_ICON_SVG)
            bar_layout.addWidget(self.search_icon_label)

            # Search Input
            self.search_input = QLineEdit(self.search_bar_frame)
            self.search_input.setObjectName("search_input")
            self.search_input.setPlaceholderText("Search apps...")
            self.search_input.textChanged.connect(self._on_query_changed)
            self.search_input.installEventFilter(self)
            self.search_input.returnPressed.connect(self._on_enter_pressed)
            bar_layout.addWidget(self.search_input, 1)

            # Shortcut Pill Badge removed per user request
            self.shortcut_badge = None

            self.main_layout.addWidget(self.search_bar_frame)

            # 2. Results Container Frame
            self.results_frame = QFrame(self)
            self.results_frame.setObjectName("results_frame")
            self.results_frame.setVisible(False)

            # Drop shadow for results panel
            res_shadow = QGraphicsDropShadowEffect(self.results_frame)
            res_shadow.setBlurRadius(36)
            res_shadow.setColor(QColor(0, 0, 0, 190))
            res_shadow.setOffset(0, 10)
            self.results_frame.setGraphicsEffect(res_shadow)

            results_layout = QVBoxLayout(self.results_frame)
            results_layout.setContentsMargins(4, 4, 4, 4)
            results_layout.setSpacing(0)

            # List Widget
            self.results_list = QListWidget(self.results_frame)
            self.results_list.setObjectName("results_list")
            self.results_list.setSelectionMode(QListWidget.SingleSelection)
            self.results_list.setFocusPolicy(Qt.NoFocus)
            self.results_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.results_list.itemClicked.connect(self._on_item_clicked)
            results_layout.addWidget(self.results_list)

            # Empty State Label
            self.empty_label = QLabel("No matching applications found", self.results_frame)
            self.empty_label.setObjectName("empty_state_label")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setVisible(False)
            results_layout.addWidget(self.empty_label)

            self.main_layout.addWidget(self.results_frame)

            self.setFixedWidth(SEARCH_BAR_WIDTH + 32)

        def _setup_animations(self) -> None:
            """Configure smooth slide and fade animations with spring overshoot dynamics."""
            # 1. Open Animations
            self.open_pos_anim = QPropertyAnimation(self, b"pos")
            self.open_pos_anim.setDuration(220)
            self.open_pos_anim.setEasingCurve(QEasingCurve.OutBack)

            self.open_opacity_anim = QPropertyAnimation(self, b"windowOpacity")
            self.open_opacity_anim.setDuration(180)
            self.open_opacity_anim.setEasingCurve(QEasingCurve.OutCubic)

            self.open_group = QParallelAnimationGroup(self)
            self.open_group.addAnimation(self.open_pos_anim)
            self.open_group.addAnimation(self.open_opacity_anim)

            # 2. Close Animations (completely separate from open group)
            self.close_pos_anim = QPropertyAnimation(self, b"pos")
            self.close_pos_anim.setDuration(140)
            self.close_pos_anim.setEasingCurve(QEasingCurve.InCubic)

            self.close_opacity_anim = QPropertyAnimation(self, b"windowOpacity")
            self.close_opacity_anim.setDuration(140)
            self.close_opacity_anim.setEasingCurve(QEasingCurve.InCubic)

            self.close_group = QParallelAnimationGroup(self)
            self.close_group.addAnimation(self.close_pos_anim)
            self.close_group.addAnimation(self.close_opacity_anim)
            self.close_group.finished.connect(self._on_close_finished)

            # 3. Results Panel Height Expansion Animation
            self.height_anim = QPropertyAnimation(self.results_frame, b"maximumHeight")
            self.height_anim.setDuration(150)
            self.height_anim.setEasingCurve(QEasingCurve.OutCubic)

        def _on_close_finished(self) -> None:
            """Triggered strictly when close animation completes."""
            self.hide()
            self._is_animating = False
            self.search_input.clear()
            self._update_search_results("", animate=False)

        def _set_svg_icon(self, label: QLabel, svg_data: str) -> None:
            """Render raw SVG data into a QLabel pixmap."""
            try:
                from PySide6.QtSvg import QSvgRenderer
                renderer = QSvgRenderer(svg_data.encode("utf-8"))
                pix = QPixmap(label.size())
                pix.fill(Qt.transparent)
                painter = QPainter(pix)
                renderer.render(painter)
                painter.end()
                label.setPixmap(pix)
            except Exception:
                pass

        def show_launcher(self) -> None:
            """Reveal the launcher at the top-center with smooth spring animation and auto-focus."""
            # Stop any running close animation immediately
            self.close_group.stop()
            self._is_animating = False
            self._can_blur_hide = False

            if self.isVisible() and self.windowOpacity() > 0.8:
                # If already open, select existing text and focus
                self.search_input.selectAll()
                self.search_input.setFocus()
                force_foreground_window(int(self.winId()))
                self.blur_timer.start(50)
                QTimer.singleShot(250, lambda: setattr(self, "_can_blur_hide", True))
                return

            self._center_at_top()

            # Dynamic spring entrance starting from y - 35
            start_pos = QPoint(self.x(), self._target_y - 35)
            end_pos = QPoint(self.x(), self._target_y)

            self.open_pos_anim.setStartValue(start_pos)
            self.open_pos_anim.setEndValue(end_pos)

            self.open_opacity_anim.setStartValue(0.0)
            self.open_opacity_anim.setEndValue(1.0)

            self.move(start_pos)
            self.setWindowOpacity(0.0)
            self.show()
            self.raise_()
            self.activateWindow()

            hwnd = int(self.winId())
            set_no_taskbar(hwnd)
            force_foreground_window(hwnd)

            # Trigger opening animation
            self.open_group.stop()
            self.open_group.start()

            # Refresh search results based on current query
            self._update_search_results(self.search_input.text(), animate=False)

            # Focus search input for immediate typing without needing an extra click
            self.search_input.setFocus()
            self.search_input.selectAll()
            QTimer.singleShot(40, self.search_input.setFocus)
            QTimer.singleShot(40, lambda: force_foreground_window(int(self.winId())))

            # Start outside click monitor & enable blur-to-hide after brief entrance grace
            self.blur_timer.start(50)
            QTimer.singleShot(250, lambda: setattr(self, "_can_blur_hide", True))

        def hide_launcher(self) -> None:
            """Dismiss the launcher with snappy slide-up and fade-out."""
            self.blur_timer.stop()
            self._can_blur_hide = False
            if not self.isVisible() or self._is_animating:
                return

            self._is_animating = True
            self.open_group.stop()

            end_pos = QPoint(self.x(), self._target_y - 25)

            self.close_pos_anim.setStartValue(self.pos())
            self.close_pos_anim.setEndValue(end_pos)

            self.close_opacity_anim.setStartValue(self.windowOpacity())
            self.close_opacity_anim.setEndValue(0.0)

            self.close_group.stop()
            self.close_group.start()

        def _check_focus_and_outside_click(self) -> None:
            """Check if user clicked outside or switched to another window, and dismiss."""
            if not self.isVisible() or self._is_animating:
                return
            if not getattr(self, "_can_blur_hide", False):
                return

            hwnd = int(self.winId())
            fg_hwnd = ctypes.windll.user32.GetForegroundWindow()

            # If foreground window is another application / desktop
            if fg_hwnd and fg_hwnd != hwnd:
                self.hide_launcher()
                return

            # Real-time mouse click outside window bounds (VK_LBUTTON=0x01, VK_RBUTTON=0x02)
            user32 = ctypes.windll.user32
            if (user32.GetAsyncKeyState(0x01) & 0x8000) or (user32.GetAsyncKeyState(0x02) & 0x8000):
                cursor_pos = QCursor.pos()
                if not self.geometry().contains(cursor_pos):
                    self.hide_launcher()

        def _center_at_top(self) -> None:
            """Center window horizontally near the top of the primary display."""
            screen = QGuiApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                x = geom.x() + (geom.width() - self.width()) // 2
                self._target_y = geom.y() + 50
                self.move(x, self._target_y)

        def _on_query_changed(self, text: str) -> None:
            """Handle as-you-type search queries."""
            self._update_search_results(text, animate=True)

        def _update_search_results(self, query: str, animate: bool = True) -> None:
            """Query the search engine and update the suggestions UI with height transition."""
            max_results = self.settings.get("max_visible_results", 6)
            prioritize_recent = self.settings.get("prioritize_recent", True)

            results = self.search_engine.search(
                query=query,
                max_results=max_results,
                prioritize_recent=prioritize_recent
            )
            self._current_results = results
            self.results_list.clear()

            if not query.strip() and not results:
                self.results_frame.setVisible(False)
                self.adjustSize()
                return

            if not results:
                self.results_list.setVisible(False)
                self.empty_label.setText(f"No applications found for '{query}'")
                self.empty_label.setVisible(True)
                self.results_frame.setVisible(True)
                self._animate_results_height(80, animate)
                return

            self.empty_label.setVisible(False)
            self.results_list.setVisible(True)

            # Populate results list
            for r in results:
                item = QListWidgetItem(self.results_list)
                item.setSizeHint(QSize(self.results_list.width(), RESULT_ITEM_HEIGHT))
                widget = ResultItemWidget(r, self.results_list)
                self.results_list.setItemWidget(item, widget)

            # Select first item by default
            if results:
                self.results_list.setCurrentRow(0)

            # Calculate and animate height expansion
            num_visible = min(len(results), max_results)
            calculated_height = (num_visible * RESULT_ITEM_HEIGHT) + 14
            self.results_list.setFixedHeight(calculated_height)
            self._animate_results_height(calculated_height + 8, animate)

        def _animate_results_height(self, target_h: int, animate: bool) -> None:
            """Smoothly unfold the results panel height."""
            self.results_frame.setVisible(True)
            if animate and self.isVisible():
                self.height_anim.stop()
                self.height_anim.setStartValue(self.results_frame.height())
                self.height_anim.setEndValue(target_h)
                self.height_anim.start()
            else:
                self.results_frame.setMaximumHeight(target_h)
                self.results_frame.setFixedHeight(target_h)
            self.adjustSize()

        def _on_item_clicked(self, item: QListWidgetItem) -> None:
            """Launch the clicked application."""
            row = self.results_list.row(item)
            self._launch_result_at_row(row)

        def _launch_result_at_row(self, row: int) -> None:
            """Launch application at given result index and dismiss launcher."""
            if 0 <= row < len(self._current_results):
                res = self._current_results[row]
                success, err = self.app_launcher.launch(
                    target_path=res.app.target_path,
                    arguments=res.app.arguments,
                    working_dir=res.app.working_dir,
                    app_id=res.app.id
                )
                self.hide_launcher()
                if not success:
                    print(f"[QuickFind] Launch failed: {err}", file=sys.stderr)

        def eventFilter(self, obj, event):
            """Intercept keyboard events on the search input to handle navigation and launch."""
            if obj == self.search_input and event.type() == QEvent.KeyPress:
                key = event.key()
                if key == Qt.Key_Escape:
                    self.hide_launcher()
                    return True
                elif key in (Qt.Key_Down, Qt.Key_Tab):
                    current_row = self.results_list.currentRow()
                    count = self.results_list.count()
                    if count > 0:
                        next_row = (current_row + 1) % count
                        self.results_list.setCurrentRow(next_row)
                        self.results_list.scrollToItem(self.results_list.item(next_row))
                    return True
                elif key in (Qt.Key_Up, Qt.Key_Backtab):
                    current_row = self.results_list.currentRow()
                    count = self.results_list.count()
                    if count > 0:
                        prev_row = (current_row - 1 + count) % count
                        self.results_list.setCurrentRow(prev_row)
                        self.results_list.scrollToItem(self.results_list.item(prev_row))
                    return True
                elif key in (Qt.Key_Return, Qt.Key_Enter):
                    self._on_enter_pressed()
                    return True
            return super().eventFilter(obj, event)

        def _on_enter_pressed(self) -> None:
            """Launch current selection when Enter is pressed."""
            current_row = self.results_list.currentRow()
            if current_row >= 0:
                self._launch_result_at_row(current_row)
            elif self._current_results:
                self._launch_result_at_row(0)

        def keyPressEvent(self, event: QKeyEvent) -> None:
            """Handle keyboard navigation: Arrows, Tab, Enter, Escape."""
            key = event.key()

            if key == Qt.Key_Escape:
                self.hide_launcher()
                event.accept()
                return

            if key in (Qt.Key_Down, Qt.Key_Tab):
                current_row = self.results_list.currentRow()
                count = self.results_list.count()
                if count > 0:
                    next_row = (current_row + 1) % count
                    self.results_list.setCurrentRow(next_row)
                    self.results_list.scrollToItem(self.results_list.item(next_row))
                event.accept()
                return

            if key in (Qt.Key_Up, Qt.Key_Backtab):
                current_row = self.results_list.currentRow()
                count = self.results_list.count()
                if count > 0:
                    prev_row = (current_row - 1 + count) % count
                    self.results_list.setCurrentRow(prev_row)
                    self.results_list.scrollToItem(self.results_list.item(prev_row))
                event.accept()
                return

            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._on_enter_pressed()
                event.accept()
                return

            super().keyPressEvent(event)

        def changeEvent(self, event) -> None:
            """Close launcher when losing focus if hide_on_blur is enabled."""
            if event.type() in (QEvent.ActivationChange, QEvent.Type.ActivationChange):
                if getattr(self, "_can_blur_hide", False):
                    if not self.isActiveWindow():
                        focus_w = QApplication.focusWidget()
                        if focus_w is None or focus_w.window() != self:
                            self.hide_launcher()
            super().changeEvent(event)
