from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_unique_series, get_seasons, get_episodes

# Helper to pack callback data (stay under 64 bytes)
def pack_list_cb(prefix, series, extra=None):
    data = f"{prefix}#{series}"
    if extra:
        data += f"#{extra}"
    if len(data) > 64:
        limit = 64 - (len(prefix) + 2 + len(str(extra or "")))
        data = f"{prefix}#{series[:limit]}#{extra}" if extra else f"{prefix}#{series[:limit]}"
    return data

@Client.on_message(filters.command("list_channel") & filters.private)
async def list_channel_handler(client, message):
    if len(message.command) > 1:
        # MODE 2: /list_channel <series_name>
        series_name = " ".join(message.command[1:])
        seasons = await get_seasons(series_name)

        if not seasons:
            await message.reply_text(f"**No seasons found for \"{series_name}\"**")
            return

        buttons = []
        for s in seasons:
            buttons.append([InlineKeyboardButton(f"Season {s}", callback_data=pack_list_cb("ss", series_name, s))])

        await message.reply_text(
            f"**📺 {series_name}**\n\n**Select a Season:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # MODE 1: /list_channel
        status = await message.reply_text("**Fetching all series... Please wait**")
        series_list = await get_unique_series()

        if not series_list:
            await status.edit_text("**No series found in database**")
            return

        buttons = []
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
    for e in episodes:
        btn_text = f"Episode E{e['e_num']:02}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"f#{e['id']}")])

    buttons.append([InlineKeyboardButton("🔙 Back to Seasons", callback_data=pack_list_cb("s", series_name))])

    await cb.message.edit_text(
        f"**📺 {series_name} - Season {s_num}**\n\n**Select an Episode:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^list_all$"))
async def list_all_callback(client, cb: CallbackQuery):
    series_list = await get_unique_series()
    buttons = [[InlineKeyboardButton(s, callback_data=pack_list_cb("s", s))] for s in series_list]
    await cb.message.edit_text(
        "**📺 All Available Series**\n\n**Select a series to view seasons:**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
