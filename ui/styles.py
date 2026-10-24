"""
QuickFind Dark Theme Styles & Vector Icons
Provides advanced glassmorphism QSS stylesheets, palette definitions, and embedded SVG icons.
"""

from config import (
    COLOR_BG_BAR,
    COLOR_BG_BAR_BORDER,
    COLOR_BG_RESULTS,
    COLOR_BG_RESULTS_BORDER,
    COLOR_ITEM_HOVER,
    COLOR_ITEM_SELECTED,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_INPUT_PLACEHOLDER,
    COLOR_BADGE_BG,
    COLOR_BADGE_BORDER,
    SEARCH_BAR_RADIUS,
)

# SVG Icons
SEARCH_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00c2cb" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="11" cy="11" r="8"></circle>
  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
</svg>"""

APP_DEFAULT_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#00c2cb" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="18" height="18" rx="4" ry="4"></rect>
  <line x1="9" y1="9" x2="15" y2="15"></line>
  <line x1="15" y1="9" x2="9" y2="15"></line>
</svg>"""

SETTINGS_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8b92a5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="3"></circle>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
</svg>"""

# Complete Qt Stylesheet (QSS) with Glassmorphism, Elevated Shadows, and Sleek Dark Palette
SEARCH_WINDOW_QSS = f"""
/* Root Container */
QWidget#root_container {{
    background-color: transparent;
}}

/* Floating Search Bar Frame (Matte Glassmorphism) */
QFrame#search_bar_frame {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
        stop:0 rgba(22, 26, 34, 0.96), 
        stop:1 rgba(13, 15, 20, 0.98));
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-top: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: {SEARCH_BAR_RADIUS}px;
}}

/* Search Input LineEdit */
QLineEdit#search_input {{
    background-color: transparent;
    border: none;
    color: #ffffff;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    font-size: 16px;
    font-weight: 500;
    selection-background-color: {COLOR_ACCENT};
    selection-color: #0b1117;
    padding: 0px 6px;
}}

QLineEdit#search_input:focus {{
    outline: none;
}}

/* Shortcut Badge / Pill */
QLabel#shortcut_badge {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(32, 38, 49, 0.9),
        stop:1 rgba(21, 25, 33, 0.9));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 7px;
    color: #94a3b8;
    font-family: 'Segoe UI', sans-serif;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 9px;
    letter-spacing: 0.5px;
}}

/* Results Panel Frame (Translucent Charcoal Glass) */
QFrame#results_frame {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(18, 21, 28, 0.96),
        stop:1 rgba(11, 13, 18, 0.98));
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-top: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 14px;
}}

/* Results List Widget */
QListWidget#results_list {{
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px;
}}

QListWidget#results_list::item {{
    background-color: transparent;
    border-radius: 9px;
    padding: 0px 4px;
    margin-bottom: 2px;
}}

QListWidget#results_list::item:hover {{
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 9px;
}}

QListWidget#results_list::item:selected {{
    background-color: rgba(255, 255, 255, 0.09);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 9px;
}}

/* Smooth Sleek Scrollbar */
QScrollBar:vertical {{
    background-color: transparent;
    width: 5px;
    margin: 8px 3px 8px 0px;
}}

QScrollBar::handle:vertical {{
    background-color: rgba(255, 255, 255, 0.12);
    min-height: 24px;
    border-radius: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_ACCENT};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background-color: transparent;
}}

/* Empty State Label */
QLabel#empty_state_label {{
    color: #64748b;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 500;
    padding: 24px;
}}
"""

SETTINGS_DIALOG_QSS = f"""
QDialog {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #161921,
        stop:1 #0f1116);
    color: {COLOR_TEXT_PRIMARY};
    font-family: 'Segoe UI', sans-serif;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
}}

QLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 13px;
}}

QLabel#header_title {{
    font-size: 19px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.2px;
}}

QLabel#header_desc {{
    font-size: 12px;
    color: #94a3b8;
}}

QGroupBox {{
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: {COLOR_ACCENT};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 11px;
    margin-top: 14px;
    padding-top: 18px;
    background: rgba(255, 255, 255, 0.02);
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {COLOR_ACCENT};
}}

QComboBox {{
    background-color: #1a1e27;
    border: 1px solid #2d3342;
    border-radius: 8px;
    color: #ffffff;
    padding: 6px 12px;
    font-size: 13px;
}}

QComboBox:focus {{
    border-color: {COLOR_ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: #1a1e27;
    border: 1px solid #2d3342;
    selection-background-color: rgba(0, 194, 203, 0.2);
    selection-color: {COLOR_ACCENT};
    color: #ffffff;
    padding: 4px;
}}

QCheckBox {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 13px;
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #383f50;
    background-color: #1a1e27;
}}

QCheckBox::indicator:hover {{
    border-color: {COLOR_ACCENT};
}}

QCheckBox::indicator:checked {{
    background-color: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}

QSlider::groove:horizontal {{
    height: 6px;
    background-color: #242936;
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLOR_ACCENT},
        stop:1 {COLOR_ACCENT_HOVER});
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: #ffffff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QPushButton {{
    background-color: #202430;
    border: 1px solid #313746;
    border-radius: 8px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 500;
    padding: 8px 16px;
}}

QPushButton:hover {{
    background-color: #2b3141;
    border-color: #424a5d;
}}

QPushButton#primary_button {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLOR_ACCENT},
        stop:1 {COLOR_ACCENT_HOVER});
    border: none;
    color: #080d12;
    font-weight: 700;
    letter-spacing: 0.2px;
}}

QPushButton#primary_button:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLOR_ACCENT_HOVER},
        stop:1 #7dd3fc);
}}
"""
