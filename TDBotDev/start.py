import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import START_TEXT, PICS, LOG_CHANNEL_ID, UPDATES
from TDBotDev.forcesub import force_sub
from utils import safe_reply, style_text, style_btn
import datetime

# Helper to generate the main start menu keyboard
def get_start_buttons():
    buttons = [
        [
            InlineKeyboardButton(style_btn("📖 Help"), callback_data="help_menu"),
            InlineKeyboardButton(style_btn("❄️ Update"), url=UPDATES),
        ],
        [
            InlineKeyboardButton(style_btn("About ☘️"), callback_data="about_menu")
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
    styled_start = style_text(START_TEXT)
    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=random.choice(PICS),
            caption=styled_start,
            reply_markup=get_start_buttons()
        )
    except Exception:
        await safe_reply(message, styled_start, reply_markup=get_start_buttons())
