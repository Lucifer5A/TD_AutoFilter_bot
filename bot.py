import asyncio
import os
import threading
from pyrogram import Client, filters, idle
from config import API_ID, API_HASH, BOT_TOKEN, db_CHANNEL_ID, OWNER_ID
from database import add_file, get_file_by_db_id
from utils import safe_reply
from app import app
from TDBotDev.forcesub import force_sub
from config import LOG_CHANNEL_ID

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
    # Force Subscribe Check
    if not await force_sub(client, cb.message, user_id=cb.from_user.id):
        return

    db_id = cb.data.split("#")[1]
    file_info = await get_file_by_db_id(db_id)
    if not file_info:
        await cb.answer("File not available", show_alert=True)
        return
    file_id = file_info['file_id']
    file_name = file_info['file_name']
    caption = file_info.get('caption') or file_name

    try:
        # STEP 1: Send/forward file to LOG_CHANNEL_ID
        # We forward it to ensure the log channel has the copy and it stays "clean" for step 2
        log_msg = await client.send_document(
            chat_id=LOG_CHANNEL_ID,
            document=file_id,
            caption=caption
        )

        # STEP 2: Forward same file from LOG_CHANNEL_ID to user
        await log_msg.forward(chat_id=cb.message.chat.id)

        # STEP 3: Log "File sent to user" with details
        sent_log = (
            f"✅ **File sent to user**\n\n"
            f"👤 **User:** {cb.from_user.mention}\n"
            f"🆔 **ID:** `{cb.from_user.id}`\n"
            f"📂 **File:** `{file_name}`\n"
            f"📅 **Time:** `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        await client.send_message(LOG_CHANNEL_ID, sent_log)

        await cb.answer()
    except Exception as e:
        print(f"File Send Error: {e}")
        await cb.answer("Error sending file", show_alert=True)

if __name__ == "__main__":
    # Start Flask in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    async def main():
        print(f"DEBUG: Active db_CHANNEL_ID = {db_CHANNEL_ID}")
        await bot.start()
        try:
            await bot.send_message(OWNER_ID, f"**bot started successfully with ForceSub & Web Service ✅**\n\n**Configured Channel ID:** `{db_CHANNEL_ID}`")
        except Exception:
            pass
        await idle()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
