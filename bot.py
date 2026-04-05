from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import API_ID, API_HASH, BOT_TOKEN, START_TEXT
from database import init_db, add_file, search_files, get_file_by_id

# Initialize Database
init_db()

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 1 & 3: Start handler
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(START_TEXT)

# 5: Message listener for indexing files from private channel
# The bot must be admin in the channel
@bot.on_message(filters.chat_type.CHANNEL & (filters.document | filters.video | filters.audio))
async def channel_handler(client: Client, message: Message):
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name or "video_file"
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio_file"
    else:
        return

    add_file(file_id, file_name)

# 5 & 11: Auto search handler
@bot.on_message(filters.text & ~filters.command & filters.private)
async def search_handler(client: Client, message: Message):
    query = message.text
    results = search_files(query)

    if not results:
        # 8: No results found
        await message.reply_text("No files found 😔")
        return

    # 6: Display results as inline keyboard buttons
    buttons = []
    for db_id, file_name in results:
        buttons.append([InlineKeyboardButton(file_name, callback_data=f"file_{db_id}")])

    await message.reply_text(
        "Found results:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 7 & 9 & 11: Callback query handler
@bot.on_callback_query(filters.regex(r"^file_"))
async def callback_handler(client: Client, callback_query: CallbackQuery):
    db_id = callback_query.data.split("_")[1]
    result = get_file_by_id(db_id)

    if not result:
        # 9: File not found during callback
        await callback_query.answer("File not available", show_alert=True)
        return

    file_id, file_name = result

    # 7: Send the file using send_document
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
