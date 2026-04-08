import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import FloodWait
from config import ADMIN_IDS
from Database.database import get_all_users, get_total_users
from utils import style_text, style_btn, safe_reply, safe_edit

# Global broadcast state
broadcast_state = {}

@Client.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def broadcast_command_handler(client, message: Message):
    user_id = message.from_user.id
    broadcast_state[user_id] = {"step": "waiting", "message": None}

    text = (
        "📢 **𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗣𝗮𝗻𝗲𝗹**\n\n"
        "Send the message you want to broadcast to all users.\n\n"
        "Supported:\n"
        "• Text\n"
        "• Photo\n"
        "• Video\n"
        "• Document"
    )

    buttons = [[InlineKeyboardButton(style_btn("❌ Cancel"), callback_data="bc_cancel")]]
    await safe_reply(message, style_text(text), reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.private & filters.user(ADMIN_IDS) & ~filters.command(["start", "broadcast", "status", "reset", "delete_file", "delete_files"]))
async def capture_broadcast_message(client, message: Message):
    user_id = message.from_user.id
    if user_id not in broadcast_state or broadcast_state[user_id]["step"] != "waiting":
        return

    broadcast_state[user_id]["step"] = "preview"
    broadcast_state[user_id]["message"] = message

    text = (
        "📢 **𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗣𝗿𝗲𝘃𝗶𝗲𝘄**\n\n"
        "This message will be sent to all users."
    )

    buttons = [
        [
            InlineKeyboardButton(style_btn("✅ Send"), callback_data="bc_send"),
            InlineKeyboardButton(style_btn("✏️ Edit"), callback_data="bc_edit")
        ],
        [InlineKeyboardButton(style_btn("❌ Cancel"), callback_data="bc_cancel")]
    ]

    # We reply with preview, not editing the original because admin might have sent a photo etc
    await message.reply_text(style_text(text), reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^bc_") & filters.user(ADMIN_IDS))
async def broadcast_callback_handler(client, cb: CallbackQuery):
    user_id = cb.from_user.id
    action = cb.data.replace("bc_", "")

    if action == "cancel":
        broadcast_state.pop(user_id, None)
        await safe_edit(cb.message, style_text("❌ Broadcast cancelled"))
        return

    if action == "edit":
        broadcast_state[user_id] = {"step": "waiting", "message": None}
        await safe_edit(cb.message, style_text("Send the new message you want to broadcast:"))
        return

    if action == "send":
        if user_id not in broadcast_state or not broadcast_state[user_id]["message"]:
            await cb.answer("No message to broadcast!", show_alert=True)
            return

        msg = broadcast_state[user_id]["message"]
        broadcast_state.pop(user_id, None)

        await cb.answer("Starting broadcast...", show_alert=False)

        success = 0
        failed = 0
        total = await get_total_users()

        # Initial Progress message
        progress_text = (
            "📡 **𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁𝗶𝗻𝗴...**\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            "✅ **Sent**     : 0\n"
            "❌ **Failed**   : 0\n"
            "👥 **Total**    : {total}\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            "⚡ **Please wait...**"
        ).format(total=total)

        progress_msg = await safe_edit(cb.message, style_text(progress_text))

        users_cursor = await get_all_users()
        last_update = time.time()

        async for user in users_cursor:
            target_id = user["_id"]
            try:
                await msg.copy(chat_id=target_id)
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await msg.copy(chat_id=target_id)
                success += 1
            except Exception:
                failed += 1

            # Update UI every 5 seconds
            if time.time() - last_update > 5:
                curr_text = (
                    "📡 **𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁𝗶𝗻𝗴...**\n\n"
                    "━━━━━━━━━━━━━━━\n\n"
                    f"✅ **Sent**     : {success}\n"
                    f"❌ **Failed**   : {failed}\n"
                    f"👥 **Total**    : {total}\n\n"
                    "━━━━━━━━━━━━━━━\n\n"
                    "⚡ **Please wait...**"
                )
                await safe_edit(progress_msg, style_text(curr_text))
                last_update = time.time()

            await asyncio.sleep(0.05) # Small gap

        final_text = (
            "📊 **𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱**\n\n"
            "━━━━━━━━━━━━━━━\n\n"
            f"✅ **Success**  : {success}\n"
            f"❌ **Failed**   : {failed}\n"
            f"👥 **Total**    : {total}\n\n"
            "━━━━━━━━━━━━━━━"
        )

        buttons = [
            [
                InlineKeyboardButton(style_btn("🔁 New Broadcast"), callback_data="bc_new"),
                InlineKeyboardButton(style_btn("🏠 Back"), callback_data="status_refresh")
            ]
        ]
        await safe_edit(progress_msg, style_text(final_text), reply_markup=InlineKeyboardMarkup(buttons))

    if action == "new":
        broadcast_state[user_id] = {"step": "waiting", "message": None}
        text = (
            "📢 **𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝗣𝗮𝗻𝗲𝗹**\n\n"
            "Send the message you want to broadcast to all users."
        )
        buttons = [[InlineKeyboardButton(style_btn("❌ Cancel"), callback_data="bc_cancel")]]
        await safe_edit(cb.message, style_text(text), reply_markup=InlineKeyboardMarkup(buttons))
