import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import (
    get_unique_series,
    get_series_files,
    get_file_by_db_id,
    save_nav_state,
    get_nav_state,
    detect_lang,
    detect_qual,
    clean_ui_name,
    SEASON_REGEX,
    EPISODE_REGEX
)
from utils import safe_edit, safe_reply

# Helper for stateful callbacks
async def pack_nav(p, s, l="None", q="None", sn="None"):
    state = {"p": p, "s": s, "l": l, "q": q, "sn": sn}
    key = await save_nav_state(state)
    return f"nav#{key}"

@Client.on_message(filters.command("list_index") & filters.private)
async def list_index_handler(client, message):
    args = message.text.split("-", 1)
    if len(args) > 1:
        series_name = args[1].strip()
        files = await get_series_files(series_name)
        if not files:
            await safe_reply(message, "**❌ Series not found**")
            return
        await start_nav_flow(client, message, series_name, files)
        return

    series_list = await get_unique_series()
    if not series_list:
        await safe_reply(message, "**No content available**")
        return

    buttons = []
    for s in series_list:
        cb_data = await pack_nav("s", s)
        buttons.append([InlineKeyboardButton(s, callback_data=cb_data)])

    await safe_reply(message, "**📺 All Available Series**", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^nav#"))
async def nav_callback_handler(client, cb: CallbackQuery):
    key = cb.data.split("#")[1]
    state = await get_nav_state(key)
    if not state:
        await cb.answer("Session expired. Please search again.", show_alert=True)
        return

    p, s, l, q, sn = state["p"], state["s"], state["l"], state["q"], state["sn"]
    files = await get_series_files(s)

    if p == "s":
        await start_nav_flow(client, cb.message, s, files, is_cb=True)
    elif p == "l":
        await language_flow(client, cb.message, s, l, files, is_cb=True)
    elif p == "q":
        if l != "None": files = [f for f in files if detect_lang(f['file_name']) == l]
        await quality_flow(client, cb.message, s, l, q, files, is_cb=True)
    elif p == "sn":
        if l != "None": files = [f for f in files if detect_lang(f['file_name']) == l]
        if q != "None": files = [f for f in files if detect_qual(f['file_name']) == q]
        await season_flow(client, cb.message, s, l, q, int(sn), files, is_cb=True)

async def start_nav_flow(client, message, series, files, is_cb=False):
    langs = sorted(list(set(filter(None, [detect_lang(f['file_name']) for f in files]))))
    if len(langs) > 1:
        buttons = []
        for lang in langs:
            cb = await pack_nav("l", series, lang)
            buttons.append([InlineKeyboardButton(lang, callback_data=cb)])
        text = f"**📺 {series.title()}**\n\n**Select Language:**"
        if is_cb: await safe_edit(message, text, reply_markup=InlineKeyboardMarkup(buttons))
        else: await safe_reply(message, text, reply_markup=InlineKeyboardMarkup(buttons))
        return
    lang = langs[0] if langs else "None"
    await language_flow(client, message, series, lang, files, is_cb)

async def language_flow(client, message, series, lang, files, is_cb):
    if lang != "None":
        files = [f for f in files if detect_lang(f['file_name']) == lang]
    quals = sorted(list(set(filter(None, [detect_qual(f['file_name']) for f in files]))))
    if len(quals) > 1:
        buttons = []
        for qual in quals:
            cb = await pack_nav("q", series, lang, qual)
            buttons.append([InlineKeyboardButton(qual, callback_data=cb)])
        text = f"**📺 {series.title()} [{lang if lang != 'None' else ''}]**\n\n**Select Quality:**"
        if is_cb: await safe_edit(message, text, reply_markup=InlineKeyboardMarkup(buttons))
        else: await safe_reply(message, text, reply_markup=InlineKeyboardMarkup(buttons))
        return
    qual = quals[0] if quals else "None"
    await quality_flow(client, message, series, lang, qual, files, is_cb)

async def quality_flow(client, message, series, lang, qual, files, is_cb):
    if qual != "None":
        files = [f for f in files if detect_qual(f['file_name']) == qual]
    seasons = set()
    for f in files:
        match = SEASON_REGEX.search(f['file_name'])
        if match: seasons.add(int(match.group(2)))
        else: seasons.add(1)
    sorted_seasons = sorted(list(seasons))
    if len(sorted_seasons) > 1:
        buttons = []
        for s_num in sorted_seasons:
            cb = await pack_nav("sn", series, lang, qual, s_num)
            buttons.append([InlineKeyboardButton(f"Season {s_num}", callback_data=cb)])
        text = f"**📺 {series.title()} [{lang if lang != 'None' else ''}] [{qual if qual != 'None' else ''}]**\n\n**Select Season:**"
        if is_cb: await safe_edit(message, text, reply_markup=InlineKeyboardMarkup(buttons))
        else: await safe_reply(message, text, reply_markup=InlineKeyboardMarkup(buttons))
        return
    await season_flow(client, message, series, lang, qual, sorted_seasons[0] if sorted_seasons else 1, files, is_cb)

async def season_flow(client, message, series, lang, qual, season, files, is_cb):
    final_files = []
    for f in files:
        match = SEASON_REGEX.search(f['file_name'])
        cur_s = int(match.group(2)) if match else 1
        if cur_s == season: final_files.append(f)
    episodes = []
    for f in final_files:
        match = EPISODE_REGEX.search(f['file_name'])
        e_num = int(match.group(2)) if match else 1
        episodes.append({"id": str(f["_id"]), "ui_name": clean_ui_name(f['file_name']), "e_num": e_num})
    if not episodes:
        if is_cb: await safe_edit(message, "**No episodes found**")
        else: await safe_reply(message, "**No episodes found**")
        return
    episodes.sort(key=lambda x: x["e_num"])
    buttons = [[InlineKeyboardButton(ep["ui_name"], callback_data=f"f#{ep['id']}")] for ep in episodes]
    text = f"**📺 {series.title()} [{lang if lang != 'None' else ''}] [{qual if qual != 'None' else ''}] - Season {season}**\n\n**Select Episode:**"
    if is_cb: await safe_edit(message, text, reply_markup=InlineKeyboardMarkup(buttons))
    else: await safe_reply(message, text, reply_markup=InlineKeyboardMarkup(buttons))
