from pyrogram import Client, filters
from config import START_TEXT
from utils import safe_reply

@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await safe_reply(message, START_TEXT)
