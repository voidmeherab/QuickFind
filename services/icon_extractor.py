"""
Windows Icon Extractor
Extracts crisp application icons from executables, shortcuts, or DLLs using Windows Shell APIs
and converts/caches them to disk for fast UI rendering.
"""

import os
import sys
import hashlib
import ctypes
from ctypes import wintypes
from typing import Optional
from config import get_icon_cache_dir

# Windows Shell / GDI Constants
SHGFI_ICON = 0x000000100
SHGFI_LARGEICON = 0x000000000
SHGFI_USEFILEATTRIBUTES = 0x000000010
FILE_ATTRIBUTE_NORMAL = 0x00000080
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040

class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]

class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP),
    ]

class BITMAP(ctypes.Structure):
    _fields_ = [
        ("bmType", wintypes.LONG),
        ("bmWidth", wintypes.LONG),
        ("bmHeight", wintypes.LONG),
        ("bmWidthBytes", wintypes.LONG),
        ("bmPlanes", wintypes.WORD),
        ("bmBitsPixel", wintypes.WORD),
        ("bmBits", ctypes.c_void_p),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class IconExtractor:
    """Extracts and caches Windows application icons."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or get_icon_cache_dir()
        os.makedirs(self.cache_dir, exist_ok=True)
        self._memory_cache = {}

    def get_icon_path(self, target_path: str, icon_source: Optional[str] = None, icon_index: int = 0) -> Optional[str]:
        """
        Get or extract the cached PNG icon for the given application.
        Returns the path to the cached PNG file on disk.
        """
        source = icon_source or target_path
        if not source or not os.path.exists(source):
            source = target_path

        # Generate a unique cache key
        cache_key = hashlib.md5(f"{source.lower()}:{icon_index}".encode("utf-8")).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.png")

        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
            return cache_file

        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Extract icon using Windows API
        extracted = self._extract_and_save_icon(source, icon_index, cache_file)
        if extracted and os.path.exists(cache_file):
            self._memory_cache[cache_key] = cache_file
            return cache_file

        return None

    def _extract_and_save_icon(self, source_path: str, icon_index: int, out_png_path: str) -> bool:
        """Extract HICON using SHGetFileInfo or ExtractIconEx and save to PNG."""
        h_icon = None

        try:
            # Method 1: ExtractIconExW for specific icon index
            if source_path.lower().endswith((".exe", ".dll", ".ico")):
                large_icons = (wintypes.HICON * 1)()
                small_icons = (wintypes.HICON * 1)()
                num_extracted = ctypes.windll.shell32.ExtractIconExW(
                    source_path, icon_index, large_icons, small_icons, 1
                )
                if num_extracted > 0 and large_icons[0]:
                    h_icon = large_icons[0]
                    if small_icons[0]:
                        ctypes.windll.user32.DestroyIcon(small_icons[0])

            # Method 2: SHGetFileInfoW
            if not h_icon:
                shfi = SHFILEINFOW()
                res = ctypes.windll.shell32.SHGetFileInfoW(
                    source_path,
                    0,
                    ctypes.byref(shfi),
                    ctypes.sizeof(shfi),
                    SHGFI_ICON | SHGFI_LARGEICON
                )
                if res != 0 and shfi.hIcon:
                    h_icon = shfi.hIcon

            if not h_icon:
                return False

            # Convert HICON to PNG file
            success = self._save_hicon_to_png(h_icon, out_png_path)
            ctypes.windll.user32.DestroyIcon(h_icon)
            return success

        except Exception as e:
            if h_icon:
                try:
                    ctypes.windll.user32.DestroyIcon(h_icon)
                except Exception:
                    pass
            return False

    def _save_hicon_to_png(self, h_icon: wintypes.HICON, out_path: str) -> bool:
        """Convert a Windows HICON to 32-bit RGBA BMP/PNG data and write to disk."""
        icon_info = ICONINFO()
        if not ctypes.windll.user32.GetIconInfo(h_icon, ctypes.byref(icon_info)):
            return False

        h_bm_color = icon_info.hbmColor
        h_bm_mask = icon_info.hbmMask

        try:
            # Get bitmap dimensions
            bm = BITMAP()
            ctypes.windll.gdi32.GetObjectW(h_bm_color, ctypes.sizeof(bm), ctypes.byref(bm))
            width = bm.bmWidth
            height = bm.bmHeight

            if width <= 0 or height <= 0:
                width, height = 32, 32

            # Create DIB Section for 32bpp RGBA
            bi = BITMAPINFOHEADER()
            bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bi.biWidth = width
            bi.biHeight = -height  # Top-down DIB
            bi.biPlanes = 1
            bi.biBitCount = 32
            bi.biCompression = 0  # BI_RGB

            hdc_screen = ctypes.windll.user32.GetDC(None)
            hdc_mem = ctypes.windll.gdi32.CreateCompatibleDC(hdc_screen)

            bits = ctypes.c_void_p()
            h_dib = ctypes.windll.gdi32.CreateDIBSection(
                hdc_mem,
                ctypes.byref(bi),
                0,
                ctypes.byref(bits),
                None,
                0
            )

            if not h_dib or not bits:
                ctypes.windll.gdi32.DeleteDC(hdc_mem)
                ctypes.windll.user32.ReleaseDC(None, hdc_screen)
                return False

            old_bmp = ctypes.windll.gdi32.SelectObject(hdc_mem, h_dib)

            # Draw icon into DIB DC
            ctypes.windll.user32.DrawIconEx(
                hdc_mem, 0, 0, h_icon, width, height, 0, None, 0x0003  # DI_NORMAL
            )

            # Read raw BGRA pixels
            num_bytes = width * height * 4
            buffer = (ctypes.c_char * num_bytes).from_address(bits.value)
            raw_data = bytes(buffer)

            # Clean up GDI objects
            ctypes.windll.gdi32.SelectObject(hdc_mem, old_bmp)
            ctypes.windll.gdi32.DeleteObject(h_dib)
            ctypes.windll.gdi32.DeleteDC(hdc_mem)
            ctypes.windll.user32.ReleaseDC(None, hdc_screen)

            # Check if image has non-zero alpha
            has_alpha = any(raw_data[i + 3] > 0 for i in range(0, len(raw_data), 4))
            if not has_alpha:
                # If no alpha channel, make all pixels with color opaque
                new_data = bytearray(raw_data)
                for i in range(0, len(new_data), 4):
                    if new_data[i] > 0 or new_data[i + 1] > 0 or new_data[i + 2] > 0:
                        new_data[i + 3] = 255
                raw_data = bytes(new_data)

            # Save as standard PNG using pure Python PNG writer
            return _write_png(out_path, width, height, raw_data)

        finally:
            if h_bm_color:
                ctypes.windll.gdi32.DeleteObject(h_bm_color)
            if h_bm_mask:
                ctypes.windll.gdi32.DeleteObject(h_bm_mask)


def _write_png(file_path: str, width: int, height: int, bgra_data: bytes) -> bool:
    """
    Pure Python lightweight PNG writer for RGBA pixel data.
    Avoids requiring PIL/Pillow or external libraries!
    """
    import zlib
    import struct

    try:
        # Convert BGRA to RGBA and add filter byte (0 = None) per scanline
        raw_rows = []
        stride = width * 4
        for y in range(height):
            row_start = y * stride
            row_end = row_start + stride
            row = bgra_data[row_start:row_end]
            rgba_row = bytearray(stride)
            for x in range(width):
                i = x * 4
                rgba_row[i] = row[i + 2]      # R
                rgba_row[i + 1] = row[i + 1]  # G
                rgba_row[i + 2] = row[i]      # B
                rgba_row[i + 3] = row[i + 3]  # A
            raw_rows.append(b"\x00" + bytes(rgba_row))

        raw_idat = zlib.compress(b"".join(raw_rows), 6)

        def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            length = struct.pack(">I", len(data))
            crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
            return length + chunk_type + data + crc

        # PNG Header
        png_header = b"\x89PNG\r\n\x1a\n"

        # IHDR chunk: width, height, bit depth (8), color type (6 = RGBA), compression (0), filter (0), interlace (0)
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
        ihdr_chunk = make_chunk(b"IHDR", ihdr_data)

        # IDAT chunk
        idat_chunk = make_chunk(b"IDAT", raw_idat)

        # IEND chunk
        iend_chunk = make_chunk(b"IEND", b"")

        with open(file_path, "wb") as f:
            f.write(png_header + ihdr_chunk + idat_chunk + iend_chunk)

        return True
    except Exception as e:
        print(f"[QuickFind] Error writing PNG '{file_path}': {e}", file=sys.stderr)
        return False
