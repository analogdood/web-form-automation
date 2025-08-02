# Claude Code セッション記録

## 🎯 プロジェクト概要
Toto自動投票システム - Web Form Automation with GUI

## ✅ 確立済み成功フロー (2025-08-02)

### 🏆 完全成功した操作パターン

**Complete Workflow (11セット → 2バッチ処理)**

#### ユーザー操作
1. CSVファイル選択
2. "Complete Workflow"ボタンクリック
3. 確認ダイアログ → Yes
4. ラウンド選択 (minitoto回避)
5. "Continue Workflow"クリック
6. 完了待機

#### 自動処理フロー
```
https://www.toto-dream.com/toto/index.html
↓ ラウンド検出
↓ ユーザー選択 (第1558回等)
↓ 「今すぐ投票予想する」クリック
↓ 「シングル」自動クリック
↓ Batch 1: 10セット入力・カート追加
↓ 「totoの投票を追加する」クリック ← 重要発見
↓ ラウンドリンク再クリック
↓ 「シングル」クリック
↓ Batch 2: 1セット入力・完了
```

### 🔧 技術的成功ポイント

#### 重要なセレクター
- **ラウンド検出**: `pcOnlyInline`, `PGSPIN00001DisptotoLotInfo`
- **投票予想**: `//img[@id='bt_yosou2']`
- **シングル**: `//img[@id='select_single']`
- **toto追加**: `//p[contains(@class, 'c-clubtoto-btn-base__text') and contains(text(), 'totoの投票を追加する')]/parent::*`

#### モーダル対応
- 検出: `.modal-cont-wrap`
- 対処: 5種類のクリック戦略 (Direct/Scroll/JS/ActionChains/Coordinate)

#### 待機時間
- ページロード: 5秒
- ボタンクリック後: 3秒
- アラート処理: 1秒

### 🚨 修正済み問題
- ✅ モーダルダイアログ阻害
- ✅ ブラウザ早期終了
- ✅ GUI表示問題
- ✅ 2バッチ目文字列エラー
- ✅ データ処理優先順位
- ✅ ラウンド選択UI

### 📊 期待結果
```
batch processing completed: 2/2 successful
Total sets: 11 (10+1)
All items added to cart
```

## 🎮 主要ファイル

### Core Files
- `enhanced_gui_automation.py` - メインGUI (950x800)
- `enhanced_automation.py` - バッチ処理エンジン
- `toto_round_selector.py` - ラウンド選択・ナビゲーション
- `data_handler.py` - CSV処理・バッチ分割

### Test Files
- `test_multi_batch.csv` - 25セット (3バッチ用)
- `sample_data.csv` - 15セット (2バッチ用)

### Documentation
- `SUCCESS_WORKFLOW.md` - 成功フロー詳細
- `USAGE_GUIDE.md` - 使用方法
- `README_GUI.md` - GUI説明

## 🚀 実行方法

```bash
# メイン実行
python3 enhanced_gui_automation.py

# テスト
python3 test_gui.py
python3 validate_csv_batches.py
```

## 💡 開発ガイドライン

### Complete Workflowが最優先
- すべての新機能はComplete Workflowに統合
- 段階的処理を維持 (検出→選択→実行)
- ユーザー選択ポイントを保持

### エラー処理パターン
1. 複数セレクター戦略
2. 待機時間調整
3. スクリーンショット保存
4. 詳細ログ出力

### セッション管理
- ラウンド情報永続化
- バッチ状態追跡
- 統計情報収集

## 🌐 投票サイト (toto-dream.com) 画面遷移フロー

### 📱 詳細画面遷移パターン

#### 1️⃣ スタートページ
```
URL: https://www.toto-dream.com/toto/index.html
画面: TOTOトップページ
要素: 複数のラウンドリンク (第1557回、第1558回、minitoto等)
   - PC版: class="pcOnlyInline" 
   - URL特徴: PGSPIN00001DisptotoLotInfo.form?holdCntId=XXXX
クリック: 希望ラウンド選択 (minitoto避ける)
```

#### 2️⃣ ラウンド情報ページ  
```
URL: store.toto-dream.com/.../PGSPIN00001DisptotoLotInfo.form?holdCntId=1558
画面: 選択ラウンドの詳細情報
要素: 「今すぐ投票予想する」ボタン
   - タグ: <img id="bt_yosou2" alt="今すぐ投票予想する">
   - src: bt_yosou.gif
クリック: 投票予想ボタン
```

#### 3️⃣ 投票種別選択ページ
```
URL: store.toto-dream.com/.../PGSPSL00001DispTotoHoldCnt.form
画面: BIG/toto/mini選択画面
要素: 「シングル」ボタン
   - タグ: <img id="select_single" alt="シングル">
   - src: bt_toto_single.gif
クリック: シングルボタン (自動)
```

#### 4️⃣ 投票入力ページ (メイン処理)
```
URL: store.toto-dream.com/.../PGSPSL00001MoveSingleVoteSheet.form
画面: totoシングル投票フォーム
要素: 13ゲーム × 各3択 (1/X/2) のラジオボタン
処理: 
  - CSVデータに基づいてラジオボタン選択
  - 10セット入力完了後
  - 「投票を追加」ボタンクリック
```

#### 5️⃣ カート追加確認
```
アラート: 「購入カートに追加します。よろしいですか？」
操作: OK押下
結果: カート追加ページへ遷移
```

#### 6️⃣ カート追加完了ページ ⭐重要⭐
```
URL: カート追加完了画面
画面: BIG購入画面 (title: スポーツくじ「BIG」...)
⚠️ 重要な分岐点:
  - 1バッチ目: ここで終了
  - 2バッチ目以降: さらに追加が必要

🔑 キーポイント:
要素: 「totoの投票を追加する」ボタン
   - タグ: <p class="c-clubtoto-btn-base__text">totoの投票を追加する</p>
   - 親要素クリック必要
クリック: このボタンで再度toto投票画面へ
```

#### 7️⃣ 再投票選択ページ (2バッチ目以降)
```
画面: 再度ラウンド選択画面
要素: 該当ラウンドリンク (第1558回等)
   - onclick: ChengeCommodityId('06');AlertNoVote(...,'1558')
   - href: "#" 
クリック: 同じラウンド再選択
```

#### 8️⃣ 再投票入力ページ
```
URL: 再び投票フォーム画面
処理: 残りセット (2バッチ目なら1セット) を入力
完了: 最終「投票を追加」でカート完了
```

### 🎯 重要な成功ポイント

#### サイト固有の仕様
1. **PC/Mobile判別**: pcOnlyInline vs spOnlyInline
2. **ラウンドID**: holdCntId パラメータで管理
3. **セッション管理**: 選択ラウンドをセッション中記憶
4. **バッチ間遷移**: 必ず「totoの投票を追加する」経由

#### 画面判別方法
```python
# 投票ページ判別
if 'PGSPSL00001MoveSingleVoteSheet' in url:
    # 投票入力画面
    
# カート追加ページ判別  
if 'BIG' in title and 'totoの投票を追加する' in page:
    # バッチ間遷移必要
    
# ラウンド情報ページ判別
if 'PGSPIN00001DisptotoLotInfo' in url:
    # 投票予想ボタン探す
```

#### 待機戦略
- ページ遷移: **5秒** (JS読み込み完了待ち)
- ボタンクリック後: **3秒** (画面更新待ち)  
- アラート処理: **1秒** (確認待ち)

---

**投票サイトのこの流れは絶対に変更しないでください。この成功パターンをベースに全ての機能を実装してください。**