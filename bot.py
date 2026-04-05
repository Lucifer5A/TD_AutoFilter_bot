import asyncio
import re
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import API_ID, API_HASH, BOT_TOKEN, START_TEXT, SEARCH_CHANNEL_ID, MAX_RESULTS, OWNER_ID
from database import add_file, search_files, get_file_by_db_id, collection

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

# Channel History Indexing
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

# Helper to truncate query for callback data (64 byte limit)
def pack_callback_data(prefix, query, filter_text, page):
    data = f"{prefix}#{query}#{filter_text or 'None'}#{page}"
    if len(data) > 64:
        query_limit = 64 - (len(prefix) + 1 + len(str(filter_text or 'None')) + 1 + len(str(page)) + 1)
        data = f"{prefix}#{query[:query_limit]}#{filter_text or 'None'}#{page}"
    return data

# Helper to generate professional Pagination UI
def get_ui_markup(query, filter_text, current_page, total_results, results):
    buttons = []
    # Quality & Language Filter buttons at TOP
    buttons.append([
        InlineKeyboardButton("Quality ⚡", callback_data=pack_callback_data("q", query, filter_text, current_page)),
        InlineKeyboardButton("Language 🎵", callback_data=pack_callback_data("l", query, filter_text, current_page))
    ])

    # File List (Buttons)
    for file in results:
        db_id = str(file['_id'])
        # EXACT file_name from database as requested
        file_name = file['file_name']
        buttons.append([InlineKeyboardButton(file_name, callback_data=f"f#{db_id}")])

    # Bottom Navigation
    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=pack_callback_data("p", query, filter_text, current_page - 1)))

    if (current_page + 1) * MAX_RESULTS < total_results:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=pack_callback_data("p", query, filter_text, current_page + 1)))

    if nav_row:
        buttons.append(nav_row)

    return InlineKeyboardMarkup(buttons)

# Auto search handler
@bot.on_message(filters.text & filters.private & ~filters.command(["start", "reset"]))
async def auto_search_handler(client: Client, message: Message):
    if IS_INDEXING:
        await message.reply_text("⏳ Please wait, indexing is in progress...")
        return

    # Intermediate message as requested
    status_msg = await message.reply_text("🔍 Searching... Please wait")

    query = message.text
    try:
        results, total_results = await search_files(query, limit=MAX_RESULTS)
    except Exception as e:
        await status_msg.edit_text(f"😔 An error occurred: {str(e)}")
        return

    if not results:
        await status_msg.edit_text("No files found 😔")
        return

    # UI Format
    query_display = query
    text = f"🔍 Found {total_results} results for: \"{query_display}\"\n\nPage 1\n\nClick on a file to get it:"

    markup = get_ui_markup(query, None, 0, total_results, results)

    await status_msg.edit_text(
        text,
        reply_markup=markup
    )

# Callback for Quality and Language filters
@bot.on_callback_query(filters.regex(r"^(q|l)#"))
async def filter_menu_handler(client: Client, callback_query: CallbackQuery):
    type, query, current_filter, page = callback_query.data.split("#")

    buttons = []
    if type == "q":
        qualities = ["480p", "720p", "1080p"]
        for q in qualities:
            buttons.append([InlineKeyboardButton(q, callback_data=pack_callback_data("p", query, q, 0))])
    else:
        languages = ["Telugu", "Tamil", "Hindi", "English", "Multi"]
        for l in languages:
            buttons.append([InlineKeyboardButton(l, callback_data=pack_callback_data("p", query, l, 0))])

    buttons.append([InlineKeyboardButton("🔙 Back to Results", callback_data=pack_callback_data("p", query, current_filter if current_filter != "None" else None, page))])

    await callback_query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Pagination and Filter Callback Logic
@bot.on_callback_query(filters.regex(r"^p#"))
async def pagination_handler(client: Client, callback_query: CallbackQuery):
    _, query, filter_text, page = callback_query.data.split("#")
    page = int(page)
    if filter_text == "None":
        filter_text = None

    skip = page * MAX_RESULTS
    results, total_results = await search_files(query, filter_text=filter_text, skip=skip, limit=MAX_RESULTS)

    if not results and page > 0:
        await callback_query.answer("No more results", show_alert=True)
        return

    query_display = f"{query} {filter_text}" if filter_text else query
    text = f"🔍 Found {total_results} results for: \"{query_display}\"\n\nPage {page + 1}\n\nClick on a file to get it:"

    markup = get_ui_markup(query, filter_text, page, total_results, results)

    await callback_query.message.edit_text(
        text,
        reply_markup=markup
    )

# File Callback handler
@bot.on_callback_query(filters.regex(r"^f#"))
async def file_callback_handler(client: Client, callback_query: CallbackQuery):
    db_id = callback_query.data.split("#")[1]
    file_info = await get_file_by_db_id(db_id)

    if not file_info:
        await callback_query.answer("File not available", show_alert=True)
        return

    file_id = file_info['file_id']
    # Original caption or fallback to file_name
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
        # Indexing must complete before users can search
        await index_channel_history(bot)

        try:
            await bot.send_message(OWNER_ID, "bot started successfully ✅")
        except Exception:
            pass

        print("Initial channel indexing complete. Bot is now active for users.")
        await idle()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
