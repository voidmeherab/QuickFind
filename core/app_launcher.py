"""
QuickFind Application Launcher
Safely executes applications using Windows ShellExecuteW or subprocess.Popen
without shell injection risks, and records launch telemetry in the local history DB.
"""

import os
import sys
import subprocess
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
from storage.history_db import HistoryDB

SW_SHOWNORMAL = 1


class AppLauncher:
    """Handles safe launching of applications, documents, and system utilities."""

    def __init__(self, history_db: Optional[HistoryDB] = None):
        self.history_db = history_db or HistoryDB()

    def launch(self, target_path: str, arguments: str = "", working_dir: str = "", app_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Launch the application safely.
        Returns (success: bool, error_message: str).
        """
        if not target_path:
            return False, "Target path is empty"

        clean_target = os.path.expandvars(target_path).strip()

        # Determine effective working directory
        work_dir = working_dir
        if not work_dir and os.path.isfile(clean_target):
            work_dir = os.path.dirname(clean_target)
        if work_dir and not os.path.isdir(work_dir):
            work_dir = ""

        # Method 1: ShellExecuteW (standard native Windows launcher)
        try:
            # ShellExecuteW(hwnd, lpOperation, lpFile, lpParameters, lpDirectory, nShowCmd)
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "open",
                clean_target,
                arguments if arguments else None,
                work_dir if work_dir else None,
                SW_SHOWNORMAL
            )

            # ShellExecute returns an HINSTANCE > 32 on success
            if ret > 32:
                if app_id:
                    self.history_db.record_launch(app_id)
                return True, ""

            # If ret <= 32, ShellExecute returned an error code
            err_code = ret
        except Exception as e:
            err_code = str(e)

        # Method 2: subprocess.Popen fallback (for raw executables)
        try:
            if clean_target.lower().endswith((".exe", ".bat", ".cmd")):
                cmd_list = [clean_target]
                if arguments:
                    import shlex
                    try:
                        cmd_list.extend(shlex.split(arguments, posix=False))
                    except Exception:
                        cmd_list.append(arguments)

                subprocess.Popen(
                    cmd_list,
                    cwd=work_dir if work_dir else None,
                    close_fds=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )

                if app_id:
                    self.history_db.record_launch(app_id)
                return True, ""
        except Exception as e:
            return False, f"Failed to launch '{clean_target}': {e} (ShellExecute code: {err_code})"

        return False, f"Failed to launch '{clean_target}' (ShellExecute error code: {err_code})"
