import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_unique_series, get_series_files, get_file_by_db_id, SEASON_REGEX, EPISODE_REGEX, LANG_MAP, QUAL_MAP

# Helper to pack callback data
def pack(p, s, l="None", q="None", sn="None"):
    # p#series#lang#qual#season
    data = f"{p}#{s}#{l}#{q}#{sn}"
    if len(data) > 64:
        # Extreme cases: truncate series name
        limit = 64 - (len(p) + 4 + len(l) + len(q) + len(str(sn)))
        data = f"{p}#{s[:limit]}#{l}#{q}#{sn}"
    return data

def detect_lang(name):
    name = name.lower()
    for lang, tags in LANG_MAP.items():
        if any(tag in name for tag in tags):
            return lang.title()
    return "Multiple"

def detect_qual(name):
    name = name.lower()
    for qual, tags in QUAL_MAP.items():
        if any(tag in name for tag in tags):
            return qual
    return "720p"

@Client.on_message(filters.command("list_index") & filters.private)
async def list_index_handler(client, message):
    args = message.text.split("-", 1)
    if len(args) > 1:
        # MODE 2: /list_index - Naruto
        series_name = args[1].strip()
        files = await get_series_files(series_name)
        if not files:
            await message.reply_text("**❌ Series not found**")
            return
        await start_nav_flow(client, message, series_name, files)
        return

    # MODE 1: /list_index
    series_list = await get_unique_series()
    if not series_list:
        await message.reply_text("**No content available**")
        return

    buttons = [[InlineKeyboardButton(s, callback_data=pack("s", s))] for s in series_list]
    await message.reply_text("**📺 All Available Series**", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^s#"))
async def series_cb(client, cb: CallbackQuery):
    series_name = cb.data.split("#")[1]
    files = await get_series_files(series_name)
    await start_nav_flow(client, cb.message, series_name, files, is_cb=True)

async def start_nav_flow(client, message, series, files, is_cb=False):
    # SERIES -> LANGUAGE -> QUALITY -> SEASON -> EPISODE

    # 3) Language Detection
    langs = sorted(list(set(detect_lang(f['file_name']) for f in files)))
    if len(langs) > 1:
        # Multiple languages exist
        buttons = [[InlineKeyboardButton(l, callback_data=pack("l", series, l))] for l in langs]
        text = f"**📺 {series.title()}**\n\n**Select Language:**"
        if is_cb: await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        else: await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    lang = langs[0] if langs else "None"
    await language_flow(client, message, series, lang, files, is_cb)

async def language_flow(client, message, series, lang, files, is_cb):
    # Filter files by lang if lang != "None"
    if lang != "None":
        files = [f for f in files if detect_lang(f['file_name']) == lang]

    # 4) Quality Detection
    quals = sorted(list(set(detect_qual(f['file_name']) for f in files)))
    if len(quals) > 1:
        buttons = [[InlineKeyboardButton(q, callback_data=pack("q", series, lang, q))] for q in quals]
        text = f"**📺 {series.title()} [{lang}]**\n\n**Select Quality:**"
        if is_cb: await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        else: await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    qual = quals[0] if quals else "None"
    await quality_flow(client, message, series, lang, qual, files, is_cb)

async def quality_flow(client, message, series, lang, qual, files, is_cb):
    # Filter by qual
    if qual != "None":
        files = [f for f in files if detect_qual(f['file_name']) == qual]

    # 5) Season Detection
    seasons = set()
    for f in files:
        match = SEASON_REGEX.search(f['file_name'])
        if match: seasons.add(int(match.group(2)))
        else: seasons.add(1) # Default Season 1

    sorted_seasons = sorted(list(seasons))
    if len(sorted_seasons) > 1:
        buttons = [[InlineKeyboardButton(f"Season {s}", callback_data=pack("sn", series, lang, qual, s))] for s in sorted_seasons]
        text = f"**📺 {series.title()} [{lang}] [{qual}]**\n\n**Select Season:**"
        if is_cb: await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        else: await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    season = sorted_seasons[0] if sorted_seasons else 1
    await season_flow(client, message, series, lang, qual, season, files, is_cb)

async def season_flow(client, message, series, lang, qual, season, files, is_cb):
    # Filter by season
    final_files = []
    for f in files:
        match = SEASON_REGEX.search(f['file_name'])
        cur_s = int(match.group(2)) if match else 1
        if cur_s == season:
            final_files.append(f)

    # 6) Episode Detection
    episodes = []
    for f in final_files:
        match = EPISODE_REGEX.search(f['file_name'])
        e_num = int(match.group(2)) if match else 1
        episodes.append({
            "id": str(f['_id']),
            "name": f['file_name'],
            "e_num": e_num
        })

    sorted_ep = sorted(episodes, key=lambda x: x['e_num'])
    buttons = []
    for ep in sorted_ep:
        btn_text = f"Episode E{ep['e_num']:02}"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"f#{ep['id']}")])

    text = f"**📺 {series.title()} [{lang}] [{qual}] - Season {season}**\n\n**Select Episode:**"
    if is_cb: await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else: await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Register mid-flow callbacks
@Client.on_callback_query(filters.regex(r"^l#"))
async def lang_cb(client, cb: CallbackQuery):
    _, s, l, q, sn = cb.data.split("#")
    files = await get_series_files(s)
    await language_flow(client, cb.message, s, l, files, is_cb=True)

@Client.on_callback_query(filters.regex(r"^q#"))
async def qual_cb(client, cb: CallbackQuery):
    _, s, l, q, sn = cb.data.split("#")
    files = await get_series_files(s)
    # Re-apply lang filter
    if l != "None": files = [f for f in files if detect_lang(f['file_name']) == l]
    await quality_flow(client, cb.message, s, l, q, files, is_cb=True)

@Client.on_callback_query(filters.regex(r"^sn#"))
async def season_cb(client, cb: CallbackQuery):
    _, s, l, q, sn = cb.data.split("#")
    files = await get_series_files(s)
    if l != "None": files = [f for f in files if detect_lang(f['file_name']) == l]
    if q != "None": files = [f for f in files if detect_qual(f['file_name']) == q]
    await season_flow(client, cb.message, s, l, q, int(sn), files, is_cb=True)
