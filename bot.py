import asyncio
import os
import threading
from pyrogram import Client, filters, idle
from config import API_ID, API_HASH, BOT_TOKEN, db_CHANNEL_ID, OWNER_ID
from database import add_file, get_file_by_db_id
from utils import safe_reply
from app import app

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="TDBotDev")
)

def run_flask():
    # Flask for Render keep-alive
    app.run(host='0.0.0.0', port=8080)

# Real-time Channel Indexing handler
@bot.on_message(filters.chat(db_CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def channel_index_handler(client, message):
    media = message.document or message.video or message.audio
    file_id = media.file_id
    file_name = getattr(media, "file_name", "document_file")
    await add_file(file_id, file_name, message.caption, message_id=message.id, channel_id=db_CHANNEL_ID)

# Callback routing - handlers are now in plugins
# But centralized f# stays here for stability across all modes.

# Centralized File Delivery Callback
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
        await client.send_document(chat_id=cb.message.chat.id, document=file_id, caption=caption)
        await cb.answer()
    except Exception:
        await cb.answer("Error sending file", show_alert=True)

if __name__ == "__main__":
    # Start Flask in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    async def main():
        await bot.start()
        try:
            await bot.send_message(OWNER_ID, "**bot started successfully with ForceSub & Web Service ✅**")
        except Exception:
            pass
        await idle()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
