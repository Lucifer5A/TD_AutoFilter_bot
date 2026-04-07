import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant
from config import FORCE_SUB_CHANNELS, ADMIN_IDS, FORCE_SUB_TEXT, PICS, START_TEXT
from utils import safe_reply

# Button Labels & Extra Texts
JOIN_BUTTON_TEXT = "Join Channel 🔗"
TRY_AGAIN_BUTTON_TEXT = "Try Again 🔄"
SUCCESS_TEXT = "✅ **Thank you for joining! You can now use the bot.**"
ALERT_TEXT = "❌ You haven't joined all channels yet!"

async def is_subscribed(client: Client, user_id: int):
    if user_id in ADMIN_IDS:
        return True, []

    unjoined = []
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            await client.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            unjoined.append(channel_id)
        except Exception:
            continue

    return (len(unjoined) == 0), unjoined

async def force_sub(client: Client, message: Message):
    user_id = message.from_user.id
    subscribed, unjoined_channels = await is_subscribed(client, user_id)

    if subscribed:
        return True

    # Generate Buttons
    buttons = []
    for chat_id in unjoined_channels:
        try:
            chat = await client.get_chat(chat_id)
            invite_link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
            if invite_link:
                buttons.append([InlineKeyboardButton(JOIN_BUTTON_TEXT, url=invite_link)])
        except:
            continue

    buttons.append([InlineKeyboardButton(TRY_AGAIN_BUTTON_TEXT, callback_data="check_sub")])

    # Send ForceSub UI with random image
    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=random.choice(PICS),
            caption=FORCE_SUB_TEXT,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception:
        await safe_reply(message, FORCE_SUB_TEXT, reply_markup=InlineKeyboardMarkup(buttons))

    return False

@Client.on_callback_query(filters.regex(r"^check_sub$"))
async def check_sub_callback(client: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    subscribed, _ = await is_subscribed(client, user_id)

    if subscribed:
        # Success: Delete message and send welcome with random image
        await cb.message.delete()
        try:
            await client.send_photo(
                chat_id=cb.message.chat.id,
                photo=random.choice(PICS),
                caption=START_TEXT
            )
        except:
            await client.send_message(cb.message.chat.id, START_TEXT)
        await cb.answer(SUCCESS_TEXT.replace("**", ""), show_alert=False)
    else:
        await cb.answer(ALERT_TEXT, show_alert=True)
