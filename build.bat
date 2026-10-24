@echo off
setlocal
cd /d "%~dp0"

echo ===================================================================
echo   QuickFind - Standalone Executable Builder
echo ===================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please ensure Python is installed and added to PATH.
    pause
    exit /b 1
)

echo [1/3] Checking and installing build requirements (PySide6, PyInstaller)...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Pip install had issues. Attempting build anyway...
)

echo.
echo [2/3] Building standalone executable with PyInstaller...
python build.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! See error output above.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Deployment complete!
echo QuickFind.exe is now ready on your Desktop.
echo.
pause
