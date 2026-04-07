import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import START_TEXT, PICS, LOG_CHANNEL_ID, UPDATES
from TDBotDev.forcesub import force_sub
from utils import safe_reply
import datetime

# Helper to generate the main start menu keyboard
def get_start_buttons():
    buttons = [
        [
            InlineKeyboardButton("📖 Help", callback_data="help_menu"),
            InlineKeyboardButton("🏚️ Updates", callback_data="updates_menu"),
            InlineKeyboardButton("❄️ About", callback_data="about_menu")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if not await force_sub(client, message):
        return

    # Log user details on /start
    user = message.from_user
    log_text = (
        f"👤 **New User Started Bot**\n\n"
        f"**User ID:** `{user.id}`\n"
        f"**First Name:** {user.first_name}\n"
        f"**Username:** @{user.username if user.username else 'None'}\n"
        f"**Mention:** {user.mention}\n"
        f"**Time:** `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    try:
        await client.send_message(LOG_CHANNEL_ID, log_text)
    except Exception as e:
        print(f"Log Error: {e}")

    # Send random START image with welcome message and menu buttons
    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=random.choice(PICS),
            caption=START_TEXT,
            reply_markup=get_start_buttons()
        )
    except Exception:
        await safe_reply(message, START_TEXT, reply_markup=get_start_buttons())
