from pyrogram import Client, filters
from database import collection, db
from config import OWNER_ID
from utils import safe_reply
from TDBotDev.forcesub import force_sub

@Client.on_message(filters.command("reset") & filters.private)
async def reset_handler(client, message):
    if not await force_sub(client, message):
        return

    if message.from_user.id != OWNER_ID:
        await safe_reply(message, "❌ You are not authorized to use this command")
        return

    try:
        # Delete ALL documents from MongoDB files collection
        await collection.delete_many({})
        # Also clear scan states and nav cache
        await db["scan_state"].delete_many({})
        await db["nav_cache"].delete_many({})
        await safe_reply(message, "✅ Database and cache have been reset successfully")
    except Exception as e:
        await safe_reply(message, f"❌ Error resetting database: {str(e)}")
