@echo off
setlocal
REM Launcher for Simple Complete Workflow GUI - Hidden Console Version

REM Change to project directory
cd /d "D:\Github\totokn"

REM Python paths
set "PYW=C:\Users\Hiroshi Ohtaka\AppData\Local\Programs\Python\Python312\pythonw.exe"
set "PY=C:\Users\Hiroshi Ohtaka\AppData\Local\Programs\Python\Python312\python.exe"

REM Try pythonw.exe first (no console), then python.exe as fallback
if exist "%PYW%" (
  start "" "%PYW%" "D:\Github\totokn\simple_complete_gui.py"
) else if exist "%PY%" (
  start "" "%PY%" "D:\Github\totokn\simple_complete_gui.py"
) else (
  echo Python not found! Please check Python installation.
  echo Expected paths:
  echo   %PYW%
  echo   %PY%
  pause
  exit /b 1
)

REM Exit batch file immediately (don't wait for GUI to close)
endlocal
exit /b 0
