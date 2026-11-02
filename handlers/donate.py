from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from config import DONATE_LINK, DONATE_TEXT
from keyboards.inline import get_donate_inline_keyboard
from locales.strings import t, get_button_variants
from database import get_or_create_user
from handlers.preview_helper import remove_reply_keyboard

router = Router(name="donate_router")

DONATE_TRIGGERS = get_button_variants("btn_donate", ["donate", "/donate", "support"])

@router.message(Command("donate"), StateFilter("*"))
@router.message(F.text.lower().in_(DONATE_TRIGGERS), StateFilter("*"))
@router.callback_query(F.data == "open_donate", StateFilter("*"))
async def show_donate_info(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    if isinstance(event, Message):
        await remove_reply_keyboard(event)
        
    user_id = event.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    msg_target = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()
        
    title = t("donate_title", lang)
    custom_desc = DONATE_TEXT if DONATE_TEXT else t("donate_text", lang)
    full_text = f"{title}\n\n{custom_desc}"
    
    kb = get_donate_inline_keyboard(DONATE_LINK)
    await msg_target.answer(full_text, reply_markup=kb)

@router.callback_query(F.data == "close_donate", StateFilter("*"))
async def cb_close_donate(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass

