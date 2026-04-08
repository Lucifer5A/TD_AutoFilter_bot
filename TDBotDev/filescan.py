import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import MAX_RESULTS
from Database.database import search_files_fuzzy, save_nav_state, get_nav_state, clean_ui_name
from utils import safe_edit, safe_reply, style_text, style_btn
from TDBotDev.forcesub import force_sub

# Helper for stateful search callbacks
async def pack_search(q, qu, l, pg):
    state = {"q": q, "qu": qu, "l": l, "pg": pg}
    key = await save_nav_state(state)
    return f"spage#{key}"

async def pack_menu(m_type, q, qu, l, pg):
    state = {"t": m_type, "q": q, "qu": qu, "l": l, "pg": pg}
    key = await save_nav_state(state)
    return f"smenu#{key}"

async def pack_all(q, qu, l, pg):
    state = {"q": q, "qu": qu, "l": l, "pg": pg}
    key = await save_nav_state(state)
    return f"sall#{key}"

async def get_ui(q, qu, l, pg, total, results):
    buttons = []
    # Row 1: Language (Centered)
    buttons.append([
        InlineKeyboardButton(style_btn("🎵 Language 🎵"), callback_data=await pack_menu("l", q, qu, l, pg))
    ])
    # Row 2: Quality, All
    buttons.append([
        InlineKeyboardButton(style_btn("✨ Quality ✨"), callback_data=await pack_menu("q", q, qu, l, pg)),
        InlineKeyboardButton(style_btn("🔎 All"), callback_data=await pack_all(q, qu, l, pg))
    ])

    for f in results:
        db_id = str(f['_id'])
        ui_name = clean_ui_name(f['file_name'])
        buttons.append([InlineKeyboardButton(style_btn(ui_name), callback_data=f"f#{db_id}")])

    total_pages = (total + MAX_RESULTS - 1) // MAX_RESULTS
    current_page = pg + 1

    nav = []
    # Left button logic
    if pg > 0:
        nav.append(InlineKeyboardButton(style_btn("🔙 BACK"), callback_data=await pack_search(q, qu, l, pg - 1)))
    else:
        nav.append(InlineKeyboardButton(style_btn("📚 PAGE"), callback_data="pages_info"))

    # Center info
    nav.append(InlineKeyboardButton(style_btn(f"{current_page} / {total_pages}"), callback_data="pages_info"))

    # Right button logic
    if (pg + 1) * MAX_RESULTS < total:
        nav.append(InlineKeyboardButton(style_btn("NEXT 🔜"), callback_data=await pack_search(q, qu, l, pg + 1)))
    else:
        nav.append(InlineKeyboardButton(style_btn("PAGE 📚"), callback_data="pages_info"))

    buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

# Exclude commands from search handler
@Client.on_message(filters.text & filters.private & ~filters.command(["start", "reset"]))
async def initial_search_handler(client: Client, message: Message):
    # Mandatory ForceSub Check for ALL activities
    if not await force_sub(client, message):
        return

    if getattr(client, "is_indexing", False):
        await safe_reply(message, style_text("⏳ Please wait, indexing is in progress..."))
        return
    query = message.text
    status = await safe_reply(message, style_text(f"🔍 Searching for \"{query}\"... Please wait"))
    if not status: return

    results, total = await search_files_fuzzy(query, limit=MAX_RESULTS)
    if not results:
        await safe_edit(status, style_text("No files found 😔"))
        return
    text = style_text(f"🔍 Found {total} results for: \"{query}\"\n\nPage 1\n\nClick on a file to get it:")
    markup = await get_ui(query, "None", "None", 0, total, results)
    await safe_edit(status, text, reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^smenu#"))
async def search_filter_menu_handler(client, cb: CallbackQuery):
    await cb.answer()

    # Force Subscribe Check
    if not await force_sub(client, cb.message, user_id=cb.from_user.id):
        return

    key = cb.data.split("#")[1]
    state = await get_nav_state(key)
    if not state:
        await cb.answer("Session expired", show_alert=True)
        return
    m_type, q, qu, l, pg = state["t"], state["q"], state["qu"], state["l"], state["pg"]
    buttons = []
    if m_type == "q":
        for opt in ["480p", "720p", "1080p", "4K"]:
            buttons.append([InlineKeyboardButton(style_btn(opt), callback_data=await pack_search(q, opt, l, 0))])
    else:
        langs = ["Telugu", "Tamil", "Hindi", "English", "Multiple"]
        for opt in langs:
            buttons.append([InlineKeyboardButton(style_btn(opt), callback_data=await pack_search(q, qu, opt, 0))])
    back_cb = await pack_search(q, qu, l, pg)
    buttons.append([InlineKeyboardButton(style_btn("🔙 Back"), callback_data=back_cb)])
    await cb.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^spage#"))
async def search_pagination_handler(client, cb: CallbackQuery):
    await cb.answer()

    # Force Subscribe Check
    if not await force_sub(client, cb.message, user_id=cb.from_user.id):
        return

    key = cb.data.split("#")[1]
    state = await get_nav_state(key)
    if not state:
        await cb.answer("Session expired", show_alert=True)
        return
    q, qu, l, pg = state["q"], state["qu"], state["l"], state["pg"]
    results, total = await search_files_fuzzy(q, quality=qu, language=l, skip=pg*MAX_RESULTS, limit=MAX_RESULTS)
    if not results:
        await safe_edit(cb.message, style_text("❌ No matching files found"))
        return
    query_disp = f"{q} {qu if qu != 'None' else ''} {l if l != 'None' else ''}".strip()
    text = style_text(f"🔍 Found {total} results for: \"{query_disp}\"\n\nPage {pg+1}\n\nClick on a file to get it:")
    markup = await get_ui(q, qu, l, pg, total, results)
    await safe_edit(cb.message, text, reply_markup=markup)
