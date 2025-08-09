@echo off
setlocal
REM Focused launcher for Complete Toto Automation workflow
cd /d "D:\Github\totokn"

set "PY=C:\Users\Hiroshi Ohtaka\AppData\Local\Programs\Python\Python312\python.exe"

set /p CSV=CSVファイルのパスを入力してください: 
if not defined CSV (
  echo CSVパスが入力されませんでした。終了します。
  pause
  exit /b 1
)

set /p RN=ラウンド番号を入力（空欄でファイル名から自動検出→なければ最新）: 

set /p HD=ヘッドレス(画面非表示)で実行しますか? (y/N): 
set "HEADLESS="
if /I "%HD%"=="Y" set "HEADLESS=--headless"

set "RNARG=--auto-round"
if defined RN set "RNARG=--round %RN%"

"%PY%" "D:\Github\totokn\run_complete_workflow.py" --csv "%CSV%" %RNARG% %HEADLESS%

if errorlevel 1 (
  echo 実行に失敗しました。出力ログを確認してください。
) else (
  echo 完了しました。
)

pause
endlocal
