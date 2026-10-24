' QuickFind Silent Background Launcher
' Launches QuickFind via pythonw without opening any console window.

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

strScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
strMainPy = strScriptDir & "\main.py"

' Run pythonw with window style 0 (hidden)
WshShell.Run "pythonw.exe """ & strMainPy & """", 0, False
