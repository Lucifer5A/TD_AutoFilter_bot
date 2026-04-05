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

# 1 & 4: Start handler
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(START_TEXT)

# 10: Channel Indexing handler
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

# 5, 6, 7, 8, 11: Auto search handler with instant feedback
@bot.on_message(filters.text & filters.private)
async def auto_search_handler(client: Client, message: Message):
    # Simple manually filtering out commands to avoid common Pyrogram filter issues
    if message.text.startswith("/"):
        return

    # 5: Immediate reply for instant feedback
    status_msg = await message.reply_text("🔍 Searching for your file...")

    query = message.text
    # 6: Search in MongoDB
    try:
        results = await search_files(query, limit=MAX_RESULTS)
    except Exception as e:
        await status_msg.edit_text(f"😔 An error occurred while searching: {str(e)}")
        return

    if not results:
        # 8: Edit message if no results
        await status_msg.edit_text("😔 Sorry, I couldn't find anything for that")
        return

    # 7: Edit message and add inline buttons
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

# 9 & 11: Callback handler
@bot.on_callback_query(filters.regex(r"^f#"))
async def callback_handler(client: Client, callback_query: CallbackQuery):
    db_id = callback_query.data.split("#")[1]
    file_info = await get_file_by_db_id(db_id)

    if not file_info:
        await callback_query.answer("File not available", show_alert=True)
        return

    file_id = file_info['file_id']

    # 9: Send file instantly with requested caption
    try:
        await client.send_document(
            chat_id=callback_query.message.chat.id,
            document=file_id,
            caption="📥 Here is your file"
        )
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer("Error sending file", show_alert=True)

if __name__ == "__main__":
    bot.run()
