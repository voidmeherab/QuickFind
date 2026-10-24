@echo off
setlocal
cd /d "%~dp0"

echo Starting QuickFind...
where pythonw >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" pythonw main.py
) else (
    start "" python main.py
)
exit
