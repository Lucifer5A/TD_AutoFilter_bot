from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from Database.database import collection, db, search_files_fuzzy, save_nav_state, get_nav_state, clean_ui_name, delete_files_by_ids, delete_files_by_regex
from config import OWNER_ID, ADMIN_IDS, MAX_RESULTS
from utils import safe_reply, safe_edit, style_text, style_btn
from TDBotDev.forcesub import force_sub
from bson.objectid import ObjectId

# State Packing for Deletion
async def pack_delete(q, pg, selected, action=None):
    # selected is a list of file_ids (strings)
    state = {"q": q, "pg": pg, "sel": selected, "act": action}
    key = await save_nav_state(state)
    return key

async def get_delete_ui(q, pg, total, results, selected_ids):
    buttons = []

    # Pack state ONCE for the entire UI
    state_key = await pack_delete(q, pg, selected_ids)

    for f in results:
        file_id = f['file_id']
        db_id = str(f['_id'])
        ui_name = clean_ui_name(f['file_name'])

        prefix = "✅ " if file_id in selected_ids else ""
        btn_text = style_btn(f"{prefix}{ui_name}")

        # d_toggle#<db_id>#<key>
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"dt#{db_id}#{state_key}")])

    # Deletion Controls
    buttons.append([
        InlineKeyboardButton(style_btn("🗑️ Delete"), callback_data=f"dc#sel#{state_key}"),
        InlineKeyboardButton(style_btn("🗑️ Delete All"), callback_data=f"dc#all#{state_key}")
    ])

    # Pagination
    total_pages = (total + MAX_RESULTS - 1) // MAX_RESULTS
    current_page = pg + 1

    nav = []
    if pg > 0:
        nav.append(InlineKeyboardButton(style_btn("🔙 BACK"), callback_data=f"dp#{pg-1}#{state_key}"))
    else:
        nav.append(InlineKeyboardButton(style_btn("📚 PAGE"), callback_data="pages_info"))

    nav.append(InlineKeyboardButton(style_btn(f"{current_page} / {total_pages}"), callback_data="pages_info"))

    if (pg + 1) * MAX_RESULTS < total:
        nav.append(InlineKeyboardButton(style_btn("NEXT 🔜"), callback_data=f"dp#{pg+1}#{state_key}"))
    else:
        nav.append(InlineKeyboardButton(style_btn("PAGE 📚"), callback_data="pages_info"))

    buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("delete_file") & filters.private)
async def delete_file_command_handler(client, message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await safe_reply(message, style_text("❌ You are not authorized to use this command"))
        return

    if len(message.command) < 2:
        await safe_reply(message, style_text("❌ Usage: /delete_file <query>"))
        return

    query = message.text.split(None, 1)[1]
    status = await safe_reply(message, style_text(f"🔍 Searching for \"{query}\" to delete..."))

    results, total = await search_files_fuzzy(query, limit=MAX_RESULTS)
    if not results:
        await safe_edit(status, style_text("No files found 😔"))
        return

    text = style_text(f"🗑️ ADMIN DELETE MODE\n\nQuery: \"{query}\"\nResults: {total}\n\nSelect files to delete:")
    markup = await get_delete_ui(query, 0, total, results, [])
    await safe_edit(status, text, reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^dt#"))
async def delete_toggle_handler(client, cb: CallbackQuery):
    await cb.answer()
    parts = cb.data.split("#")
    if len(parts) != 3: return
    _, db_id, key = parts

    state = await get_nav_state(key)
    if not state: return

    q, pg, selected = state["q"], state["pg"], state["sel"]

    # Efficient fetch: only file_id needed
    file_info = await collection.find_one({"_id": ObjectId(db_id)}, {"file_id": 1})
    if not file_info: return

    file_id = file_info['file_id']
    if file_id in selected:
        selected.remove(file_id)
    else:
        selected.append(file_id)

    results, total = await search_files_fuzzy(q, skip=pg*MAX_RESULTS, limit=MAX_RESULTS)
    markup = await get_delete_ui(q, pg, total, results, selected)
    await cb.message.edit_reply_markup(reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^dp#"))
async def delete_pagination_handler(client, cb: CallbackQuery):
    await cb.answer()
    parts = cb.data.split("#")
    if len(parts) != 3: return
    _, new_pg, key = parts
    new_pg = int(new_pg)

    state = await get_nav_state(key)
    if not state: return

    q, selected = state["q"], state["sel"]
    results, total = await search_files_fuzzy(q, skip=new_pg*MAX_RESULTS, limit=MAX_RESULTS)

    text = style_text(f"🗑️ ADMIN DELETE MODE\n\nQuery: \"{q}\"\nResults: {total}\n\nSelect files to delete:")
    markup = await get_delete_ui(q, new_pg, total, results, selected)
    await safe_edit(cb.message, text, reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^dc#"))
async def delete_confirm_handler(client, cb: CallbackQuery):
    await cb.answer()
    parts = cb.data.split("#")
    if len(parts) != 3: return
    _, action, key = parts

    state = await get_nav_state(key)
    if not state: return

    q, pg, selected = state["q"], state["pg"], state["sel"]

    if action == "sel" and not selected:
        await cb.answer("No files selected!", show_alert=True)
        return

    confirm_text = style_text(
        "⚠️ **CONFIRM DELETION**\n\n"
        f"Action: {'Delete Selected' if action == 'sel' else 'Delete All Results'}\n"
        f"Selected: {len(selected) if action == 'sel' else 'All matching ' + q}\n\n"
        "This action cannot be undone. Are you sure?"
    )

    new_state_key = await pack_delete(q, pg, selected, action=action)
    buttons = [
        [
            InlineKeyboardButton(style_btn("Yes ✅"), callback_data=f"dy#{new_state_key}"),
            InlineKeyboardButton(style_btn("No ✖️"), callback_data=f"dn#{new_state_key}")
        ],
        [InlineKeyboardButton(style_btn("BACK 🔙"), callback_data=f"dn#{new_state_key}")]
    ]
    await safe_edit(cb.message, confirm_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^dy#"))
async def delete_execution_handler(client, cb: CallbackQuery):
    await cb.answer("Deleting...", show_alert=False)
    parts = cb.data.split("#")
    if len(parts) != 2: return
    key = parts[1]

    state = await get_nav_state(key)
    if not state: return

    q, selected, action = state["q"], state["sel"], state["act"]

    deleted_count = 0
    if action == "sel":
        deleted_count = await delete_files_by_ids(selected)
    elif action == "all":
        deleted_count = await delete_files_by_regex(q)

    await safe_edit(cb.message, style_text(f"✅ Successfully deleted {deleted_count} files."))

@Client.on_callback_query(filters.regex(r"^dn#"))
async def delete_cancel_handler(client, cb: CallbackQuery):
    await cb.answer()
    parts = cb.data.split("#")
    if len(parts) != 2: return
    key = parts[1]

    state = await get_nav_state(key)
    if not state: return

    q, pg, selected = state["q"], state["pg"], state["sel"]
    results, total = await search_files_fuzzy(q, skip=pg*MAX_RESULTS, limit=MAX_RESULTS)

    text = style_text(f"🗑️ ADMIN DELETE MODE\n\nQuery: \"{q}\"\nResults: {total}\n\nSelect files to delete:")
    markup = await get_delete_ui(q, pg, total, results, selected)
    await safe_edit(cb.message, text, reply_markup=markup)

@Client.on_message(filters.command("reset") & filters.private)
async def reset_handler(client, message):
    if not await force_sub(client, message):
        return

    if message.from_user.id != OWNER_ID:
        await safe_reply(message, style_text("❌ You are not authorized to use this command"))
        return

    try:
        await collection.delete_many({})
        await db["scan_state"].delete_many({})
        await db["nav_cache"].delete_many({})
        await safe_reply(message, style_text("✅ Database and cache have been reset successfully"))
    except Exception as e:
        await safe_reply(message, style_text(f"❌ Error resetting database: {str(e)}"))
