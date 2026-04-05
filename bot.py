import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import API_ID, API_HASH, BOT_TOKEN, START_TEXT, SEARCH_CHANNEL_ID, MAX_RESULTS, OWNER_ID
from database import add_file, search_files, get_file_by_db_id, collection

# 7: Integration - importing TDBotDev submodules
import TDBotDev.start
import TDBotDev.admin

# Initialize Bot
bot = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="TDBotDev") # Load handlers from TDBotDev
)

# Channel History Indexing
async def index_channel_history(client: Client):
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

# Indexing handler for NEW files
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

    existing = await collection.find_one({"file_id": file_id})
    if not existing:
        await add_file(file_id, file_name, caption)
        print(f"Saved: {file_name}")

# Auto search handler
@bot.on_message(filters.text & filters.private & ~filters.command(["start", "reset"]))
async def auto_search_handler(client: Client, message: Message):
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

# Callback handler
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
        print("Bot started. Beginning channel history indexing...")
        await index_channel_history(bot)

        # Bot started successfully notification to owner
        try:
            await bot.send_message(OWNER_ID, "bot started successfully ✅")
        except Exception as e:
            print(f"Failed to send startup message to owner: {e}")

        print("Initial channel indexing complete. Bot is now active for users.")
        await idle()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
