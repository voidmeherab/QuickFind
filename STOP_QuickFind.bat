@echo off
setlocal
echo ===================================================================
echo     Stopping QuickFind Background Process
echo ===================================================================
echo.

taskkill /F /IM QuickFind.exe >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*QuickFind*' } | Stop-Process -Force" >nul 2>&1

if exist "C:\Users\Meherab\Desktop\NOVA QuickFind" (
    echo Removing NOVA QuickFind directory...
    rd /s /q "C:\Users\Meherab\Desktop\NOVA QuickFind"
)
if exist "C:\Users\Meherab\Desktop\NOVA QuickFind.exe" (
    del /f /q "C:\Users\Meherab\Desktop\NOVA QuickFind.exe"
)

echo.
echo [DONE] QuickFind process stopped.
echo.
pause
