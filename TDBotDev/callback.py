from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import START_TEXT, HELP_TEXT, ABOUT_TEXT, UPDATES
from TDBotDev.start import get_start_buttons
from TDBotDev.forcesub import force_sub
from utils import style_text, style_btn

@Client.on_callback_query(filters.regex(r"^(help_menu|about_menu|back_start)$"))
async def menu_callback_handler(client: Client, cb: CallbackQuery):
    await cb.answer()

    if not await force_sub(client, cb.message, user_id=cb.from_user.id):
        return

    data = cb.data

    # Use back button for help/about
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton(style_btn("🔙 Back"), callback_data="back_start")]])

    if data == "help_menu":
        await cb.message.edit_caption(caption=style_text(HELP_TEXT), reply_markup=back_button)
    elif data == "about_menu":
        await cb.message.edit_caption(caption=style_text(ABOUT_TEXT), reply_markup=back_button)
    elif data == "back_start":
        await cb.message.edit_caption(caption=style_text(START_TEXT), reply_markup=get_start_buttons())

    await cb.answer()
