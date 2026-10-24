# QuickFind

<p align="center">
  <b>A modern, ultra-lightweight Windows application launcher with instant search, spring animations, and zero taskbar footprint.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows" alt="Windows Platform" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/UI-PySide6%20%7C%20Qt6-41CD52?style=for-the-badge&logo=qt" alt="PySide6 / Qt6" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/Developer-Meherab-00c2cb?style=for-the-badge" alt="Developer Meherab" />
</p>

---

## Overview

**QuickFind** is a clean, background-resident productivity launcher designed for Windows 10 and 11. Inspired by macOS Spotlight and Raycast, QuickFind enables you to instantly find and launch any installed application from anywhere in the operating system using a global keyboard shortcut.

### Key Highlights

- **Global Shortcut (`Ctrl + F`)**: Open the launcher instantly over any window, full-screen game, or desktop.
- **Spotlight / Raycast Design Language**: Single-line app cards with crisp extracted PNG icons and subtle frosted glass highlights. No ugly file paths or cluttered tags.
- **Zero Taskbar Footprint**: Hidden completely from the Windows Taskbar and Alt+Tab switcher (`WS_EX_TOOLWINDOW`).
- **Instant Click-Outside Auto-Dismiss**: Clicking anywhere outside the launcher on your desktop or another application immediately dismisses the search bar with a smooth upward slide.
- **Sub-Millisecond Search**: Multi-tiered heuristic matching (Exact match > Prefix match > Acronym match > Subsequence fuzzy) with recency boosting.
- **Ultra-Lightweight**: Uses virtually **0% CPU** while idling in the background.
- **Standalone Windows Executable**: Includes precompiled `QuickFind.exe` for instant 1-click execution.

---

## Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Ctrl + F`** | Summon or refocus QuickFind anywhere in Windows |
| **`Down / Tab`** | Navigate down suggestions |
| **`Up / Shift + Tab`** | Navigate up suggestions |
| **`Enter`** | Launch the selected application |
| **`Escape`** | Close QuickFind |
| **`Click Outside`** | Dismiss QuickFind immediately |

---

## Project Structure

```text
QuickFind/
├── QuickFind.exe            # Standalone native launcher executable
├── main.py                  # Application entry point & lifecycle coordinator
├── config.py                # Styling parameters, dimensions & defaults
├── launcher.cs              # C# native launcher source code
├── compile_launcher.bat     # Windows csc.exe compiler script for QuickFind.exe
├── requirements.txt         # Python dependencies (PySide6)
├── QuickFind.spec           # PyInstaller build specification
├── build.py                 # PyInstaller standalone build orchestrator
├── run.bat                  # Background launcher script
├── STOP_QuickFind.bat       # Script to terminate background instances
├── LICENSE                  # MIT License
├── README.md                # Project documentation
│
├── core/                    # Core operating system services
│   ├── hotkey.py            # Windows RegisterHotKey background listener
│   ├── single_instance.py   # Named mutex & inter-process messaging
│   └── app_launcher.py      # Safe process execution & elevation handler
│
├── services/                # Indexing & search engine
│   ├── app_scanner.py       # Start Menu, Registry & Desktop app discovery
│   ├── search_engine.py     # Multi-tiered ranking & fuzzy matching
│   ├── shortcut_resolver.py # Windows Shell COM (.lnk target resolution)
│   └── icon_extractor.py    # Win32 HICON to pure-Python PNG extraction
│
├── storage/                 # Persistence layer
│   ├── settings.py          # Atomic JSON configuration manager
│   └── history_db.py        # SQLite application usage tracking
│
└── ui/                      # User Interface & Design
    ├── styles.py            # Glassmorphism QSS stylesheets & SVG vectors
    ├── search_window.py     # Translucent floating search bar HUD
    ├── tray_icon.py         # Windows System Tray context menu
    ├── settings_dialog.py   # Launcher preferences modal
    └── tk_fallback.py       # Standard-library Tkinter fallback HUD
```

---

## Getting Started

### Option 1: Direct Run (No Installation Required)

1. Download or clone this repository:
   ```bash
   git clone https://github.com/voidmeherab/QuickFind.git
   ```
2. Double-click `QuickFind.exe` to start QuickFind in the background.
3. Press `Ctrl + F` anywhere in Windows to start searching!

### Option 2: Running from Python Source

Ensure you have Python 3.10+ installed:

```bash
# 1. Clone the repository
git clone https://github.com/voidmeherab/QuickFind.git
cd QuickFind

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch QuickFind
pythonw main.py
```

---

## How to Stop or Exit

- **Method 1**: Run `STOP_QuickFind.bat`.
- **Method 2**: Right-click the **QuickFind** icon in the Windows System Tray (near the clock) and select **Exit**.
- **Method 3**: In Task Manager (`Ctrl + Shift + Esc`), end task `QuickFind.exe` or `pythonw.exe`.

---

## Developer & Author

- **Developer**: **Meherab** ([@voidmeherab](https://github.com/voidmeherab))
- **Repository**: [https://github.com/voidmeherab/QuickFind](https://github.com/voidmeherab/QuickFind)

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details. Open-source and free for all developers.
