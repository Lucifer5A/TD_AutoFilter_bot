import asyncio
import random
import time

from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery
)

from config import (
    FORCE_SUB_CHANNELS,
    ADMIN_IDS,
    FORCE_SUB_TEXT,
    PICS,
    START_TEXT,
    UPDATES
)

from utils import safe_reply, style_text, style_btn

# Cache Structure:
# {user_id: expiry_timestamp}
SUB_CACHE = {}

JOIN_BUTTON_TEXT = "Join Channel 🔗"
TRY_AGAIN_BUTTON_TEXT = "Try Again 🔄"

SUCCESS_TEXT = "✅ Thank you for joining! You can now use the bot."
ALERT_TEXT = "❌ You haven't joined all channels yet!"

CACHE_TIME = 10


async def is_subscribed(client: Client, user_id: int):

    # Admin bypass
    if user_id in ADMIN_IDS:
        return True, []

    # Cache check
    expiry = SUB_CACHE.get(user_id)

    if expiry and expiry > time.time():
        return True, []

    unjoined = []

    for channel_id in FORCE_SUB_CHANNELS:

        try:
            member = await client.get_chat_member(channel_id, user_id)

            # Robust status check for various Pyrogram versions
            status = str(member.status).lower()
            if "left" in status or "kicked" in status or "banned" in status:
                unjoined.append(channel_id)

        except UserNotParticipant:
            unjoined.append(channel_id)

        except Exception as e:
            print(f"[FORCESUB ERROR] {channel_id}: {e}")
            # If there's an error (like PeerIdInvalid), we might want to skip this channel
            # instead of blocking the user, but the user wants it to work.
            # Let's be cautious. If the bot is not admin, it might fail.
            continue

    subscribed = len(unjoined) == 0

    if subscribed:
        SUB_CACHE[user_id] = time.time() + CACHE_TIME

    else:
        # Remove old cache if user unsubscribed
        SUB_CACHE.pop(user_id, None)

    return subscribed, unjoined


async def build_buttons(client: Client, channels):

    buttons = []

    for chat_id in channels:

        try:
            chat = await client.get_chat(chat_id)

            invite_link = None

            # Public channel
            if chat.username:
                invite_link = f"https://t.me/{chat.username}"

            # Existing invite link
            elif getattr(chat, "invite_link", None):
                invite_link = chat.invite_link

            # Export new invite link
            else:
                try:
                    invite_link = await client.export_chat_invite_link(chat_id)
                except Exception as e:
                    print(f"[INVITE EXPORT ERROR] {chat_id}: {e}")

            if not invite_link:
                invite_link = UPDATES

            buttons.append([
                InlineKeyboardButton(
                    style_btn(JOIN_BUTTON_TEXT),
                    url=invite_link
                )
            ])

        except Exception as e:
            print(f"[BUTTON BUILD ERROR] {chat_id}: {e}")
            # Fallback for error case
            buttons.append([
                InlineKeyboardButton(
                    style_btn(JOIN_BUTTON_TEXT),
                    url=UPDATES
                )
            ])

    # Always add retry button
    buttons.append([
        InlineKeyboardButton(
            style_btn(TRY_AGAIN_BUTTON_TEXT),
            callback_data="check_sub"
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def force_sub(client: Client, message: Message, user_id: int = None):

    user_id = user_id or message.from_user.id

    subscribed, unjoined_channels = await is_subscribed(client, user_id)

    if subscribed:
        return True

    reply_markup = await build_buttons(client, unjoined_channels)

    styled_text = style_text(FORCE_SUB_TEXT)

    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=random.choice(PICS),
            caption=styled_text,
            reply_markup=reply_markup
        )

    except Exception as e:

        print(f"[FORCESUB SEND ERROR]: {e}")

        await safe_reply(
            message,
            styled_text,
            reply_markup=reply_markup
        )

    return False


@Client.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_callback(client: Client, cb: CallbackQuery):

    user_id = cb.from_user.id

    # Force immediate re-check by clearing cache
    SUB_CACHE.pop(user_id, None)

    subscribed, _ = await is_subscribed(client, user_id)

    if not subscribed:
        return await cb.answer(ALERT_TEXT, show_alert=True)

    from TDBotDev.start import get_start_buttons

    styled_start = style_text(START_TEXT)

    try:
        await cb.message.delete()
    except:
        pass

    try:

        await client.send_photo(
            chat_id=cb.message.chat.id,
            photo=random.choice(PICS),
            caption=styled_start,
            reply_markup=get_start_buttons()
        )

    except Exception:

        await client.send_message(
            chat_id=cb.message.chat.id,
            text=styled_start,
            reply_markup=get_start_buttons()
        )

    await cb.answer(SUCCESS_TEXT, show_alert=False)
