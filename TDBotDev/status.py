import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import ADMIN_IDS
from Database.database import db, collection, get_total_users, nav_cache
from utils import style_text, style_btn, safe_reply, safe_edit

def get_uptime(start_time):
    delta = int(time.time() - start_time)
    hours, rem = divmod(delta, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {seconds}s"

async def get_status_ui(client, start_time, start_check_time=None):
    # 1. DB Check
    try:
        await db.command("ping")
        db_status = "Connected"
    except Exception:
        db_status = "Error"

    # 2. Ping calculation
    ping = 0
    if start_check_time:
        ping = round((time.time() - start_check_time) * 1000)

    # 3. Counts
    users = await get_total_users()
    files = await collection.count_documents({})
    uptime = get_uptime(start_time)

    text = (
        "⚙️ **𝗧𝗗 𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗧𝗔𝗧𝗨𝗦**\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"🤖 **𝗕𝗼𝘁**        : Online\n"
        f"🧠 **𝗗𝗕**         : {db_status}\n"
        f"⚡ **𝗣𝗶𝗻𝗴**       : {ping} ms\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"⏳ **𝗨𝗽𝘁𝗶𝗺𝗲**     : {uptime}\n"
        f"👥 **𝗨𝘀𝗲𝗿𝘀**      : {users:,}\n"
        f"📁 **𝗙𝗶𝗹𝗲𝘀**      : {files:,}\n\n"
        "━━━━━━━━━━━━━━━"
    )

    buttons = [
        [
            InlineKeyboardButton(style_btn("🔄 Refresh"), callback_data="status_refresh"),
            InlineKeyboardButton(style_btn("🧹 Clear Cache"), callback_data="clear_cache")
        ]
    ]
    return style_text(text), InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("status") & filters.user(ADMIN_IDS))
async def status_command_handler(client, message: Message):
    start_time = getattr(client, "start_time", time.time())
    text, markup = await get_status_ui(client, start_time, time.time())
    await safe_reply(message, text, reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^status_refresh$") & filters.user(ADMIN_IDS))
async def status_refresh_handler(client, cb: CallbackQuery):
    start_time = getattr(client, "start_time", time.time())
    text, markup = await get_status_ui(client, start_time, time.time())
    await safe_edit(cb.message, text, reply_markup=markup)
    await cb.answer("Status Updated 🔄")

@Client.on_callback_query(filters.regex(r"^clear_cache$") & filters.user(ADMIN_IDS))
async def clear_cache_handler(client, cb: CallbackQuery):
    try:
        await nav_cache.delete_many({})
        await cb.answer("Cache cleared successfully ✅", show_alert=True)
    except Exception as e:
        await cb.answer(f"Error: {str(e)}", show_alert=True)
