from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME
from database import get_or_create_user
from locales.strings import t, get_button_variants
from handlers.preview_helper import send_cached_banner, remove_reply_keyboard

router = Router(name="help_router")

HELP_TRIGGERS = get_button_variants("btn_help", ["help", "/help", "guide", "помощь"])

@router.message(Command("help"), StateFilter("*"))
@router.message(F.text.lower().in_(HELP_TRIGGERS), StateFilter("*"))
@router.callback_query(F.data == "show_help", StateFilter("*"))
async def show_help_guide(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    if isinstance(event, Message):
        await remove_reply_keyboard(event)
        
    user_id = event.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    text = t("help_text", lang, bot_username=BOT_USERNAME or "bot")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Menu", callback_data="back_to_menu", style="danger")]])
    
    if isinstance(event, Message):
        await send_cached_banner(event, "help", text, reply_markup=kb)
    else:
        await event.answer()
        await send_cached_banner(event.message, "help", text, reply_markup=kb)
