from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_unique_series, get_seasons, get_episodes

# Helper to pack callback data (stay under 64 bytes)
def pack_list_cb(prefix, series, extra=None):
    # s#series | ss#series#num
    data = f"{prefix}#{series}"
    if extra:
        data += f"#{extra}"
    if len(data) > 64:
        limit = 64 - (len(prefix) + 2 + len(str(extra or "")))
        data = f"{prefix}#{series[:limit]}#{extra}" if extra else f"{prefix}#{series[:limit]}"
    return data

@Client.on_message(filters.command("list_index") & filters.private)
async def list_index_handler(client, message):
    # Parse Mode 2: /list_index - Naruto
    if "-" in message.text:
        try:
            series_name = message.text.split("-", 1)[1].strip()
            if series_name:
                seasons = await get_seasons(series_name)
                if not seasons:
                    await message.reply_text("**❌ Series not found**")
                    return

                # Directly go to Season View
                buttons = []
                for s in seasons:
                    buttons.append([InlineKeyboardButton(f"Season {s}", callback_data=pack_list_cb("ss", series_name, s))])

                await message.reply_text(
                    f"**📺 {series_name}**\n\n**Select a Season:**",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                return
        except Exception:
            pass

    # Default Mode 1: /list_index
    status = await message.reply_text("**Fetching all series... Please wait**")
    series_list = await get_unique_series()

    if not series_list:
        await status.edit_text("**No content available**")
        return

    buttons = []
    # Remove duplicates and sort handled in DB function
    for s in series_list:
        buttons.append([InlineKeyboardButton(s, callback_data=pack_list_cb("s", s))])

    await status.edit_text(
        "**📺 All Available Series**\n\n**Select a series to view seasons:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^s#"))
async def series_callback_handler(client, cb: CallbackQuery):
    _, series_name = cb.data.split("#")
    seasons = await get_seasons(series_name)

    if not seasons:
        await cb.answer("No seasons found", show_alert=True)
        return

    buttons = []
    for s in seasons:
        buttons.append([InlineKeyboardButton(f"Season {s}", callback_data=pack_list_cb("ss", series_name, s))])

    buttons.append([InlineKeyboardButton("🔙 Back to All Series", callback_data="list_all")])

    await cb.message.edit_text(
        f"**📺 {series_name}**\n\n**Select a Season:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^ss#"))
async def season_callback_handler(client, cb: CallbackQuery):
    _, series_name, s_num = cb.data.split("#")
    episodes = await get_episodes(series_name, int(s_num))

    if not episodes:
        await cb.answer("No episodes found", show_alert=True)
        return

    buttons = []
    # Show episode buttons (normalized names)
    for e in episodes:
        # Normalize: Episode 01
        btn_text = f"Episode {e['e_num']:02}"
        # Use existing f# prefix for file delivery
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"f#{e['id']}")])

    buttons.append([InlineKeyboardButton("🔙 Back to Seasons", callback_data=pack_list_cb("s", series_name))])

    await cb.message.edit_text(
        f"**📺 {series_name} - Season {s_num}**\n\n**Select an Episode:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^list_all$"))
async def list_all_callback(client, cb: CallbackQuery):
    series_list = await get_unique_series()
    if not series_list:
        await cb.message.edit_text("**No content available**")
        return
    buttons = [[InlineKeyboardButton(s, callback_data=pack_list_cb("s", s))] for s in series_list]
    await cb.message.edit_text(
        "**📺 All Available Series**\n\n**Select a series to view seasons:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
