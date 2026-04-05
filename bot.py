import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import API_ID, API_HASH, BOT_TOKEN, START_TEXT, SEARCH_CHANNEL_ID, MAX_RESULTS
from database import add_file, search_files, get_file_by_db_id, collection

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 2 & 9 & 10 & 11: Channel History Indexing with specific logging and flood delay
async def index_channel_history(client: Client):
    print(f"Starting channel indexing for chat ID: {SEARCH_CHANNEL_ID}...")
    total_saved = 0

    try:
        # Resilient scanning
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
                    # Check if file already exists in DB before adding
                    existing = await collection.find_one({"file_id": file_id})
                    if not existing:
                        # Store original caption (fallback to file_name)
                        await add_file(file_id, file_name, caption)
                        # Logging format "Saved: <file_name>"
                        print(f"Saved: {file_name}")
                        total_saved += 1

                    # Performance delay (0.2s) to avoid flood
                    await asyncio.sleep(0.2)
            except Exception:
                # Handle individual message errors and continue
                continue
    except Exception as e:
        # Handle overall errors (e.g., Peer id invalid)
        print(f"Error during overall indexing loop: {str(e)}")

    # Completion message
    print(f"✅ Channel indexing completed. Total files saved: {total_saved}")

# 1 & 4: Start handler
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(START_TEXT)

# 8 & 13: Channel Indexing handler for NEW files
@bot.on_message(filters.chat(SEARCH_CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def channel_index_handler(client: Client, message: Message):
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
    else:
        return

    # Check if file exists to avoid duplicate logs/actions
    existing = await collection.find_one({"file_id": file_id})
    if not existing:
        await add_file(file_id, file_name, caption)
        print(f"Saved: {file_name}")

# 5, 6, 7: Auto search handler with specific messaging
@bot.on_message(filters.text & filters.private)
async def auto_search_handler(client: Client, message: Message):
    if message.text.startswith("/"):
        return

    status_msg = await message.reply_text("🔍 Searching... Please wait")

    query = message.text
    try:
        results = await search_files(query, limit=MAX_RESULTS)
    except Exception as e:
        await status_msg.edit_text(f"😔 An error occurred: {str(e)}")
        return

    if not results:
        await status_msg.edit_text("No files found 😔")
        return

    buttons = []
    for file in results:
        db_id = str(file['_id'])
        file_name = file['file_name']
        callback_data = f"f#{db_id}"

        try:
            buttons.append([InlineKeyboardButton(file_name, callback_data=callback_data)])
        except Exception:
            continue

    if not buttons:
        await status_msg.edit_text("No results available 😔")
        return

    await status_msg.edit_text(
        "Here are your results 👇",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 9, 10, 11, 13: Callback handler
@bot.on_callback_query(filters.regex(r"^f#"))
async def callback_handler(client: Client, callback_query: CallbackQuery):
    db_id = callback_query.data.split("#")[1]
    file_info = await get_file_by_db_id(db_id)

    if not file_info:
        await callback_query.answer("File not available", show_alert=True)
        return

    file_id = file_info['file_id']
    caption = file_info.get('caption') or file_info['file_name']

    try:
        await client.send_document(
            chat_id=callback_query.message.chat.id,
            document=file_id,
            caption=caption
        )
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer("Error sending file", show_alert=True)

if __name__ == "__main__":
    async def main():
        await bot.start()
        # Ensure indexing is complete before idling
        print("Bot started. Beginning channel history indexing...")
        await index_channel_history(bot)
        print("Initial channel indexing complete. Bot is now active for users.")
        await idle()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
