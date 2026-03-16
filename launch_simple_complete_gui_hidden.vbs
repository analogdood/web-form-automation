' TotoKN Simple Complete GUI - Hidden Console Launcher
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

projectDir = "D:\Github\totokn"
pythonScript = projectDir & "\simple_complete_gui.py"

' Auto-detect pythonw.exe
Dim pythonwPath
pythonwPath = ""

' 1) Search in PATH using where command
Dim oExec
Set oExec = objShell.Exec("where pythonw")
Do While oExec.Status = 0
    WScript.Sleep 100
Loop
If oExec.ExitCode = 0 Then
    pythonwPath = Trim(oExec.StdOut.ReadLine())
End If

' 2) Fallback: search common version folders
If pythonwPath = "" Then
    Dim baseDir
    baseDir = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\"
    Dim versions(5)
    versions(0) = "Python313"
    versions(1) = "Python312"
    versions(2) = "Python311"
    versions(3) = "Python310"
    versions(4) = "Python39"
    versions(5) = "Python38"
    Dim i
    Dim candidate
    For i = 0 To 5
        candidate = baseDir & versions(i) & "\pythonw.exe"
        If objFSO.FileExists(candidate) Then
            pythonwPath = candidate
            Exit For
        End If
    Next
End If

' 3) Show error if not found
If pythonwPath = "" Then
    MsgBox "pythonw.exe not found. Please check Python installation.", vbCritical, "TotoKN"
Else
    objShell.Run """" & pythonwPath & """ """ & pythonScript & """", 0, False
End If
