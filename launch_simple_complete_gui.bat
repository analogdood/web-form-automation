@echo off
setlocal
REM Launcher for Simple Complete Workflow GUI
cd /d "D:\Github\totokn"

set "PYW=C:\Users\Hiroshi Ohtaka\AppData\Local\Programs\Python\Python312\pythonw.exe"
set "PY=C:\Users\Hiroshi Ohtaka\AppData\Local\Programs\Python\Python312\python.exe"

if exist "%PYW%" (
  "%PYW%" "D:\Github\totokn\simple_complete_gui.py"
) else (
  "%PY%" "D:\Github\totokn\simple_complete_gui.py"
)

if errorlevel 1 (
  echo 起動に失敗しました。Press any key to close...
  pause
)

endlocal
