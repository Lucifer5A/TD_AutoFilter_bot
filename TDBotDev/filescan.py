import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import MAX_RESULTS
from database import search_files_advanced, get_file_by_db_id

# Helper to truncate query for callback data (64 byte limit)
def pack_cb(p, q, qu, l, pg):
    # p#query#quality#language#page
    data = f"{p}#{q}#{qu}#{l}#{pg}"
    if len(data) > 64:
        # Max lengths: p(1) + qu(6) + l(10) + pg(2) + symbols(4) = 23. 64-23 = 41 for q
        q_limit = 64 - (len(p) + 1 + len(qu) + 1 + len(l) + 1 + len(str(pg)) + 1)
        data = f"{p}#{q[:q_limit]}#{qu}#{l}#{pg}"
    return data

def get_buttons(q, qu, l, pg, total, results):
    buttons = []
    # TOP BUTTONS: [ Quality ⚡ ] [ Language 🎵 ]
    buttons.append([
        InlineKeyboardButton("Quality ⚡", callback_data=pack_cb("mq", q, qu, l, pg)),
        InlineKeyboardButton("Language 🎵", callback_data=pack_cb("ml", q, qu, l, pg))
    ])

    # FILE LIST
    for f in results:
        db_id = str(f['_id'])
        buttons.append([InlineKeyboardButton(f"📁 {f['file_name']}", callback_data=f"f#{db_id}")])

    # BOTTOM: Prev | Next
    nav = []
    if pg > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=pack_cb("p", q, qu, l, pg - 1)))
    if (pg + 1) * MAX_RESULTS < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=pack_cb("p", q, qu, l, pg + 1)))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "reset"]))
async def auto_search_handler(client, message):
    query = message.text
    # Bold text as requested
    status = await message.reply_text(f"**🔍 Searching for \"{query}\"... Please wait**")

    results, total = await search_files_advanced(query, limit=MAX_RESULTS)

    if not results:
        await status.edit_text(f"**No files found 😔**")
        return

    text = f"**🔍 Found {total} results for: \"{query}\"**\n\n**Page 1**\n\n**Click on a file to get it:**"
    await status.edit_text(text, reply_markup=get_buttons(query, "None", "None", 0, total, results))

@Client.on_callback_query(filters.regex(r"^(mq|ml)#"))
async def filter_menu_handler(client, cb: CallbackQuery):
    t, q, qu, l, pg = cb.data.split("#")

    buttons = []
    if t == "mq":
        # Quality sub-buttons
        for opt in ["480p", "720p", "1080p"]:
            buttons.append([InlineKeyboardButton(opt, callback_data=pack_cb("p", q, opt, l, 0))])
    else:
        # Language sub-buttons
        for opt in ["Telugu", "Tamil", "Hindi", "English", "Multi"]:
            buttons.append([InlineKeyboardButton(opt, callback_data=pack_cb("p", q, qu, opt, 0))])

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=pack_cb("p", q, qu, l, pg))])
    await cb.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^p#"))
async def pagination_handler(client, cb: CallbackQuery):
    _, q, qu, l, pg = cb.data.split("#")
    pg = int(pg)

    results, total = await search_files_advanced(q, quality=qu, language=l, skip=pg*MAX_RESULTS, limit=MAX_RESULTS)

    if not results:
        # Error handling: If no files found after filtering
        err_type = "quality" if qu != "None" else "language"
        err_val = qu if qu != "None" else l
        await cb.message.edit_text(f"**❌ No {err_val} {err_type} files found in database**")
        return

    query_disp = f"{q} {qu if qu != 'None' else ''} {l if l != 'None' else ''}".strip()
    text = f"**🔍 Found {total} results for: \"{query_disp}\"**\n\n**Page {pg+1}**\n\n**Click on a file to get it:**"

    await cb.message.edit_text(text, reply_markup=get_buttons(q, qu, l, pg, total, results))
