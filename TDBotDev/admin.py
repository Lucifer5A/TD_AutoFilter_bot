from pyrogram import Client, filters
from database import collection
from config import OWNER_ID

@Client.on_message(filters.command("reset") & filters.private)
async def reset_handler(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text("❌ You are not authorized to use this command")
        return

    try:
        # 3: Delete ALL documents from MongoDB files collection
        await collection.delete_many({})
        await message.reply_text("✅ Database has been reset successfully")
    except Exception as e:
        await message.reply_text(f"❌ Error resetting database: {str(e)}")
