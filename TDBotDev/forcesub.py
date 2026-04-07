import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, ChatAdminRequired
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
        except Exception as e:
            # If bot is not admin or channel invalid, we skip check for that channel to avoid blocking user
            print(f"ForceSub Error for {channel_id}: {e}")
            continue

    return (len(unjoined) == 0), unjoined

async def force_sub(client: Client, message: Message, user_id: int = None):
    # Use user_id if provided (for callbacks), else get from message
    if not user_id:
        user_id = message.from_user.id

    subscribed, unjoined_channels = await is_subscribed(client, user_id)

    if subscribed:
        return True

    # Generate Buttons
    buttons = []
    for chat_id in unjoined_channels:
        try:
            # Try to get invite link automatically
            chat = await client.get_chat(chat_id)
            invite_link = chat.invite_link
            if not invite_link:
                if chat.username:
                    invite_link = f"https://t.me/{chat.username}"
                else:
                    # If private and no link, attempt to export one
                    try:
                        invite_link = await client.export_chat_invite_link(chat_id)
                    except Exception:
                        # If still no link, we'll just use the ID or title as placeholder
                        # But typically we need a URL for the button.
                        continue

            buttons.append([InlineKeyboardButton(JOIN_BUTTON_TEXT, url=invite_link)])
        except Exception as e:
            print(f"Error fetching chat {chat_id}: {e}")
            continue

    # ALWAYS block the user if they are not subscribed, even if buttons fail to generate
    # We add the "Try Again" button at minimum.
    buttons.append([InlineKeyboardButton(TRY_AGAIN_BUTTON_TEXT, callback_data="check_sub")])

    # Determine where to send/edit the message
    chat_id = message.chat.id if hasattr(message, "chat") else message.message.chat.id

    # Send ForceSub UI with random image
    try:
        await client.send_photo(
            chat_id=chat_id,
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

    # Small delay to ensure Telegram DB consistency
    await asyncio.sleep(1)

    subscribed, _ = await is_subscribed(client, user_id)

    if subscribed:
        from TDBotDev.start import get_start_buttons
        await cb.message.delete()
        try:
            await client.send_photo(
                chat_id=cb.message.chat.id,
                photo=random.choice(PICS),
                caption=START_TEXT,
                reply_markup=get_start_buttons()
            )
        except:
            await client.send_message(cb.message.chat.id, START_TEXT, reply_markup=get_start_buttons())
        await cb.answer(SUCCESS_TEXT.replace("**", ""), show_alert=False)
    else:
        await cb.answer(ALERT_TEXT, show_alert=True)
