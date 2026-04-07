import random
from pyrogram import Client, filters
from config import START_TEXT, PICS
from TDBotDev.forcesub import force_sub
from utils import safe_reply

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if not await force_sub(client, message):
        return

    # If subscribed, send random START image with welcome message
    try:
        await client.send_photo(
            chat_id=message.chat.id,
            photo=random.choice(PICS),
            caption=START_TEXT
        )
    except Exception:
        await safe_reply(message, START_TEXT)
