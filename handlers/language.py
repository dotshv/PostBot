from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME
from database import get_or_create_user, update_user_setting
from keyboards.inline import get_language_keyboard, get_welcome_inline_keyboard
from locales.strings import t, LANGUAGES, LANGUAGE_NAMES, get_button_variants
from handlers.preview_helper import send_cached_banner, remove_reply_keyboard

router = Router(name="language_router")

LANG_TRIGGERS = get_button_variants("btn_language", ["language", "lang", "bhasha", "dil", "язык", "zaban", "/lang", "/language"])

@router.message(Command("lang", "language"), StateFilter("*"))
@router.message(F.text.lower().in_(LANG_TRIGGERS), StateFilter("*"))
@router.callback_query(F.data == "settings_lang", StateFilter("*"))
async def show_language_selector(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    if isinstance(event, Message):
        await remove_reply_keyboard(event)
        
    user_id = event.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    text = t("choose_language", lang)
    kb = get_language_keyboard()
    
    if isinstance(event, Message):
        await send_cached_banner(event, "language", text, reply_markup=kb)
    else:
        await event.answer()
        try:
            await event.message.edit_caption(caption=text, reply_markup=kb)
        except Exception:
            try:
                await event.message.edit_text(text=text, reply_markup=kb)
            except Exception:
                await send_cached_banner(event.message, "language", text, reply_markup=kb)

@router.callback_query(F.data.startswith("setlang_"), StateFilter("*"))
async def process_set_language(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang_code = callback.data.split("_")[1]
    
    if lang_code not in LANGUAGES:
        await callback.answer()
        return
        
    await update_user_setting(callback.from_user.id, "language", lang_code)
    lang_name = LANGUAGE_NAMES.get(lang_code, LANGUAGES.get(lang_code, lang_code))
    alert_msg = t("lang_changed", lang_code, name=lang_name, lang=lang_name)
    
    await callback.answer(alert_msg, show_alert=True)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    welcome_text = t("welcome", lang_code, bot_username=BOT_USERNAME or "bot")
    welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang_code)
    
    await send_cached_banner(callback.message, "welcome", welcome_text, reply_markup=welcome_inline_kb)
