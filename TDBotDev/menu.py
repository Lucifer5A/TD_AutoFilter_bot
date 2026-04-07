from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import START_TEXT, HELP_TEXT, ABOUT_TEXT, UPDATES
from TDBotDev.start import get_start_buttons

@Client.on_callback_query(filters.regex(r"^(help_menu|about_menu|back_start|updates_menu)$"))
async def menu_callback_handler(client: Client, cb: CallbackQuery):
    data = cb.data

    if data == "updates_menu":
        # Rule: Do NOT show any text, only open channel link
        await cb.answer(url=UPDATES)
        return

    # Use back button for help/about
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]])

    if data == "help_menu":
        await cb.message.edit_caption(caption=HELP_TEXT, reply_markup=back_button)
    elif data == "about_menu":
        await cb.message.edit_caption(caption=ABOUT_TEXT, reply_markup=back_button)
    elif data == "back_start":
        await cb.message.edit_caption(caption=START_TEXT, reply_markup=get_start_buttons())

    await cb.answer()
