import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import MAX_RESULTS
from database import search_files_fuzzy, save_nav_state, get_nav_state, clean_ui_name
from utils import safe_edit, safe_reply

# Helper for stateful search callbacks
async def pack_search(q, qu, l, pg):
    state = {"q": q, "qu": qu, "l": l, "pg": pg}
    key = await save_nav_state(state)
    return f"spage#{key}"

async def pack_menu(m_type, q, qu, l, pg):
    state = {"t": m_type, "q": q, "qu": qu, "l": l, "pg": pg}
    key = await save_nav_state(state)
    return f"smenu#{key}"

async def get_ui(q, qu, l, pg, total, results):
    buttons = []
    # TOP BUTTONS
    buttons.append([
        InlineKeyboardButton("Quality ⚡", callback_data=await pack_menu("q", q, qu, l, pg)),
        InlineKeyboardButton("Language 🎵", callback_data=await pack_menu("l", q, qu, l, pg))
    ])
    for f in results:
        db_id = str(f['_id'])
        ui_name = clean_ui_name(f['file_name'])
        buttons.append([InlineKeyboardButton(ui_name, callback_data=f"f#{db_id}")])
    nav = []
    if pg > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=await pack_search(q, qu, l, pg - 1)))
    if (pg + 1) * MAX_RESULTS < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=await pack_search(q, qu, l, pg + 1)))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "reset", "list_index"]))
async def initial_search_handler(client: Client, message: Message):
    if getattr(client, "is_indexing", False):
        await safe_reply(message, "**⏳ Please wait, indexing is in progress...**")
        return
    query = message.text
    status = await safe_reply(message, f"**🔍 Searching for \"{query}\"... Please wait**")
    if not status: return

    results, total = await search_files_fuzzy(query, limit=MAX_RESULTS)
    if not results:
        await safe_edit(status, f"**No files found 😔**")
        return
    text = f"**🔍 Found {total} results for: \"{query}\"**\n\n**Page 1**\n\n**Click on a file to get it:**"
    markup = await get_ui(query, "None", "None", 0, total, results)
    await safe_edit(status, text, reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^smenu#"))
async def search_filter_menu_handler(client, cb: CallbackQuery):
    key = cb.data.split("#")[1]
    state = await get_nav_state(key)
    if not state:
        await cb.answer("Session expired", show_alert=True)
        return
    m_type, q, qu, l, pg = state["t"], state["q"], state["qu"], state["l"], state["pg"]
    buttons = []
    if m_type == "q":
        for opt in ["480p", "720p", "1080p", "4K"]:
            buttons.append([InlineKeyboardButton(opt, callback_data=await pack_search(q, opt, l, 0))])
    else:
        langs = ["Telugu", "Tamil", "Hindi", "English", "Multiple"]
        for opt in langs:
            buttons.append([InlineKeyboardButton(opt, callback_data=await pack_search(q, qu, opt, 0))])
    back_cb = await pack_search(q, qu, l, pg)
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data=back_cb)])
    await cb.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^spage#"))
async def search_pagination_handler(client, cb: CallbackQuery):
    key = cb.data.split("#")[1]
    state = await get_nav_state(key)
    if not state:
        await cb.answer("Session expired", show_alert=True)
        return
    q, qu, l, pg = state["q"], state["qu"], state["l"], state["pg"]
    results, total = await search_files_fuzzy(q, quality=qu, language=l, skip=pg*MAX_RESULTS, limit=MAX_RESULTS)
    if not results:
        await safe_edit(cb.message, f"**❌ No matching files found**")
        return
    query_disp = f"{q} {qu if qu != 'None' else ''} {l if l != 'None' else ''}".strip()
    text = f"**🔍 Found {total} results for: \"{query_disp}\"**\n\n**Page {pg+1}**\n\n**Click on a file to get it:**"
    markup = await get_ui(q, qu, l, pg, total, results)
    await safe_edit(cb.message, text, reply_markup=markup)
