# ableton-cli

Ableton Live をターミナルから操作する CLI ツール。[AbletonMCP](https://github.com/ahujasid/ableton-mcp) の Remote Script と TCP ソケットで通信します。

## なぜ MCP ではなく CLI？

ableton-cli と [Ableton MCP](https://github.com/ahujasid/ableton-mcp) は**同じ Remote Script** をバックエンドに使っています。違いは AI エージェントとの接続方式だけです。

```
Ableton MCP:   Claude → MCP JSON-RPC → Remote Script (TCP:9877)
ableton-cli:   Claude → Bash → CLI    → Remote Script (TCP:9877)
```

### トークン効率の比較

| 観点 | MCP | CLI | 優位 |
|------|-----|-----|------|
| **固定コスト** | 17個のツール定義が毎ターン system prompt に含まれる（数千トークン） | Bash ツール1つだけ。コマンドは `--help` やスキルで把握 | **CLI** |
| **呼び出しコスト** | JSON-RPC のリクエスト/レスポンス（完全なパラメータスキーマ付き） | 短いシェルコマンド + 簡潔なテキスト出力 | **CLI** |
| **バッチ操作** | 操作ごとに1回のツール呼び出し | `&&` で1回の Bash 呼び出しにチェーン可能 | **CLI** |
| **型安全性** | JSON Schema によるパラメータ検証あり | スキーマ検証なし | MCP |
| **発見性** | ツール一覧がモデルに自動公開 | `--help` やスキルが必要 | MCP |

### 例：テンポ設定 + トラック作成 + クリップ再生

```bash
# MCP: 3回のツール呼び出し（3往復）
mcp__ableton__set_tempo(bpm=128)
mcp__ableton__create_midi_track(index=-1)
mcp__ableton__fire_clip(track_index=0, clip_index=0)

# CLI: 1回の Bash 呼び出し
ableton tempo 128 && ableton track create && ableton clip fire 0 0
```

CLI は特に長いセッションでトークン効率が大幅に優れています。MCP のツール定義は毎ターンのコンテキストを消費し続けるためです。

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

**推奨** – 1コマンドでグローバルインストール（[uv](https://docs.astral.sh/uv/) が必要）:

```bash
uv tool install git+https://github.com/ryok/ableton-cli.git
```

[pipx](https://pipx.pypa.io/) でも可:

```bash
pipx install git+https://github.com/ryok/ableton-cli.git
```

<details>
<summary>開発用（編集可能インストール）</summary>

```bash
git clone https://github.com/ryok/ableton-cli.git
cd ableton-cli
uv venv && uv pip install -e .
source .venv/bin/activate
```

</details>

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

# アイテムの詳細取得
ableton browser get -p "instruments/Synths/Bass"
ableton browser get -u "query:Synths#Instrument%20Rack:Bass:FileId_5116"

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

## AI エージェント向けスキル

[`skills/`](skills/) ディレクトリに [Claude Code スキル](https://docs.anthropic.com/en/docs/claude-code/skills) を同梱しています。AI エージェントが CLI 経由で Ableton Live を操作できるようになります。

### セットアップ

**他のプロジェクト**でスキルを使う場合は `.claude/skills/` にコピーします:

```bash
cp -r /path/to/ableton-cli/skills/ableton-live /your/project/.claude/skills/
```

**全プロジェクト共通**のパーソナルスキルとして登録する場合:

```bash
cp -r /path/to/ableton-cli/skills/ableton-live ~/.claude/skills/
```

詳細は [`skills/README.md`](skills/README.md) を参照してください。

## ライセンス

MIT
