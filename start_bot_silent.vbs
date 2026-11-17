Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\hp\OneDrive\Desktop\Antigravity projects\ShieldGuard"
WshShell.Run "cmd /c START_SERVER.bat", 0, False
Set WshShell = Nothing
