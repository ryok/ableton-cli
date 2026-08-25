# ableton-cli

Ableton Live をターミナルから操作する CLI ツール。同梱している AbletonMCP Remote Script と TCP ソケットで通信します。

## なぜ MCP ではなく CLI？

ableton-cli は [Ableton MCP](https://github.com/ahujasid/ableton-mcp) をベースにした同梱 Remote Script を使います。CLI 用の command handler を追加しており、AI エージェントは CLI 経由で Remote Script の TCP ソケットへ命令を送ります。

```
Ableton MCP:   Claude -> MCP JSON-RPC -> Remote Script (TCP:9877)
ableton-cli:   Claude -> Bash -> CLI    -> 同梱 Remote Script (TCP:9877)
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

このリポジトリを clone または download して、`remote_scripts/AbletonMCP_Remote_Script` フォルダを Ableton の MIDI Remote Scripts ディレクトリにコピーします。

```
# macOS
~/Music/Ableton/User Library/Remote Scripts/AbletonMCP_Remote_Script/

# Windows
~\Documents\Ableton\User Library\Remote Scripts\AbletonMCP_Remote_Script\
```

Ableton Live の設定 → Link, Tempo & MIDI → Control Surface で **AbletonMCP** を選択します。

この script は `ahujasid/ableton-mcp` をベースに ableton-cli 用の変更を加えたものです。元にした commit と変更点は [`remote_scripts/README.md`](remote_scripts/README.md) を参照してください。

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
ableton track mute 0           # ミュート（--off で解除）
ableton track solo 0           # ソロ（--off で解除）
ableton track volume 0 --db -4.6   # 音量を dB で指定（ミキサーの表示値）
ableton track delete 3         # トラック削除（--yes で確認を省略）
```

音量について一点。Live はミキサーのフェーダーを 0-1 のパラメータとして公開して
いますが、これは非線形カーブ上の値で（0.85 が約 0dB）、dB のセッターはありません。
`--db` は Live が表示する値を見ながら二分探索して一致させます。生のパラメータを
直接指定したい場合は `--value` を使ってください。

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

# 入ったノートを読み戻して確認する
ableton clip notes 0 0 --count

# Session クリップを Arrangement の beat 0 へコピー
ableton clip to-arrangement 0 0 0

# 再生 / 停止
ableton clip fire 0 0
ableton clip stop 0 0
```

ここは Live API の制約が2つ効いています。Arrangement クリップは新規作成できないので、
まず Session クリップを作って `to-arrangement` で複製します。削除もできませんが、
既存の領域にクリップを置くと上書きされるので、誤配置は「正しいものを同じ位置に置く」
ことで直せます。

数百音を超えると `add-notes` はシェルの引数長制限に引っかかります。ファイルから
読ませてください:

```bash
ableton clip add-notes 0 0 --file notes.json
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

### ブラウザ項目の読み込み

```bash
# URI を指定してロード
ableton load 0 "query:Synths#Instrument%20Rack:Bass:FileId_5116"

# サンプルやブラウザ項目を Session View の特定スロットへロード
ableton load-slot 2 0 "query:UserLibrary#Samples:auto-dtm:chop_08_outro_vocal.wav"

# サンプルやブラウザ項目を Arrangement View の拍位置へロード
ableton load-arrangement 3 16 "query:UserLibrary#Samples:auto-dtm:chop_10_swing_loop.wav"

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
