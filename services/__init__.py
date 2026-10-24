"""Services package for QuickFind."""
from services.app_scanner import AppScanner, AppEntry
from services.search_engine import SearchEngine, SearchResult
from services.shortcut_resolver import resolve_shortcut, ShortcutInfo
from services.icon_extractor import IconExtractor

__all__ = [
    "AppScanner",
    "AppEntry",
    "SearchEngine",
    "SearchResult",
    "resolve_shortcut",
    "ShortcutInfo",
    "IconExtractor",
]
