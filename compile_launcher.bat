@echo off
setlocal
cd /d "%~dp0"

echo Compiling native QuickFind launcher...
set CSC="C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist %CSC% (
    set CSC="C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)

%CSC% /target:winexe /out:"%~dp0QuickFind.exe" /r:System.Windows.Forms.dll "%~dp0launcher.cs"
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Compiled QuickFind.exe!
    copy /Y "%~dp0QuickFind.exe" "C:\Users\Meherab\Desktop\QuickFind.exe" >nul
    echo [DEPLOYED] Placed QuickFind.exe directly on your Desktop!
) else (
    echo [ERROR] Compilation failed.
)
