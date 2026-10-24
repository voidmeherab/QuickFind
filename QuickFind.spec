# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification for QuickFind
Compiles a standalone, optimized, windowed Windows executable.
"""

import sys
import os

block_cipher = None
project_root = os.path.abspath(SPECPATH)

added_files = [
    (os.path.join(project_root, 'assets'), 'assets'),
] if os.path.exists(os.path.join(project_root, 'assets')) else []

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'winreg',
        'ctypes',
        'ctypes.wintypes',
        'sqlite3',
        'zlib',
        'struct',
        'shlex',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QuickFind',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets', 'icon.ico') if os.path.exists(os.path.join(project_root, 'assets', 'icon.ico')) else None,
)
