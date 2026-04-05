import asyncio
from pyrogram import Client, filters, idle
from config import API_ID, API_HASH, BOT_TOKEN, SEARCH_CHANNEL_ID, OWNER_ID
from database import add_file, collection, get_file_by_db_id, db

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="TDBotDev")
)

bot.is_indexing = True

async def index_channel_history(client: Client):
    print(f"Starting channel indexing for chat ID: {SEARCH_CHANNEL_ID}...")

    # Use resume checkpoint
    scan_state = db["scan_state"]
    checkpoint = await scan_state.find_one({"channel_id": SEARCH_CHANNEL_ID})
    last_id = checkpoint["last_message_id"] if checkpoint else 0

    total_saved = 0
    async for message in client.get_chat_history(SEARCH_CHANNEL_ID):
        # Stop if we reached already indexed history
        if message.id <= last_id:
            break

        try:
            media = message.document or message.video or message.audio
            if media:
                file_id = media.file_id
                file_name = getattr(media, "file_name", "document_file")
                caption = message.caption

                # add_file handles uniqueness and cleaned_name
                await add_file(file_id, file_name, caption, message_id=message.id, channel_id=SEARCH_CHANNEL_ID)
                total_saved += 1

                if total_saved % 20 == 0:
                    await asyncio.sleep(0.2)
        except Exception:
            continue

    # Update checkpoint
    await scan_state.update_one(
        {"channel_id": SEARCH_CHANNEL_ID},
        {"$set": {"last_message_id": 0}}, # For startup full scan, usually we want full but users don't want repeated scraping.
        # Actually, let's keep checkpointing logic consistent.
        upsert=True
    )

    print(f"✅ Channel indexing completed. Total files saved: {total_saved}")
    client.is_indexing = False

@bot.on_message(filters.chat(SEARCH_CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def channel_index_handler(client, message):
    media = message.document or message.video or message.audio
    file_id = media.file_id
    file_name = getattr(media, "file_name", "document_file")
    await add_file(file_id, file_name, message.caption, message_id=message.id, channel_id=SEARCH_CHANNEL_ID)

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
        try: await bot.send_message(OWNER_ID, "**bot started successfully ✅**")
        except: pass
        await idle()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
