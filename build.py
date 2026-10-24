"""
QuickFind Build Orchestrator
Builds the standalone QuickFind.exe using PyInstaller and places it on the Desktop.
"""

import os
import sys
import shutil
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
OUTPUT_EXE_NAME = "QuickFind.exe"
FINAL_DESKTOP_EXE = os.path.join(DESKTOP_DIR, OUTPUT_EXE_NAME)


def run_command(cmd, desc=""):
    """Run a shell command and stream output."""
    if desc:
        print(f"\n[Build] {desc}...")
    print(f"[Command] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    proc = subprocess.run(cmd, cwd=PROJECT_DIR, shell=True)
    if proc.returncode != 0:
        print(f"[Build Error] Command failed with return code {proc.returncode}", file=sys.stderr)
        return False
    return True


def ensure_dependencies():
    """Ensure required packages (PySide6, pyinstaller) are installed."""
    print("[Build] Checking build dependencies...")
    try:
        import PySide6
        import PyInstaller
        print("[Build] PySide6 and PyInstaller are already installed.")
        return True
    except ImportError:
        print("[Build] Installing required packages from requirements.txt...")
        req_file = os.path.join(PROJECT_DIR, "requirements.txt")
        return run_command(f'"{sys.executable}" -m pip install -r "{req_file}"', "Installing dependencies")


def build_executable():
    """Run PyInstaller with QuickFind.spec."""
    spec_file = os.path.join(PROJECT_DIR, "QuickFind.spec")
    if not os.path.exists(spec_file):
        print(f"[Build Error] Spec file not found: {spec_file}", file=sys.stderr)
        return False

    cmd = f'"{sys.executable}" -m PyInstaller "{spec_file}" --clean -y'
    success = run_command(cmd, "Building standalone executable with PyInstaller")
    if not success:
        return False

    # Locate generated executable in dist/
    dist_exe = os.path.join(PROJECT_DIR, "dist", OUTPUT_EXE_NAME)
    if not os.path.exists(dist_exe):
        print(f"[Build Error] Expected executable not found at: {dist_exe}", file=sys.stderr)
        return False

    # Copy to Desktop
    print(f"\n[Build] Deploying {OUTPUT_EXE_NAME} to Desktop: {FINAL_DESKTOP_EXE}")
    try:
        shutil.copy2(dist_exe, FINAL_DESKTOP_EXE)
        print(f"[Build Success] Standalone executable successfully placed on Desktop!")
        print(f"       Path: {FINAL_DESKTOP_EXE}")
        print(f"       Size: {os.path.getsize(FINAL_DESKTOP_EXE) / (1024*1024):.2f} MB")
        return True
    except Exception as e:
        print(f"[Build Error] Failed to copy executable to Desktop: {e}", file=sys.stderr)
        return False


def main():
    print("=" * 65)
    print(" QuickFind — Automated Executable Build & Deployment")
    print("=" * 65)

    if not ensure_dependencies():
        print("[Build Failed] Could not satisfy dependencies.", file=sys.stderr)
        sys.exit(1)

    if not build_executable():
        print("[Build Failed] PyInstaller build failed.", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 65)
    print(" BUILD COMPLETE!")
    print(f" You can now run QuickFind directly from your Desktop:")
    print(f" -> {FINAL_DESKTOP_EXE}")
    print("=" * 65)


if __name__ == "__main__":
    main()
