from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import API_ID, API_HASH, BOT_TOKEN, START_TEXT, SEARCH_CHANNEL_ID
from database import add_file, search_files, get_file_by_db_id

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 1 & 4: Start handler
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(START_TEXT)

# 6: Channel Indexing handler
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

    add_file(file_id, file_name)

# 5 & 7 & 11: Auto search handler
@bot.on_message(filters.text & filters.private)
async def auto_search_handler(client: Client, message: Message):
    # Skip commands
    if message.text.startswith("/"):
        return

    query = message.text
    results = search_files(query)

    if not results:
        # 9: No results found
        await message.reply_text("No files found 😔")
        return

    # 7: Display results as inline keyboard buttons
    buttons = []
    # Limit to 50 results to avoid Telegram's button limits
    for file in results[:50]:
        db_id = str(file['_id'])
        file_name = file['file_name']

        # Use database ID instead of file_id to stay within 64-byte limit
        callback_data = f"f#{db_id}"

        try:
            buttons.append([InlineKeyboardButton(file_name, callback_data=callback_data)])
        except Exception:
            continue

    if not buttons:
        await message.reply_text("No results available 😔")
        return

    await message.reply_text(
        "Search results:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 8 & 9 & 11: Callback handler
@bot.on_callback_query(filters.regex(r"^f#"))
async def callback_handler(client: Client, callback_query: CallbackQuery):
    db_id = callback_query.data.split("#")[1]
    file_info = get_file_by_db_id(db_id)

    if not file_info:
        # 9: File not found during callback
        await callback_query.answer("File not available", show_alert=True)
        return

    file_id = file_info['file_id']
    file_name = file_info['file_name']

    # 8: Send file using send_document
    try:
        await client.send_document(
            chat_id=callback_query.message.chat.id,
            document=file_id,
            caption=file_name
        )
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer("Error sending file", show_alert=True)

if __name__ == "__main__":
    bot.run()
