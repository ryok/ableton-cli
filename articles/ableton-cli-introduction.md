---
title: "Ableton Live を CLI で操作する — MCP より軽量なトークン効率重視のアプローチ"
emoji: "🎹"
type: "tech"
topics: ["ableton", "cli", "claude", "mcp", "ai"]
published: false
---

## はじめに

AI エージェント（Claude Code など）から Ableton Live を操作する方法として、[Ableton MCP](https://github.com/ahujasid/ableton-mcp) が知られています。MCP（Model Context Protocol）はツールを構造的に公開する優れた仕組みですが、**トークン効率**の観点では改善の余地があります。

本記事では、同じバックエンドを使いながらトークン消費を大幅に削減する **[ableton-cli](https://github.com/ryok/ableton-cli)** を紹介します。

## ableton-cli とは

Ableton Live をターミナルから操作する CLI ツールです。

```bash
# テンポを128に設定して、トラック作成して、再生
ableton tempo 128 && ableton track create && ableton clip fire 0 0
```

内部的には Ableton MCP と**同じ Remote Script**（TCP:9877）に接続しています。つまり機能は同一で、AI との接続方式だけが違います。

## アーキテクチャ比較

```
Ableton MCP:   Claude → MCP JSON-RPC → Remote Script (TCP:9877)
ableton-cli:   Claude → Bash → CLI    → Remote Script (TCP:9877)
```

重要なのは、バックエンドが共通だということ。Ableton 側で動く Remote Script はまったく同じものです。違いは「Claude がどうやって操作を送るか」だけ。

## なぜ CLI の方がトークン効率が良いのか

### 1. 固定オーバーヘッド：ツール定義のコスト

MCP を使うと、17 個のツール定義（name, description, parameters の JSON Schema）が**毎ターンの system prompt に含まれます**。これだけで数千トークンの固定コストが発生します。

CLI の場合、Claude が使うツールは既存の `Bash` ひとつだけ。コマンド体系はスキルや `--help` で一度学習すれば済むので、**固定コストはほぼゼロ**です。

### 2. 呼び出し時のコスト

```python
# MCP（1操作 = 1ツール呼び出し）
mcp__ableton-mcp__set_tempo(bpm=128)
# → JSON-RPC request + JSON response（スキーマ付き）

# CLI（1操作 = 1 Bash コマンド）
ableton tempo 128
# → "Tempo set to 128 BPM"（短い stdout テキスト）
```

CLI の方がコマンド文字列が短く、レスポンスもテキストベースで簡潔です。

### 3. バッチ操作

MCP ではノートを追加してクリップを再生するのに **2 回のツール呼び出し**が必要です：

```python
mcp__ableton-mcp__add_notes_to_clip(track=0, slot=0, notes=[...])
mcp__ableton-mcp__fire_clip(track_index=0, clip_index=0)
```

CLI なら `&&` でチェーンして **1 回の Bash 呼び出し**で完了：

```bash
ableton clip add-notes 0 0 '[...]' && ableton clip fire 0 0
```

## 比較まとめ

| 観点 | MCP | CLI | 優位 |
|------|-----|-----|------|
| 固定コスト | ツール定義 17 個分が毎ターン消費 | Bash ツール 1 つで十分 | **CLI** |
| 呼び出しコスト | JSON-RPC + Schema | 短いシェルコマンド | **CLI** |
| バッチ効率 | 操作ごとに 1 往復 | `&&` でチェーン可能 | **CLI** |
| 型安全性 | JSON Schema でバリデーション | なし | MCP |
| 発見性 | ツール一覧が自動公開 | `--help` やスキルが必要 | MCP |

トークン効率では CLI が明確に優位。型安全性と自動発見性では MCP に分があります。

## インストール

### 1. Remote Script（Ableton 側）

[AbletonMCP](https://github.com/ahujasid/ableton-mcp) の `AbletonMCP_Remote_Script` を Ableton の Remote Scripts ディレクトリにコピーします：

```
~/Music/Ableton/User Library/Remote Scripts/AbletonMCP_Remote_Script/
```

Ableton Live の設定 → Link, Tempo & MIDI → Control Surface で **AbletonMCP** を選択。

### 2. CLI のインストール

```bash
uv tool install git+https://github.com/ryok/ableton-cli.git
```

これだけで `ableton` コマンドがグローバルに使えるようになります。

:::message
既に Ableton MCP を使っている場合は `.mcp.json` から `ableton-mcp` を削除するだけで切り替え完了。Remote Script は同じなのでそのまま動きます。
:::

## 使い方

### 基本操作

```bash
# セッション情報を確認
ableton session

# テンポ変更
ableton tempo 120

# 再生 / 停止
ableton play
ableton stop
```

### トラック操作

```bash
# MIDI トラック作成
ableton track create

# トラック名変更
ableton track rename 0 "Bass"

# トラック情報確認
ableton track info 0
```

### クリップ操作

```bash
# クリップ作成（8ビート）
ableton clip create 0 0 --length 8

# MIDI ノート追加（Cメジャーコード）
ableton clip add-notes 0 0 '[
  {"pitch": 60, "start_time": 0, "duration": 1, "velocity": 100},
  {"pitch": 64, "start_time": 0, "duration": 1, "velocity": 90},
  {"pitch": 67, "start_time": 0, "duration": 1, "velocity": 90}
]'

# クリップ再生
ableton clip fire 0 0
```

### ブラウザ & インストゥルメント

```bash
# ブラウザのカテゴリツリー
ableton browser tree -c instruments

# アイテム一覧
ableton browser items "instruments/Synths"

# インストゥルメントをロード
ableton load 0 "query:Synths#Instrument%20Rack:Bass:FileId_5116"
```

## Claude Code のスキルとして使う

ableton-cli には [Claude Code スキル](https://github.com/ryok/ableton-cli/tree/main/skills/ableton-live) が同梱されています。これを設定すると、Claude が Ableton の操作方法を自動的に把握し、音楽制作の会話で適切なコマンドを実行してくれます。

### スキルのインストール

```bash
# 特定プロジェクトで使う
cp -r /path/to/ableton-cli/skills/ableton-live /your/project/.claude/skills/

# 全プロジェクト共通で使う
cp -r /path/to/ableton-cli/skills/ableton-live ~/.claude/skills/
```

スキルには以下が含まれます：
- 全コマンドのリファレンス
- MIDI ノート番号 ↔ 音名の対応表
- GM ドラムマップ
- 推奨ワークフロー（セッション確認 → トラック作成 → 楽器ロード → クリップ作成 → ノート追加）

## 実践例：4小節のドラムパターンを作る

```bash
# 1. テンポ設定 + MIDI トラック作成
ableton tempo 100 && ableton track create

# 2. トラック名変更
ableton track rename 0 "Drums"

# 3. 4小節のクリップ作成
ableton clip create 0 0 --length 16

# 4. キック + スネア + ハイハットのパターン
ableton clip add-notes 0 0 '[
  {"pitch": 36, "start_time": 0, "duration": 0.5, "velocity": 110},
  {"pitch": 42, "start_time": 0, "duration": 0.25, "velocity": 70},
  {"pitch": 42, "start_time": 0.5, "duration": 0.25, "velocity": 60},
  {"pitch": 38, "start_time": 1, "duration": 0.5, "velocity": 100},
  {"pitch": 42, "start_time": 1, "duration": 0.25, "velocity": 70},
  {"pitch": 42, "start_time": 1.5, "duration": 0.25, "velocity": 60},
  {"pitch": 36, "start_time": 2, "duration": 0.5, "velocity": 110},
  {"pitch": 42, "start_time": 2, "duration": 0.25, "velocity": 70},
  {"pitch": 42, "start_time": 2.5, "duration": 0.25, "velocity": 60},
  {"pitch": 38, "start_time": 3, "duration": 0.5, "velocity": 100},
  {"pitch": 42, "start_time": 3, "duration": 0.25, "velocity": 70},
  {"pitch": 42, "start_time": 3.5, "duration": 0.25, "velocity": 60}
]'

# 5. 再生
ableton clip fire 0 0
```

## MCP から CLI に移行する

1. CLI をインストール：
   ```bash
   uv tool install git+https://github.com/ryok/ableton-cli.git
   ```

2. `.mcp.json` から `ableton-mcp` を削除

3. （任意）スキルを追加して CLI の使い方を Claude に教える：
   ```bash
   cp -r /path/to/ableton-cli/skills/ableton-live ~/.claude/skills/
   ```

Remote Script はそのまま。機能は一切失われません。

## まとめ

- **ableton-cli** は Ableton MCP と同じ Remote Script を使う、トークン効率重視の CLI ツール
- ツール定義の固定コスト削減、コマンドチェーンによるバッチ実行が主なメリット
- `uv tool install` で 1 コマンドインストール
- Claude Code スキルを同梱しており、AI エージェントがすぐに使える

リポジトリ：https://github.com/ryok/ableton-cli
