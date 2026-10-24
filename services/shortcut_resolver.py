"""
Windows Shortcut (.lnk) Resolver
Resolves .lnk files to target executable paths, arguments, and icon locations using
Windows COM IShellLink via ctypes or a binary fallback parser.
"""

import os
import sys
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple

# COM Constants
CLSCTX_INPROC_SERVER = 1
MAX_PATH = 260
SLGP_RAWPATH = 0x4

# GUID definitions
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]

    def __init__(self, d1, d2, d3, d4_list):
        super().__init__()
        self.Data1 = d1
        self.Data2 = d2
        self.Data3 = d3
        for i, b in enumerate(d4_list):
            self.Data4[i] = b

CLSID_ShellLink = GUID(0x00021401, 0, 0, [0xC0, 0, 0, 0, 0, 0, 0, 0x46])
IID_IShellLinkW = GUID(0x000214F9, 0, 0, [0xC0, 0, 0, 0, 0, 0, 0, 0x46])
IID_IPersistFile = GUID(0x0000010B, 0, 0, [0xC0, 0, 0, 0, 0, 0, 0, 0x46])


def _init_com():
    """Ensure COM is initialized on the current thread."""
    try:
        ctypes.windll.ole32.CoInitialize(None)
    except Exception:
        pass


class ShortcutInfo:
    """Holds resolved shortcut information."""
    def __init__(self, target_path: str, arguments: str = "", working_dir: str = "", icon_path: str = "", icon_index: int = 0):
        self.target_path = target_path
        self.arguments = arguments
        self.working_dir = working_dir
        self.icon_path = icon_path or target_path
        self.icon_index = icon_index

    def __repr__(self):
        return f"<ShortcutInfo target='{self.target_path}' args='{self.arguments}'>"


def resolve_shortcut(lnk_path: str) -> Optional[ShortcutInfo]:
    """
    Resolve a Windows .lnk shortcut to its actual target, arguments, and icon.
    Uses Windows IShellLink COM interface via ctypes.
    """
    if not os.path.isfile(lnk_path):
        return None

    _init_com()

    try:
        # Create IShellLink instance
        shell_link = ctypes.c_void_p()
        hr = ctypes.windll.ole32.CoCreateInstance(
            ctypes.byref(CLSID_ShellLink),
            None,
            CLSCTX_INPROC_SERVER,
            ctypes.byref(IID_IShellLinkW),
            ctypes.byref(shell_link)
        )
        if hr != 0 or not shell_link:
            return _fallback_resolve_lnk(lnk_path)

        # QueryInterface for IPersistFile
        persist_file = ctypes.c_void_p()
        vtbl = ctypes.cast(shell_link, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        query_interface_func = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)
        )(vtbl[0])

        hr = query_interface_func(shell_link, ctypes.byref(IID_IPersistFile), ctypes.byref(persist_file))
        if hr != 0 or not persist_file:
            _release_com(shell_link)
            return _fallback_resolve_lnk(lnk_path)

        # IPersistFile::Load
        pf_vtbl = ctypes.cast(persist_file, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        load_func = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, wintypes.LPCWSTR, wintypes.DWORD
        )(pf_vtbl[5])

        hr = load_func(persist_file, lnk_path, 0)
        if hr != 0:
            _release_com(persist_file)
            _release_com(shell_link)
            return _fallback_resolve_lnk(lnk_path)

        # IShellLinkW::GetPath (index 3 in IShellLinkW vtbl)
        get_path_func = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, wintypes.LPWSTR, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
        )(vtbl[3])

        target_buf = ctypes.create_unicode_buffer(MAX_PATH * 2)
        get_path_func(shell_link, target_buf, MAX_PATH * 2, None, SLGP_RAWPATH)
        target = target_buf.value

        # IShellLinkW::GetArguments (index 10 in IShellLinkW vtbl)
        get_args_func = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, wintypes.LPWSTR, ctypes.c_int
        )(vtbl[10])
        args_buf = ctypes.create_unicode_buffer(MAX_PATH * 2)
        get_args_func(shell_link, args_buf, MAX_PATH * 2)
        args = args_buf.value

        # IShellLinkW::GetWorkingDirectory (index 8 in IShellLinkW vtbl)
        get_workdir_func = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, wintypes.LPWSTR, ctypes.c_int
        )(vtbl[8])
        workdir_buf = ctypes.create_unicode_buffer(MAX_PATH * 2)
        get_workdir_func(shell_link, workdir_buf, MAX_PATH * 2)
        workdir = workdir_buf.value

        # IShellLinkW::GetIconLocation (index 16 in IShellLinkW vtbl)
        get_icon_func = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, wintypes.LPWSTR, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
        )(vtbl[16])
        icon_buf = ctypes.create_unicode_buffer(MAX_PATH * 2)
        icon_idx = ctypes.c_int(0)
        get_icon_func(shell_link, icon_buf, MAX_PATH * 2, ctypes.byref(icon_idx))
        icon_path = icon_buf.value

        _release_com(persist_file)
        _release_com(shell_link)

        # Expand environment strings
        if target:
            target = os.path.expandvars(target)
        if icon_path:
            icon_path = os.path.expandvars(icon_path)

        if not target:
            # Fallback for UWP shortcuts or special shell items
            return ShortcutInfo(target_path=lnk_path, arguments="", working_dir="", icon_path=lnk_path)

        return ShortcutInfo(
            target_path=target,
            arguments=args,
            working_dir=workdir,
            icon_path=icon_path or target,
            icon_index=icon_idx.value
        )
    except Exception as e:
        return _fallback_resolve_lnk(lnk_path)


def _release_com(com_ptr):
    """Release a COM pointer."""
    try:
        if com_ptr:
            vtbl = ctypes.cast(com_ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            release_func = ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(vtbl[2])
            release_func(com_ptr)
    except Exception:
        pass


def _fallback_resolve_lnk(lnk_path: str) -> Optional[ShortcutInfo]:
    """
    Fallback parser for .lnk files when COM is unavailable or fails.
    Extracts raw target path from the LinkInfo structure in the binary .lnk file.
    """
    try:
        with open(lnk_path, "rb") as f:
            content = f.read()

        # Check for LNK header signature 0x0000004C ("L\x00\x00\x00")
        if len(content) < 76 or content[:4] != b"\x4c\x00\x00\x00":
            return ShortcutInfo(target_path=lnk_path)

        # Flags at offset 0x14
        flags = int.from_bytes(content[20:24], "little")
        has_link_info = bool(flags & 0x02)

        if not has_link_info:
            return ShortcutInfo(target_path=lnk_path)

        # Skip Shell Item ID List if present
        pos = 76
        if flags & 0x01:
            id_list_len = int.from_bytes(content[pos:pos + 2], "little")
            pos += 2 + id_list_len

        # LinkInfo header
        if pos + 28 <= len(content):
            local_path_offset = int.from_bytes(content[pos + 16:pos + 20], "little")
            if local_path_offset > 0 and pos + local_path_offset < len(content):
                path_start = pos + local_path_offset
                path_end = content.find(b"\x00", path_start)
                if path_end != -1:
                    raw_path = content[path_start:path_end].decode("mbcs", errors="ignore")
                    if os.path.exists(raw_path):
                        return ShortcutInfo(target_path=raw_path)

        return ShortcutInfo(target_path=lnk_path)
    except Exception:
        return ShortcutInfo(target_path=lnk_path)
