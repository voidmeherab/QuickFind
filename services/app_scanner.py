"""
Windows Application Scanner
Discovers installed applications from Start Menus, Desktops, Windows Registry App Paths,
and common system executables without recursive full-drive scans.
"""

import os
import re
import sys
import winreg
from typing import List, Dict, Optional, Set
from services.shortcut_resolver import resolve_shortcut
from services.icon_extractor import IconExtractor


class AppEntry:
    """Represents a discovered launchable application."""

    def __init__(
        self,
        name: str,
        target_path: str,
        arguments: str = "",
        working_dir: str = "",
        icon_path: Optional[str] = None,
        source: str = "start_menu",
        is_uwp: bool = False,
    ):
        self.name = name.strip()
        self.target_path = target_path.strip()
        self.arguments = arguments.strip()
        self.working_dir = working_dir.strip()
        self.icon_path = icon_path  # Path to cached PNG icon
        self.source = source
        self.is_uwp = is_uwp

        # Generate a unique canonical identifier
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Create a stable canonical ID for deduplication and launch history tracking."""
        clean_target = self.target_path.lower().replace("/", "\\")
        return f"{self.name.lower()}|{clean_target}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "target_path": self.target_path,
            "arguments": self.arguments,
            "working_dir": self.working_dir,
            "icon_path": self.icon_path,
            "source": self.source,
            "is_uwp": self.is_uwp,
        }

    def __repr__(self):
        return f"<AppEntry '{self.name}' ({self.target_path})>"


# Common excluded names and patterns
EXCLUDED_PATTERNS = [
    re.compile(r"uninstall", re.IGNORECASE),
    re.compile(r"unins\d+", re.IGNORECASE),
    re.compile(r"^readme", re.IGNORECASE),
    re.compile(r"^help", re.IGNORECASE),
    re.compile(r"^documentation", re.IGNORECASE),
    re.compile(r"^release\s*notes", re.IGNORECASE),
    re.compile(r"\bmanual\b", re.IGNORECASE),
    re.compile(r"\blicense\b", re.IGNORECASE),
    re.compile(r"\bconfiguration\s*wizard\b", re.IGNORECASE),
]

EXCLUDED_EXTENSIONS = {".txt", ".pdf", ".chm", ".html", ".htm", ".url", ".rtf", ".doc", ".docx"}

# Common Windows System utilities to index
COMMON_SYSTEM_APPS = [
    ("Calculator", "calc.exe", "Windows Calculator"),
    ("Notepad", "notepad.exe", "Text Editor"),
    ("Paint", "mspaint.exe", "Image Editor"),
    ("Command Prompt", "cmd.exe", "Windows Command Processor"),
    ("PowerShell", "powershell.exe", "Windows PowerShell"),
    ("Windows Terminal", "wt.exe", "Modern Terminal Emulator"),
    ("Task Manager", "taskmgr.exe", "System Resource Monitor"),
    ("File Explorer", "explorer.exe", "File Manager"),
    ("Registry Editor", "regedit.exe", "Windows Registry Editor"),
    ("Snipping Tool", "SnippingTool.exe", "Screen Capture Utility"),
    ("Control Panel", "control.exe", "System Settings & Configuration"),
    ("Resource Monitor", "resmon.exe", "Real-Time Resource Monitor"),
    ("Disk Cleanup", "cleanmgr.exe", "Free Up Drive Space"),
    ("Character Map", "charmap.exe", "Unicode Character Map"),
    ("Device Manager", "devmgmt.msc", "Device Hardware Management"),
    ("Services", "services.msc", "Windows Background Services"),
]


class AppScanner:
    """Discovers installed Windows applications."""

    def __init__(self, icon_extractor: Optional[IconExtractor] = None):
        self.icon_extractor = icon_extractor or IconExtractor()

    def scan_all(self) -> List[AppEntry]:
        """
        Scan all standard Windows application discovery sources.
        Returns a deduplicated, filtered list of AppEntry instances.
        """
        apps: List[AppEntry] = []
        seen_targets: Set[str] = set()
        seen_names: Set[str] = set()

        # 1. Start Menus (User & Common)
        start_menu_dirs = self._get_start_menu_dirs()
        for folder in start_menu_dirs:
            if os.path.exists(folder):
                self._scan_directory(folder, apps, seen_targets, seen_names, source="start_menu")

        # 2. Desktops (User & Public)
        desktop_dirs = self._get_desktop_dirs()
        for folder in desktop_dirs:
            if os.path.exists(folder):
                self._scan_directory(folder, apps, seen_targets, seen_names, source="desktop")

        # 3. Windows Registry App Paths
        self._scan_registry_app_paths(apps, seen_targets, seen_names)

        # 4. Common Windows System Utilities
        self._add_system_apps(apps, seen_targets, seen_names)

        return apps

    def _get_start_menu_dirs(self) -> List[str]:
        """Return user and system Start Menu paths."""
        dirs = []
        appdata = os.environ.get("APPDATA")
        if appdata:
            dirs.append(os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs"))

        programdata = os.environ.get("PROGRAMDATA")
        if programdata:
            dirs.append(os.path.join(programdata, r"Microsoft\Windows\Start Menu\Programs"))

        return dirs

    def _get_desktop_dirs(self) -> List[str]:
        """Return user and public desktop paths."""
        dirs = []
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            dirs.append(os.path.join(userprofile, "Desktop"))

        public = os.environ.get("PUBLIC")
        if public:
            dirs.append(os.path.join(public, "Desktop"))

        return dirs

    def _scan_directory(
        self,
        base_dir: str,
        apps: List[AppEntry],
        seen_targets: Set[str],
        seen_names: Set[str],
        source: str
    ) -> None:
        """Recursively scan a directory for .lnk and .exe files."""
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()

                # Process shortcuts
                if ext == ".lnk":
                    lnk_path = os.path.join(root, file)
                    raw_name = os.path.splitext(file)[0]
                    clean_name = self._clean_app_name(raw_name)

                    if self._is_excluded(clean_name, lnk_path):
                        continue

                    shortcut = resolve_shortcut(lnk_path)
                    if not shortcut or not shortcut.target_path:
                        continue

                    target = shortcut.target_path
                    norm_target = target.lower().strip()

                    # Filter out non-executable targets if target is a file
                    if os.path.isfile(target):
                        target_ext = os.path.splitext(target)[1].lower()
                        if target_ext in EXCLUDED_EXTENSIONS:
                            continue

                    if self._is_excluded(clean_name, target):
                        continue

                    # Deduplication
                    if norm_target in seen_targets and clean_name.lower() in seen_names:
                        continue

                    # Extract icon
                    icon_png = self.icon_extractor.get_icon_path(
                        target, icon_source=shortcut.icon_path or lnk_path, icon_index=shortcut.icon_index
                    )

                    entry = AppEntry(
                        name=clean_name,
                        target_path=target,
                        arguments=shortcut.arguments,
                        working_dir=shortcut.working_dir,
                        icon_path=icon_png,
                        source=source
                    )

                    apps.append(entry)
                    seen_targets.add(norm_target)
                    seen_names.add(clean_name.lower())

                # Process raw .exe in desktop or start menu roots
                elif ext == ".exe":
                    exe_path = os.path.join(root, file)
                    raw_name = os.path.splitext(file)[0]
                    clean_name = self._clean_app_name(raw_name)

                    if self._is_excluded(clean_name, exe_path):
                        continue

                    norm_target = exe_path.lower().strip()
                    if norm_target in seen_targets:
                        continue

                    icon_png = self.icon_extractor.get_icon_path(exe_path)

                    entry = AppEntry(
                        name=clean_name,
                        target_path=exe_path,
                        icon_path=icon_png,
                        source=source
                    )

                    apps.append(entry)
                    seen_targets.add(norm_target)
                    seen_names.add(clean_name.lower())

    def _scan_registry_app_paths(self, apps: List[AppEntry], seen_targets: Set[str], seen_names: Set[str]) -> None:
        """Scan App Paths registry keys for registered applications."""
        reg_roots = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        ]

        for hkey, subkey_path in reg_roots:
            try:
                with winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        try:
                            app_sub = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, app_sub, 0, winreg.KEY_READ) as app_key:
                                target_val, _ = winreg.QueryValueEx(app_key, "")
                                if target_val and isinstance(target_val, str):
                                    target_clean = target_val.strip(' "')
                                    if os.path.isfile(target_clean):
                                        norm_target = target_clean.lower()
                                        raw_name = os.path.splitext(app_sub)[0]
                                        clean_name = self._clean_app_name(raw_name)

                                        if norm_target in seen_targets:
                                            continue
                                        if self._is_excluded(clean_name, target_clean):
                                            continue

                                        icon_png = self.icon_extractor.get_icon_path(target_clean)
                                        entry = AppEntry(
                                            name=clean_name,
                                            target_path=target_clean,
                                            icon_path=icon_png,
                                            source="registry"
                                        )
                                        apps.append(entry)
                                        seen_targets.add(norm_target)
                                        seen_names.add(clean_name.lower())
                        except Exception:
                            continue
            except Exception:
                continue

    def _add_system_apps(self, apps: List[AppEntry], seen_targets: Set[str], seen_names: Set[str]) -> None:
        """Ensure common Windows system tools are available in the index."""
        system32 = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32")

        for display_name, exe_name, desc in COMMON_SYSTEM_APPS:
            full_path = os.path.join(system32, exe_name)
            norm_target = full_path.lower()

            if norm_target in seen_targets or display_name.lower() in seen_names:
                continue

            if os.path.exists(full_path):
                icon_png = self.icon_extractor.get_icon_path(full_path)
                entry = AppEntry(
                    name=display_name,
                    target_path=full_path,
                    icon_path=icon_png,
                    source="system"
                )
                apps.append(entry)
                seen_targets.add(norm_target)
                seen_names.add(display_name.lower())

    def _clean_app_name(self, raw_name: str) -> str:
        """Strip shortcut suffixes, file extensions, and extra whitespace."""
        name = raw_name
        name = re.sub(r"\s*-\s*shortcut$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\.lnk$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\.exe$", "", name, flags=re.IGNORECASE)
        return name.strip()

    def _is_excluded(self, app_name: str, path: str) -> bool:
        """Check if application should be excluded (uninstallers, help docs, etc.)."""
        for pat in EXCLUDED_PATTERNS:
            if pat.search(app_name) or pat.search(path):
                return True

        ext = os.path.splitext(path)[1].lower()
        if ext in EXCLUDED_EXTENSIONS:
            return True

        return False
