# Complete Workflow Focused Runner

このフォーカス版は "Complete Workflow" のみを実行する軽量ランナーです。

## 使い方

- 対話式バッチで起動（おすすめ）
  - `launch_complete_workflow.bat` を実行
  - CSV パス、ラウンド、ヘッドレスの有無を尋ねられます
  - ラウンド未入力の場合は、CSVファイル名から4〜5桁の数字を抽出し、見つからなければ最新を選びます

- 直接CLIから実行
  - `run_complete_workflow.py --csv your.csv --auto-round`
  - `run_complete_workflow.py --csv your.csv --round 1558`
  - 追加オプション: `--headless`, `--timeout 20`, `--verbose`

## 仕様

- 既存の `complete_toto_automation.CompleteTotoAutomation` を使用
- 依存はプロジェクト標準の `requirements.txt`
- ログは `logs/complete_workflow_YYYYmmdd_HHMMSS.log` に出力します

## 補足

- Enhanced/通常版のGUIは使わず、ワークフロー直実行に特化しています。
- 今後、必要であればGUIボタンからこのフォーカス版を呼び出す統合も可能です。
