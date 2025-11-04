import os
import io
import requests
import discord
from discord.ext import commands
from threading import Thread
from flask import Flask

# ==== 環境変数 ====
DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
B_CHANNEL_ID = int(os.environ["B_CHANNEL_ID"])
OCR_API_KEY = os.environ["OCR_SPACE_API_KEY"]
DEEPL_API_KEY = os.environ["DEEPL_API_KEY"]
ALLOWED_USER_ID = os.environ.get("ALLOWED_USER_ID", "").strip()

# ==== Flaskサーバー（Render監視用） ====
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello Render! Discord OCR Bot is running.", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ==== Discord Bot ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def ocr_space_bytes(file_bytes: bytes, filename: str, lang_hint="chs,cht") -> str:
    url = "https://api.ocr.space/parse/image"
    files = {"file": (filename, io.BytesIO(file_bytes))}
    data = {
        "apikey": OCR_API_KEY,
        "language": lang_hint,
        "isOverlayRequired": False,
        "scale": True,
        "OCREngine": 2
    }
    r = requests.post(url, files=files, data=data, timeout=180)
    r.raise_for_status()
    js = r.json()
    if js.get("IsErroredOnProcessing"):
        raise RuntimeError(js.get("ErrorMessage") or "OCR error")
    results = js.get("ParsedResults") or []
    return "\n".join([r.get("ParsedText", "") for r in results]).strip()

def deepl_zh_to_ja(text: str) -> str:
    if not text.strip():
        return ""
    url = "https://api-free.deepl.com/v2/translate"
    data = {"text": text, "target_lang": "JA", "source_lang": "ZH"}
    headers = {"Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"}
    r = requests.post(url, data=data, headers=headers, timeout=180)
    r.raise_for_status()
    js = r.json()
    return "\n".join([t["text"] for t in js.get("translations", [])]).strip()

async def process_attachment(message: discord.Message):
    if ALLOWED_USER_ID and str(message.author.id) != ALLOWED_USER_ID:
        return
    if not message.attachments:
        return
    for att in message.attachments:
        ct = (att.content_type or "").lower()
        if not (ct.startswith("image/") or ct == "application/pdf"):
            continue
        try:
            file_bytes = await att.read()
            zh_text = ocr_space_bytes(file_bytes, att.filename, lang_hint="chs,cht")
            if not zh_text:
                await message.reply("OCR結果が空でした。画質を上げて再投稿してください。")
                return
            ja_text = deepl_zh_to_ja(zh_text) or "(翻訳なし)"
            embed = discord.Embed(
                title="🈶→🇯🇵 自動翻訳（中国語→日本語）",
                description=(ja_text[:3900] + "…") if len(ja_text) > 3900 else ja_text,
                color=0x2ecc71
            )
            excerpt = zh_text[:1000] + ("…" if len(zh_text) > 1000 else "")
            embed.add_field(name="原文（抜粋）", value=excerpt or "(空)", inline=False)
            embed.set_footer(text=f"投稿者: {message.author.display_name}")
            await message.reply(embed=embed)
        except Exception as e:
            await message.reply(f"エラー: {e}")
        break

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.channel.id == B_CHANNEL_ID:
        await process_attachment(message)
    await bot.process_commands(message)

if __name__ == "__main__":
    # FlaskとDiscordを同時起動
    Thread(target=run_flask).start()
    bot.run(DISCORD_TOKEN)
