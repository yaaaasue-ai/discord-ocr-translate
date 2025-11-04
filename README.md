# Discord OCR→翻訳 Bot（方式A：OCR.space + DeepL API）

Bサーバーの **特定チャンネル** に投稿された **スクリーンショット（画像/PDF）** を自動で読み取り、
**中国語→日本語** に翻訳して、**返信(Embed)** します。  
Aサーバーの内容は直接読みません。あなたが**スクショをBチャンネルに貼る**だけでOK。

---

## 構成
- 言語: Python 3.11 以降推奨
- Discordライブラリ: `discord.py`
- OCR: [OCR.space API](https://ocr.space/ocrapi)（無料枠 25,000リク/月）
- 翻訳: [DeepL API Free](https://www.deepl.com/pro-api)（無料枠 500,000文字/月）
- 常時稼働: Render / Railway 等の **Background Worker**

---

## できること
- 画像（PNG/JPG）および PDF（1ファイル）から文字をOCR抽出（中国語優先）
- DeepLで **中国語→日本語** 翻訳
- 翻訳結果を **Embed** で返信（原文の抜粋も併載）
- （任意）`ALLOWED_USER_ID` で投稿者を限定

---

## 前提（必要アカウント）
1. **Discord Bot** … Developer Portal で作成し、Bサーバーに招待
2. **OCR.space** … 無料APIキーを取得（メール登録のみ）
3. **DeepL API Free** … 無料APIキーを取得

### Discord Bot 作成と招待
1. https://discord.com/developers/applications → **New Application**
2. **Bot** を作成 → **TOKEN** を控える（**Reset**→**Copy**）
3. **Privileged Gateway Intents** で **Message Content Intent** を ON
4. **OAuth2 → URL Generator**
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Attach Files`, `Read Message History`, `View Channels`
5. 生成URLで **Bサーバー** に招待（監視対象のチャンネルが見えるロール/権限を付与）

### チャンネルIDの取得（B_CHANNEL_ID）
- Discordクライアント → ユーザー設定 → **詳細設定** → **開発者モード** ON
- 対象 **Bチャンネルを右クリック → IDをコピー**

### OCR.space APIキー
- https://ocr.space/ocrapi → `Register for free API key`
- 受信メールのAPIキーを控える（`OCR_SPACE_API_KEY`）

### DeepL API Free キー
- https://www.deepl.com/pro-api → **Free** を選択して登録
- アカウントページで **Auth Key** を取得（`DEEPL_API_KEY`）

---

## .env（例）
ローカル動作用。Render では **Dashboardの環境変数** に設定します。

```
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
B_CHANNEL_ID=123456789012345678
OCR_SPACE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPL_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 任意：あなた以外を無視したい場合
ALLOWED_USER_ID=987654321012345678
```

> **注意**: `.env` は配布禁止。漏洩防止のためGit管理から除外してください。

---

## セットアップ（ローカル）
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# .env を作成して環境変数をエクスポートするか、シェルで直接 export してください
python app.py
```

## デプロイ（Render の例）
1. 新規サービス → **Background Worker**
2. リポジトリ接続 or ZIPアップロード
3. **Procfile** を検出（`worker: python app.py`）
4. 環境変数を設定：`DISCORD_BOT_TOKEN`, `B_CHANNEL_ID`, `OCR_SPACE_API_KEY`, `DEEPL_API_KEY`, `ALLOWED_USER_ID(任意)`
5. ランタイム: Python 3.11 / 3.12 を推奨
6. Deploy → ログに `✅ Logged in as ...` が出ればOK

---

## 使い方
1. **Bチャンネル** に **スクリーンショット画像（またはPDF）** を投稿
2. Botが自動でOCR→翻訳→**返信**（Embed）します

> JPG/PNG/PDF 以外はスキップ。必要なら拡張子チェックを緩めてください。

---

## よくある詰まり
- **Botの権限不足**：チャンネルが見えない / メッセージ履歴を読めない → 権限付与
- **Message Content Intent 未ON**：本文取得が制限 → Developer PortalでON
- **APIキー誤り/レート制限**：ログのエラーメッセージを確認、一定時間後に再試行
- **画質が低い**：OCR精度が落ちます。解像度UP/コントラスト改善を。

---

## セキュリティ
- このBotは**あなたがBチャンネルに投稿した画像**のみ処理します。Aサーバーの読み取りは行いません。
- APIキーは**環境変数**で管理し、リポジトリには保存しないでください。

---

## 免責
各APIの無料枠・利用規約は変更されることがあります。最新の公式情報をご確認ください。
