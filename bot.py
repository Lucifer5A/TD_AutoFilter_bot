import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import API_ID, API_HASH, BOT_TOKEN, START_TEXT, SEARCH_CHANNEL_ID, MAX_RESULTS
from database import add_file, search_files, get_file_by_db_id

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 2 & 3: Channel History Indexing
async def index_channel_history(client: Client):
    print(f"Starting channel indexing for chat ID: {SEARCH_CHANNEL_ID}...")
    count = 0

    try:
        # Use get_chat_history to scan full history
        async for message in client.get_chat_history(SEARCH_CHANNEL_ID):
            file_id = None
            file_name = None

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
                # 6 & 10: add_file uses upsert=True which avoids duplicates
                await add_file(file_id, file_name)
                print(f"Indexed: {file_name}")
                count += 1

                # 7: Small delay to avoid flood
                if count % 20 == 0:
                    await asyncio.sleep(1)

        print(f"Channel indexing completed. Total files saved: {count}")
    except Exception as e:
        print(f"Error during indexing: {str(e)}")

# 1 & 4: Start handler
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(START_TEXT)

# 10: Channel Indexing handler for NEW files
@bot.on_message(filters.chat(SEARCH_CHANNEL_ID) & (filters.document | filters.video | filters.audio))
async def channel_index_handler(client: Client, message: Message):
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

    await add_file(file_id, file_name)

# 5, 6, 7, 13: Auto search handler with specific messaging
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

# 8, 11: Callback handler
@bot.on_callback_query(filters.regex(r"^f#"))
async def callback_handler(client: Client, callback_query: CallbackQuery):
    db_id = callback_query.data.split("#")[1]
    file_info = await get_file_by_db_id(db_id)

    if not file_info:
        await callback_query.answer("File not available", show_alert=True)
        return

    file_id = file_info['file_id']

    # Send file instantly without caption as requested
    try:
        await client.send_document(
            chat_id=callback_query.message.chat.id,
            document=file_id
        )
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer("Error sending file", show_alert=True)

if __name__ == "__main__":
    # Custom startup to trigger history indexing
    async def main():
        await bot.start()
        # Trigger history indexing on startup
        asyncio.create_task(index_channel_history(bot))
        print("Bot started and channel history indexing initiated in background.")
        await asyncio.Event().wait()  # Keep the main coroutine running

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
