# ableton-cli

Ableton Live をターミナルから操作する CLI ツール。[AbletonMCP](https://github.com/ahujasid/ableton-mcp) の Remote Script と TCP ソケットで通信します。

## セットアップ

### 1. Ableton Remote Script のインストール

[AbletonMCP](https://github.com/ahujasid/ableton-mcp) の `AbletonMCP_Remote_Script` フォルダを Ableton の MIDI Remote Scripts ディレクトリにコピーします。

```
# macOS
~/Music/Ableton/User Library/Remote Scripts/AbletonMCP_Remote_Script/

# Windows
~\Documents\Ableton\User Library\Remote Scripts\AbletonMCP_Remote_Script\
```

Ableton Live の設定 → Link, Tempo & MIDI → Control Surface で **AbletonMCP** を選択します。

### 2. CLI のインストール

```bash
git clone https://github.com/ryok/ableton-cli.git
cd ableton-cli
uv venv && uv pip install -e .
source .venv/bin/activate
```

## 使い方

Ableton Live が起動し、Remote Script がロードされた状態で:

```bash
# セッション情報
ableton session

# テンポ変更
ableton tempo 128

# 再生 / 停止
ableton play
ableton stop
```

### トラック操作

```bash
ableton track info 0          # トラック 0 の詳細
ableton track create           # MIDI トラック作成
ableton track create -i 2      # インデックス 2 に挿入
ableton track rename 0 "Bass"  # 名前変更
```

### クリップ操作

```bash
# クリップ作成 (トラック 0, スロット 0, 8ビート)
ableton clip create 0 0 --length 8

# MIDI ノート追加
ableton clip add-notes 0 0 '[
  {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100},
  {"pitch": 64, "start_time": 1, "duration": 1, "velocity": 80},
  {"pitch": 67, "start_time": 2, "duration": 1, "velocity": 90}
]'

# クリップ名変更
ableton clip rename 0 0 "Chord"

# 再生 / 停止
ableton clip fire 0 0
ableton clip stop 0 0
```

### ブラウザ

```bash
# カテゴリツリー表示
ableton browser tree
ableton browser tree -c instruments

# 特定パスのアイテム一覧
ableton browser items "instruments/Synths"
```

### インストゥルメント / エフェクト読み込み

```bash
# URI を指定してロード
ableton load 0 "query:Synths#Instrument%20Rack:Bass:FileId_5116"

# ドラムキットのロード
ableton load-drum-kit 0 "Drums/Drum Rack" "drums/acoustic/kit1"
```

### 接続オプション

```bash
# デフォルト: localhost:9877
ableton --host 192.168.1.10 --port 9877 session
```

## ライセンス

MIT
