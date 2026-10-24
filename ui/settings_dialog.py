"""
QuickFind Settings Dialog (PySide6)
Allows user to configure the global shortcut, startup behavior, results count,
recency ranking, and trigger manual index re-scans.
"""

from typing import Optional, Callable

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
        QCheckBox, QSlider, QPushButton, QGroupBox, QFrame
    )
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from config import SUPPORTED_HOTKEYS, APP_NAME, APP_VERSION
from storage.settings import SettingsManager
from ui.styles import SETTINGS_DIALOG_QSS


if PYSIDE6_AVAILABLE:

    class SettingsDialog(QDialog):
        """Settings configuration window."""

        settings_saved = Signal()
        request_rescan = Signal()

        def __init__(self, settings: SettingsManager, on_rescan: Optional[Callable[[], int]] = None, parent: Optional[QDialog] = None):
            super().__init__(parent)
            self.settings = settings
            self.on_rescan = on_rescan

            self._init_dialog()
            self._build_ui()
            self._load_current_settings()

        def _init_dialog(self) -> None:
            self.setWindowTitle(f"{APP_NAME} Settings")
            self.setFixedSize(480, 520)
            self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
            self.setStyleSheet(SETTINGS_DIALOG_QSS)

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(16)

            # Header
            header_layout = QVBoxLayout()
            header_layout.setSpacing(4)
            title = QLabel(f"{APP_NAME} Preferences", self)
            title.setObjectName("header_title")
            header_layout.addWidget(title)

            desc = QLabel(f"Version {APP_VERSION} — Customize your launcher experience", self)
            desc.setObjectName("header_desc")
            header_layout.addWidget(desc)
            layout.addLayout(header_layout)

            # 1. Hotkey Section
            hotkey_group = QGroupBox("Global Shortcut", self)
            hotkey_layout = QVBoxLayout(hotkey_group)
            hotkey_layout.setSpacing(10)

            hk_row = QHBoxLayout()
            hk_label = QLabel("Activation Shortcut:", hotkey_group)
            self.hotkey_combo = QComboBox(hotkey_group)
            for hk in SUPPORTED_HOTKEYS:
                self.hotkey_combo.addItem(hk)
            hk_row.addWidget(hk_label)
            hk_row.addWidget(self.hotkey_combo, 1)
            hotkey_layout.addLayout(hk_row)

            self.enable_hotkey_check = QCheckBox("Enable system-wide global shortcut", hotkey_group)
            hotkey_layout.addWidget(self.enable_hotkey_check)
            layout.addWidget(hotkey_group)

            # 2. General Preferences Section
            pref_group = QGroupBox("Search & Behavior", self)
            pref_layout = QVBoxLayout(pref_group)
            pref_layout.setSpacing(12)

            self.startup_check = QCheckBox("Start QuickFind automatically with Windows", pref_group)
            pref_layout.addWidget(self.startup_check)

            self.recent_check = QCheckBox("Prioritize frequently and recently used applications", pref_group)
            pref_layout.addWidget(self.recent_check)

            # Results Count Slider
            slider_row = QHBoxLayout()
            slider_label = QLabel("Maximum visible results:", pref_group)
            self.slider_val_label = QLabel("6", pref_group)
            self.slider_val_label.setStyleSheet("color: #00c2cb; font-weight: 700; min-width: 20px;")
            self.results_slider = QSlider(Qt.Horizontal, pref_group)
            self.results_slider.setRange(3, 10)
            self.results_slider.setValue(6)
            self.results_slider.valueChanged.connect(lambda v: self.slider_val_label.setText(str(v)))

            slider_row.addWidget(slider_label)
            slider_row.addWidget(self.results_slider, 1)
            slider_row.addWidget(self.slider_val_label)
            pref_layout.addLayout(slider_row)

            layout.addWidget(pref_group)

            # 3. Application Index Section
            index_group = QGroupBox("Index & Cache", self)
            index_layout = QHBoxLayout(index_group)
            index_layout.setSpacing(12)

            self.status_label = QLabel("Index status: Ready", index_group)
            self.status_label.setStyleSheet("color: #8b92a5; font-size: 12px;")
            index_layout.addWidget(self.status_label, 1)

            self.rescan_btn = QPushButton("Refresh Index", index_group)
            self.rescan_btn.clicked.connect(self._handle_rescan)
            index_layout.addWidget(self.rescan_btn)

            layout.addWidget(index_group)

            layout.addStretch()

            # Buttons (Save / Cancel)
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)
            btn_layout.addStretch()

            cancel_btn = QPushButton("Cancel", self)
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

            save_btn = QPushButton("Save Changes", self)
            save_btn.setObjectName("primary_button")
            save_btn.clicked.connect(self._save_and_close)
            btn_layout.addWidget(save_btn)

            layout.addLayout(btn_layout)

        def _load_current_settings(self) -> None:
            """Populate UI controls with current stored settings."""
            cur_hk = self.settings.get("global_shortcut", "Ctrl+F")
            idx = self.hotkey_combo.findText(cur_hk)
            if idx >= 0:
                self.hotkey_combo.setCurrentIndex(idx)
            else:
                self.hotkey_combo.addItem(cur_hk)
                self.hotkey_combo.setCurrentText(cur_hk)

            self.enable_hotkey_check.setChecked(self.settings.get("enable_global_shortcut", True))
            self.startup_check.setChecked(self.settings.get("launch_at_startup", False))
            self.recent_check.setChecked(self.settings.get("prioritize_recent", True))

            max_res = self.settings.get("max_visible_results", 6)
            self.results_slider.setValue(max_res)
            self.slider_val_label.setText(str(max_res))

        def _save_and_close(self) -> None:
            """Save modified settings and emit update signals."""
            self.settings.set("global_shortcut", self.hotkey_combo.currentText())
            self.settings.set("enable_global_shortcut", self.enable_hotkey_check.isChecked())
            self.settings.set("launch_at_startup", self.startup_check.isChecked())
            self.settings.set("prioritize_recent", self.recent_check.isChecked())
            self.settings.set("max_visible_results", self.results_slider.value())

            self.settings_saved.emit()
            self.accept()

        def _handle_rescan(self) -> None:
            """Trigger application index refresh."""
            self.status_label.setText("Scanning applications...")
            self.rescan_btn.setEnabled(False)

            if self.on_rescan:
                count = self.on_rescan()
                self.status_label.setText(f"Indexed {count} applications")
            else:
                self.request_rescan.emit()
                self.status_label.setText("Index refresh requested")

            self.rescan_btn.setEnabled(True)
