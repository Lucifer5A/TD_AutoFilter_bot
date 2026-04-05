import asyncio
from pyrogram import Client, filters
from config import ADMINS, OWNER_ID
from database import db, add_file, collection

@Client.on_message(filters.command("scan_channel") & filters.private)
async def scan_channel_handler(client, message):
    # Authorization check
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in ADMINS:
        await message.reply_text("❌ You are not authorized to use this command")
        return

    # Extract channel_id from command
    if len(message.command) < 2:
        await message.reply_text("Usage: `/scan_channel -100xxxxxxxxxx`")
        return

    try:
        channel_id = int(message.command[1])
    except ValueError:
        await message.reply_text("❌ Invalid Channel ID format")
        return

    status_msg = await message.reply_text(f"Starting scan for channel: `{channel_id}`...")

    # Check for resume state
    scan_state = db["scan_state"]
    checkpoint = await scan_state.find_one({"channel_id": channel_id})
    last_id = checkpoint["last_message_id"] if checkpoint else 0

    total_saved = 0
    print(f"Scanning channel {channel_id} starting from message_id > {last_id}")

    try:
        # get_chat_history(offset_id) scans OLDER than offset_id by default.
        # To scan NEWER than last_id, we use offset_id and scan history differently.
        # However, for a full scan, we scan latest to oldest.

        async for msg in client.get_chat_history(channel_id):
            # If we reached the last saved message, we can stop (if scanning latest to oldest)
            if msg.id <= last_id:
                break

            media = msg.document or msg.video or msg.audio
            if media:
                file_id = media.file_id
                file_name = getattr(media, "file_name", "unknown_file")
                file_type = "document" if msg.document else ("video" if msg.video else "audio")

                # Check for duplicates
                exists = await collection.find_one({"file_id": file_id})
                if not exists:
                    await add_file(
                        file_id=file_id,
                        file_name=file_name,
                        caption=msg.caption,
                        message_id=msg.id,
                        channel_id=channel_id,
                        file_type=file_type
                    )
                    total_saved += 1

                    # Live status update
                    if total_saved % 50 == 0:
                        try:
                            await status_msg.edit_text(f"Scanning channel... {total_saved} files saved")
                        except:
                            pass

                # Update checkpoint in background
                await scan_state.update_one(
                    {"channel_id": channel_id},
                    {"$set": {"last_message_id": msg.id}},
                    upsert=True
                )

                # Performance delay
                await asyncio.sleep(0.3)

        await status_msg.edit_text(
            f"✅ Channel scan completed successfully\nTotal files saved: {total_saved}"
        )

    except Exception as e:
        await message.reply_text(f"❌ Error during scan: {str(e)}")
        print(f"Scan Error: {e}")
