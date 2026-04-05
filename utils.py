import asyncio
from pyrogram.errors import MessageNotModified, FloodWait

async def safe_edit(message, text, reply_markup=None):
    try:
        return await message.edit_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        return message
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await safe_edit(message, text, reply_markup)
    except Exception:
        return message

async def safe_reply(message, text, reply_markup=None):
    try:
        return await message.reply_text(text, reply_markup=reply_markup)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await safe_reply(message, text, reply_markup)
    except Exception:
        return None
