import asyncio
from pyrogram import Client, filters, idle
from config import API_ID, API_HASH, BOT_TOKEN, SEARCH_CHANNEL_ID, OWNER_ID
from database import add_file, collection, get_file_by_db_id

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="TDBotDev")
)

# Flag to prevent usage during indexing
IS_INDEXING = True

async def index_channel_history(client: Client):
    global IS_INDEXING
    print(f"Starting channel indexing for chat ID: {SEARCH_CHANNEL_ID}...")
    total_saved = 0
    try:
        async for message in client.get_chat_history(SEARCH_CHANNEL_ID):
            try:
                file_id = None
                file_name = None
                caption = message.caption
                if message.document:
                    file_id = message.document.file_id
                    file_name = message.document.file_name or "document_file"
                elif message.video:
                    file_id = message.video.file_id
                    file_name = message.video.file_name or "video_file"
                elif message.audio:
                    file_id = message.audio.file_id
                    file_name = message.audio.file_name or "audio_file"
                if file_id and file_name:
                    existing = await collection.find_one({"file_id": file_id})
                    if not existing:
                        await add_file(file_id, file_name, caption)
                        print(f"Saved: {file_name}")
                        total_saved += 1
                    await asyncio.sleep(0.2)
            except Exception:
                continue
    except Exception as e:
        print(f"Error during overall indexing loop: {str(e)}")
    print(f"✅ Channel indexing completed. Total files saved: {total_saved}")
    IS_INDEXING = False

@bot.on_message(filters.chat(SEARCH_CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def channel_index_handler(client, message):
    caption = message.caption
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "document_file"
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video_file"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio_file"
    else: return
    existing = await collection.find_one({"file_id": file_id})
    if not existing:
        await add_file(file_id, file_name, caption)
        print(f"Saved: {file_name}")

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
    async def main():
        await bot.start()
        await index_channel_history(bot)
        try: await bot.send_message(OWNER_ID, "bot started successfully ✅")
        except: pass
        await idle()
    asyncio.get_event_loop().run_until_complete(main())
