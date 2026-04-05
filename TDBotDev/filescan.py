import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import MAX_RESULTS
from database import search_files_fuzzy, get_file_by_db_id

# Helper to truncate query for callback data (64 byte limit)
def pack_cb(p, q, qu, l, pg):
    data = f"{p}#{q}#{qu}#{l}#{pg}"
    if len(data) > 64:
        limit = 64 - (len(p) + 1 + len(str(qu)) + 1 + len(str(l)) + 1 + len(str(pg)) + 1)
        data = f"{p}#{q[:limit]}#{qu}#{l}#{pg}"
    return data

def get_ui(q, qu, l, pg, total, results):
    buttons = []
    # TOP BUTTONS
    buttons.append([
        InlineKeyboardButton("Quality ⚡", callback_data=f"menu#q#{q}#{qu}#{l}#{pg}"),
        InlineKeyboardButton("Language 🎵", callback_data=f"menu#l#{q}#{qu}#{l}#{pg}")
    ])
    for f in results:
        db_id = str(f['_id'])
        buttons.append([InlineKeyboardButton(f['file_name'], callback_data=f"f#{db_id}")])
    nav = []
    if pg > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=pack_cb("p", q, qu, l, pg - 1)))
    if (pg + 1) * MAX_RESULTS < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=pack_cb("p", q, qu, l, pg + 1)))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

# Exclude all bot commands from search handler to prevent interception
@Client.on_message(filters.text & filters.private & ~filters.command(["start", "reset", "scan_channel", "list_index"]))
async def initial_search_handler(client: Client, message: Message):
    if getattr(client, "is_indexing", False):
        await message.reply_text("**⏳ Please wait, indexing is in progress...**")
        return

    query = message.text
    status = await message.reply_text(f"**🔍 Searching for \"{query}\"... Please wait**")
    results, total = await search_files_fuzzy(query, limit=MAX_RESULTS)

    if not results:
        await status.edit_text(f"**No files found 😔**")
        return

    text = f"**🔍 Found {total} results for: \"{query}\"**\n\n**Page 1**\n\n**Click on a file to get it:**"
    await status.edit_text(text, reply_markup=get_ui(query, "None", "None", 0, total, results))

@Client.on_callback_query(filters.regex(r"^menu#"))
async def filter_menu_handler(client, cb: CallbackQuery):
    _, m_type, q, qu, l, pg = cb.data.split("#")
    buttons = []
    if m_type == "q":
        for opt in ["480p", "720p", "1080p"]:
            # Corrected arguments for pack_cb (p, q, qu, l, pg)
            buttons.append([InlineKeyboardButton(opt, callback_data=pack_cb("p", q, opt, l, 0))])
    else:
        langs = ["Telugu", "Tamil", "Hindi", "English", "Malayalam", "Kannada", "Japanese"]
        for opt in langs:
            # Corrected arguments for pack_cb (p, q, qu, l, pg)
            buttons.append([InlineKeyboardButton(opt, callback_data=pack_cb("p", q, qu, opt, 0))])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=pack_cb("p", q, qu, l, pg))])
    await cb.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^p#"))
async def pagination_handler(client, cb: CallbackQuery):
    _, q, qu, l, pg = cb.data.split("#")
    pg = int(pg)
    results, total = await search_files_fuzzy(q, quality=qu, language=l, skip=pg*MAX_RESULTS, limit=MAX_RESULTS)
    if not results:
        err_val = l if l != 'None' else qu
        await cb.message.edit_text(f"**❌ No {err_val} files found**")
        return
    query_disp = f"{q} {qu if qu != 'None' else ''} {l if l != 'None' else ''}".strip()
    text = f"**🔍 Found {total} results for: \"{query_disp}\"**\n\n**Page {pg+1}**\n\n**Click on a file to get it:**"
    await cb.message.edit_text(text, reply_markup=get_ui(q, qu, l, pg, total, results))
