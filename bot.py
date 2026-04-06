import asyncio
import os
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, idle

from config import API_ID, API_HASH, BOT_TOKEN, db_CHANNEL_ID, OWNER_ID
from database import add_file, get_file_by_db_id

# ---------------- FLASK SERVER ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- PYROGRAM BOT ----------------
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="TDBotDev")
)

# Channel indexing
@bot.on_message(filters.chat(db_CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def channel_index_handler(client, message):
    media = message.document or message.video or message.audio
    file_id = media.file_id
    file_name = getattr(media, "file_name", "document_file")

    await add_file(
        file_id,
        file_name,
        message.caption,
        message_id=message.id,
        channel_id=db_CHANNEL_ID
    )

# File callback
@bot.on_callback_query(filters.regex(r"^f#"))
async def file_callback_handler(client, cb):
    db_id = cb.data.split("#")[1]
    file_info = await get_file_by_db_id(db_id)

    if not file_info:
        await cb.answer("File not available", show_alert=True)
        return

    file_id = file_info['file_id']
    caption = file_info.get('caption') or file_info['file_name']

    try:
        await client.send_document(
            chat_id=cb.message.chat.id,
            document=file_id,
            caption=caption
        )
        await cb.answer()
    except Exception:
        await cb.answer("Error sending file", show_alert=True)

# ---------------- START BOTH ----------------
async def start_bot():
    await bot.start()

    try:
        await bot.send_message(OWNER_ID, "bot started successfully ✅")
    except Exception:
        pass

    await idle()

def run_bot():
    asyncio.run(start_bot())

if __name__ == "__main__":
    # Flask in background thread
    Thread(target=run_flask).start()

    # Bot in main thread
    run_bot()
