' TotoKN Simple Complete GUI - Hidden Console Launcher
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

projectDir = "D:\Github\totokn"
pythonScript = projectDir & "\simple_complete_gui.py"
pythonwPath = "C:\Users\Hiroshi Ohtaka\AppData\Local\Programs\Python\Python312\pythonw.exe"

If objFSO.FileExists(pythonwPath) Then
    objShell.Run """" & pythonwPath & """ """ & pythonScript & """", 0, False
Else
    MsgBox "Python not found\!", vbCritical, "TotoKN"
End If
