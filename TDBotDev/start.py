from pyrogram import Client, filters
from config import START_TEXT

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await message.reply_text(START_TEXT)
