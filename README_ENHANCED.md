# Enhanced Web Form Automation System 🚀

操作記録・再生機能を搭載した発展版Webフォーム自動化システム

## 🎯 基本版からの進化

### 基本版の課題
- フォーム後の操作（ボタンクリック、ページ遷移）がハードコーディング
- サイトのUI変更に対応しにくい
- 複雑な操作シーケンスの管理が困難
- 異なるサイトでの再利用が難しい

### 発展版の解決策
✅ **操作記録・再生機能** - ユーザー操作を記録してJSON形式で保存  
✅ **柔軟なアクション管理** - サイト変更時はアクションファイルのみ更新  
✅ **大量データ対応** - 100+セットの効率的なバッチ処理  
✅ **再利用性向上** - 同様構造の他サイトでも利用可能  
✅ **保守性向上** - 複雑な操作シーケンスも簡単管理  

## 🎮 3つの動作モード

### 1. Record Mode（記録モード）
ユーザーの手動操作を記録してアクションファイルを作成

```bash
python enhanced_automation.py --mode record --url "https://example.com/form"
```

### 2. Execute Mode（実行モード）  
記録されたアクション + CSVデータで大量データを自動処理

```bash
python enhanced_automation.py --mode execute --csv data.csv --actions my_actions.json
```

### 3. Basic Mode（基本モード）
従来機能（フォーム入力のみ）

```bash
python enhanced_automation.py --mode basic --csv data.csv
```

## 📋 システム構成

### 新規コンポーネント
```
action_manager.py          # アクション管理システム
action_recorder.py         # 操作記録機能
action_player.py           # アクション再生機能  
enhanced_automation.py     # 発展版メインシステム
enhanced_gui_automation.py # 発展版GUI
```

### アクションファイル形式
```json
{
  "metadata": {
    "name": "Web Form Actions",
    "description": "フォーム処理用アクション",
    "site_url": "https://example.com",
    "recorded_at": "2024-01-01 12:00:00"
  },
  "batch_actions": [
    {
      "action": "click",
      "selector": "button.submit-form",
      "description": "フォーム送信ボタン",
      "wait_after": 3.0
    },
    {
      "action": "wait_for_url_change",
      "value": "confirmation",
      "timeout": 15.0
    }
  ]
}
```

## 🎯 使用フロー例

### 100行のCSVデータ処理例
```
初回: 操作記録
1. Record Mode で手動操作を記録
2. アクションファイル（my_actions.json）作成

実行: 大量データ自動処理  
1回目: 1-10行目をフォーム入力 → 記録アクション実行 → 次画面
2回目: 11-20行目をフォーム入力 → 記録アクション実行 → 次画面
...
10回目: 91-100行目をフォーム入力 → 記録アクション実行 → 完了
```

## 🛠️ インストール & セットアップ

### 依存関係のインストール
```bash
pip install -r requirements.txt
```

### GUI版ランチャー
```bash
python enhanced_gui_launcher.py
```

## 💻 CLI使用方法

### 基本的なコマンド構文
```bash
python enhanced_automation.py --mode {record|execute|basic} [オプション]
```

### 詳細なオプション
```bash
# 操作記録
python enhanced_automation.py \
  --mode record \
  --url "https://example.com/form" \
  --actions "my_actions.json" \
  --browser chrome \
  --timeout 15

# 大量データ実行
python enhanced_automation.py \
  --mode execute \
  --csv "large_data.csv" \
  --actions "my_actions.json" \
  --headless \
  --log-level INFO

# 基本モード
python enhanced_automation.py \
  --mode basic \
  --csv "data.csv" \
  --url "https://example.com/form"
```

## 🖥️ Enhanced GUI機能

### メインタブ
- **モード選択**: Basic/Record/Execute
- **ファイル選択**: CSV・アクションファイル
- **データプレビュー**: CSVデータの事前確認
- **実行制御**: 開始・停止・スクリーンショット

### アクションタブ
- **アクション管理**: 作成・読み込み・削除
- **シーケンス表示**: アクション一覧をツリー表示
- **詳細表示**: アクションファイルのメタデータ

### 設定タブ
- **ブラウザ設定**: Chrome/Firefox/Edge、ヘッドレス
- **タイムアウト設定**: 待機時間の調整
- **バッチ設定**: 一度に処理するセット数

### ログタブ
- **リアルタイム表示**: 処理状況をリアルタイム確認
- **ログ管理**: 保存・クリア・自動スクロール

## 📊 対応アクションタイプ

| アクション | 説明 | 例 |
|-----------|------|-----|
| `click` | 要素クリック | ボタン、リンク |
| `wait_for_element` | 要素出現待ち | 次画面の要素 |
| `wait_for_url_change` | URL変更待ち | ページ遷移 |
| `wait_for_alert` | アラート処理 | 確認ダイアログ |
| `input_text` | テキスト入力 | フィールド入力 |
| `confirm_checkbox` | チェックボックス | 確認チェック |
| `submit_form` | フォーム送信 | フォーム全体送信 |
| `screenshot` | スクリーンショット | デバッグ用 |
| `sleep` | 待機 | 固定時間待機 |

## 🎮 実際の使用例

### ケース1: 新しいサイトで初回セットアップ
```bash
# 1. 操作記録
python enhanced_automation.py --mode record --url "https://newsite.com/form"
# → インタラクティブに操作を記録
# → newsite_actions.json 作成

# 2. 大量データ処理
python enhanced_automation.py --mode execute --csv "data_500sets.csv" --actions "newsite_actions.json"
# → 500セットを50回に分けて自動処理
```

### ケース2: 既存サイトでUI変更対応
```bash
# 1. 新しい操作を記録
python enhanced_automation.py --mode record --actions "updated_actions.json"

# 2. アクションファイルを差し替えて実行
python enhanced_automation.py --mode execute --csv "data.csv" --actions "updated_actions.json"
```

### ケース3: GUI使用での簡単操作
```bash
# GUI起動
python enhanced_gui_automation.py

# GUI内で：
# 1. モード選択（Record/Execute）
# 2. ファイル選択（CSV/Actions）  
# 3. Start Automation ボタンクリック
```

## 🔧 トラブルシューティング

### よくある問題と解決法

**Q: 記録したアクションが実行時に失敗する**
```bash
# デバッグモードで詳細確認
python enhanced_automation.py --mode execute --csv data.csv --actions actions.json --log-level DEBUG

# スクリーンショットで状況確認
# GUI: Take Screenshot ボタン
```

**Q: サイトのUI変更で動作しなくなった**
```bash
# 新しい操作を記録し直す
python enhanced_automation.py --mode record --actions "updated_actions.json"
```

**Q: 大量データ処理が途中で止まる**
```bash
# タイムアウト時間を延長
python enhanced_automation.py --mode execute --csv data.csv --actions actions.json --timeout 30

# バッチサイズを調整
# GUI設定タブでSets per Batchを5-15に調整
```

**Q: アクションファイルのフォーマットエラー**
```json
// 必須フィールドを確認
{
  "metadata": { "name": "必須" },
  "batch_actions": [
    {
      "action": "click",        // 必須
      "selector": "button",     // click時必須
      "description": "説明"     // 推奨
    }
  ]
}
```

## 📈 パフォーマンス最適化

### 大量データ処理のコツ
- **バッチサイズ調整**: 10セット推奨（1-20で調整可能）
- **ヘッドレスモード**: GUI不要時は有効化
- **タイムアウト最適化**: サイト応答速度に合わせて調整
- **エラー回復**: オプションアクションの活用

### 推奨設定
```bash
# 高速処理用設定
python enhanced_automation.py \
  --mode execute \
  --csv large_data.csv \
  --actions fast_actions.json \
  --headless \
  --timeout 8 \
  --browser chrome
```

## 🔒 セキュリティ & 注意事項

### 使用上の注意
- 許可されたWebサイトでのみ使用
- 利用規約の確認必須
- レート制限への配慮
- 個人情報の適切な取り扱い

### アクションファイルのセキュリティ
- アクションファイルに機密情報を含めない
- バージョン管理でのアクションファイル共有時は注意
- テスト環境での事前検証を推奨

## 🚀 応用例・拡張可能性

### 他業務への応用
- **テストデータ投入**: テスト環境への大量データ登録
- **定期レポート作成**: 毎日/毎週の定型業務自動化
- **データ移行**: システム間でのデータ移行作業
- **フォーム一括処理**: アンケート・申請フォームの一括処理

### システム拡張
- **複数サイト対応**: サイト別アクションファイル管理
- **条件分岐**: データ内容による処理分岐
- **外部API連携**: REST API経由でのデータ取得・送信
- **レポート機能**: 処理結果の自動レポート生成

## 📚 関連ファイル

### 基本システム
- `voting_automation.py` - 基本版メインシステム
- `gui_automation.py` - 基本版GUI
- `README.md` - 基本版ドキュメント

### 発展版システム  
- `enhanced_automation.py` - 発展版メインシステム
- `enhanced_gui_automation.py` - 発展版GUI
- `README_ENHANCED.md` - 発展版ドキュメント（本ファイル）

### 共通コンポーネント
- `config.py` - 設定管理
- `data_handler.py` - CSV処理
- `web_driver_manager.py` - WebDriver管理
- `form_filler.py` - フォーム操作

### 発展版専用コンポーネント
- `action_manager.py` - アクション管理
- `action_recorder.py` - 操作記録
- `action_player.py` - アクション再生

## 💡 まとめ

発展版システムにより、基本版の制限を克服し、実用的で保守しやすいWebフォーム自動化システムが実現できました。

**主な改善点:**
- 🎯 **柔軟性**: サイト変更に強い
- 🔄 **再利用性**: 他サイトでも活用可能  
- 📈 **スケーラビリティ**: 大量データ対応
- 🛠️ **保守性**: 複雑な操作も簡単管理
- 🎮 **使いやすさ**: GUI・CLI両対応

これにより、単発的な自動化から継続的な業務効率化まで、幅広いニーズに対応できるシステムとなりました！