"""
QuickFind Configuration and Constants
Defines application constants, UI styling parameters, and directory paths.
"""

import os
import sys

# Application Identity
APP_NAME = "QuickFind"
APP_DISPLAY_NAME = "QuickFind"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Premium Animated Windows Application Launcher"

# Paths
def get_app_dir() -> str:
    """Return the base directory for the application."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_user_data_dir() -> str:
    """Return the local app data directory for persistent settings and cache."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = os.path.expanduser("~")
    path = os.path.join(local_app_data, "QuickFind")
    os.makedirs(path, exist_ok=True)
    return path

def get_icon_cache_dir() -> str:
    """Return the directory for cached application icons."""
    path = os.path.join(get_user_data_dir(), "icon_cache")
    os.makedirs(path, exist_ok=True)
    return path

# Window & Animation Dimensions
SEARCH_BAR_WIDTH = 640
SEARCH_BAR_HEIGHT = 58
SEARCH_BAR_RADIUS = 16
RESULT_ITEM_HEIGHT = 44
MAX_VISIBLE_RESULTS_DEFAULT = 6
ANIMATION_DURATION_MS = 160  # Fast, crisp slide & fade animation

# Premium Dark Color Palette
COLOR_BG_TRANSPARENT = "transparent"
COLOR_BG_BAR = "#121418"               # Matte dark charcoal background
COLOR_BG_BAR_BORDER = "#252830"        # Subtle container border
COLOR_BG_RESULTS = "#15171d"           # Dark results panel
COLOR_BG_RESULTS_BORDER = "#282c37"    # Results panel border
COLOR_ITEM_HOVER = "#1c1f27"           # Hovered item background
COLOR_ITEM_SELECTED = "#222733"        # Selected item background
COLOR_ACCENT = "#00c2cb"               # Cyan accent for selection indicator
COLOR_ACCENT_HOVER = "#38bdf8"         # Brighter accent on hover/active
COLOR_TEXT_PRIMARY = "#f3f4f6"         # Clean white primary text
COLOR_TEXT_SECONDARY = "#8b92a5"       # Muted gray subtitle / path text
COLOR_TEXT_MUTED = "#525866"           # Hint / badge text
COLOR_INPUT_PLACEHOLDER = "#606775"    # Input placeholder text
COLOR_BADGE_BG = "#1e222b"             # Shortcut badge background
COLOR_BADGE_BORDER = "#2d3340"         # Shortcut badge border

# Default Settings
DEFAULT_SETTINGS = {
    "global_shortcut": "Ctrl+F",
    "launch_at_startup": False,
    "max_visible_results": 6,
    "prioritize_recent": True,
    "enable_global_shortcut": True,
    "theme": "dark_premium",
    "hide_on_blur": True,
}

# Supported Hotkey Modifiers and Keys
SUPPORTED_HOTKEYS = [
    "Ctrl+F",
    "Alt+Space",
    "Ctrl+Space",
    "Win+Space",
    "Ctrl+Shift+F",
    "Alt+F",
]
