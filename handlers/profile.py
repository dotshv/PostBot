from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from database import get_or_create_user, get_user_stats, update_user_setting
from keyboards.inline import get_profile_keyboard
from locales.strings import t, LANGUAGES, get_button_variants
from handlers.preview_helper import send_cached_banner, remove_reply_keyboard

router = Router(name="profile_router")

PROFILE_TRIGGERS = get_button_variants("btn_profile", ["profile", "/profile", "my profile", "settings"])

async def render_profile(target_event: Message | CallbackQuery, user_id: int):
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    stats = await get_user_stats(user_id)
    
    lang_display = LANGUAGES.get(lang, lang.upper())
    link_preview = "On" if user_dict.get("link_preview") else "Off"
    auto_forwards = "On" if user_dict.get("auto_save_forwards") else "Off"
    
    text = t(
        "profile_text",
        lang,
        user_id=user_id,
        posts_count=stats["posts_created"],
        fav_count=stats["saved_favorites"],
        lang_display=lang_display,
        link_preview=link_preview,
        auto_forwards=auto_forwards
    )
    
    kb = get_profile_keyboard(user_dict, lang)
    
    if isinstance(target_event, Message):
        await send_cached_banner(target_event, "profile", text, reply_markup=kb)
    else:
        try:
            await target_event.message.edit_caption(caption=text, reply_markup=kb)
        except Exception:
            try:
                await target_event.message.edit_text(text=text, reply_markup=kb)
            except Exception:
                await send_cached_banner(target_event.message, "profile", text, reply_markup=kb)
        await target_event.answer()

@router.callback_query(F.data == "btn_profile", StateFilter("*"))
@router.message(F.text.lower().in_(PROFILE_TRIGGERS) | F.text.lower().contains("profile"), StateFilter("*"))
async def show_profile_msg(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    if isinstance(event, Message):
        await remove_reply_keyboard(event)
    await render_profile(event, event.from_user.id)

@router.callback_query(F.data == "toggle_preview", StateFilter("*"))
async def cb_toggle_preview(callback: CallbackQuery):
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    current_val = user_dict.get("link_preview", 0)
    new_val = 0 if current_val else 1
    await update_user_setting(callback.from_user.id, "link_preview", new_val)
    status_str = "On" if new_val else "Off"
    await callback.answer(f"Link Preview: {status_str}")
    await render_profile(callback, callback.from_user.id)

@router.callback_query(F.data == "toggle_autoforwards", StateFilter("*"))
async def cb_toggle_autoforwards(callback: CallbackQuery):
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    current_val = user_dict.get("auto_save_forwards", 0)
    new_val = 0 if current_val else 1
    await update_user_setting(callback.from_user.id, "auto_save_forwards", new_val)
    status_str = "On" if new_val else "Off"
    await callback.answer(f"Auto-save Forwards: {status_str}")
    await render_profile(callback, callback.from_user.id)
