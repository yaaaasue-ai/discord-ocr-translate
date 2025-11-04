import os
import io
import requests
import discord
from discord.ext import commands

# ==== 環境変数 ====
DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
B_CHANNEL_ID = int(os.environ["B_CHANNEL_ID"])  # 監視対象Bチャンネル
OCR_API_KEY = os.environ["OCR_SPACE_API_KEY"]   # https://ocr.space/ocrapi
DEEPL_API_KEY = os.environ["DEEPL_API_KEY"]     # https://www.deepl.com/docs-api
ALLOWED_USER_ID = os.environ.get("ALLOWED_USER_ID", "").strip()  # 任意: 投稿者制限

# ==== Discord設定 ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== OCR (OCR.space) ====
def ocr_space_bytes(file_bytes: bytes, filename: str, lang_hint: str = "chs,cht") -> str:
    url = "https://api.ocr.space/parse/image"
    files = {"file": (filename, io.BytesIO(file_bytes))}
    data = {
        "apikey": OCR_API_KEY,
        "language": lang_hint,          # 簡体: chs / 繁体: cht / 英数: eng
        "isOverlayRequired": False,
        "scale": True,
        "OCREngine": 2
    }
    resp = requests.post(url, files=files, data=data, timeout=180)
    resp.raise_for_status()
    js = resp.json()
    if js.get("IsErroredOnProcessing"):
        raise RuntimeError(js.get("ErrorMessage") or "OCR.space error")
    results = js.get("ParsedResults") or []
    text = "
".join([r.get("ParsedText", "") for r in results]).strip()
    return text

# ==== 翻訳 (DeepL) ====
def deepl_zh_to_ja(text: str) -> str:
    if not text.strip():
        return ""
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "text": text,
        "target_lang": "JA",
        "source_lang": "ZH"
    }
    headers = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
    resp = requests.post(url, data=data, headers=headers, timeout=180)
    resp.raise_for_status()
    js = resp.json()
    translations = js.get("translations", [])
    return "\n".join([t.get("text", "") for t in translations]).strip()

async def process_attachment(message: discord.Message):
    # 投稿者制限（任意）
    if ALLOWED_USER_ID and str(message.author.id) != ALLOWED_USER_ID:
        return

    if not message.attachments:
        return

    # 画像/PDFのみ処理（最初のファイルだけ。必要ならループ）
    for att in message.attachments:
        ct = (att.content_type or "").lower()
        if not (ct.startswith("image/") or ct == "application/pdf"):
            continue

        try:
            file_bytes = await att.read()
            # OCR（中国語優先）
            zh_text = ocr_space_bytes(file_bytes, att.filename, lang_hint="chs,cht")
            if not zh_text:
                await message.reply("OCRの結果が空でした。画質を上げて再投稿してください。", mention_author=False)
                return

            # 翻訳
            ja_text = deepl_zh_to_ja(zh_text) or "(翻訳結果なし)"
            # Embedで返信（原文の抜粋も併載）
            embed = discord.Embed(
                title="🈶→🇯🇵 自動翻訳（中国語→日本語）",
                description=(ja_text[:3900] + "…") if len(ja_text) > 3900 else ja_text,
                color=0x2ecc71
            )
            excerpt = zh_text[:1000] + ("…" if len(zh_text) > 1000 else "")
            embed.add_field(name="原文（抜粋）", value=excerpt or "(空)", inline=False)
            embed.set_footer(text=f"投稿者: {message.author.display_name}")
            await message.reply(embed=embed, mention_author=False)
        except Exception as e:
            await message.reply(f"処理中にエラーが発生しました：{e}", mention_author=False)
        break  # 最初の対応ファイルのみ

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    # 自分のメッセージは無視
    if message.author == bot.user:
        return
    # 対象チャンネルのみ処理
    if message.channel.id == B_CHANNEL_ID:
        await process_attachment(message)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
