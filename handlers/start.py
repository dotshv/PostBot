import json
import asyncio
from datetime import datetime, timezone
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME, ADMIN_IDS
from database import get_or_create_user, get_post_by_code, get_total_users_count
from keyboards.inline import build_inline_keyboard, get_welcome_inline_keyboard
from locales.strings import t, get_button_variants
from handlers.preview_helper import send_cached_banner, remove_reply_keyboard

router = Router(name="start_router")

MENU_TRIGGERS = get_button_variants("btn_cancel", ["menu", "main menu", "close", "cancel", "главное меню", "menyu"])

@router.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or "User"
    
    user, is_new = await get_or_create_user(user_id, username, first_name)
    lang = user.get("language", "en")
    total_users = await get_total_users_count()
    
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    admin_log = (
        "User Activity Log\n"
        "Event: /start\n"
        f"Name: {first_name}\n"
        f"Username: @{username if username else 'None'}\n"
        f"User ID: {user_id}\n"
        f"Account: {'New User' if is_new else 'Existing User'}\n"
        f"Date: {now_str}\n"
        f"Total Users: {total_users}"
    )
    for aid in ADMIN_IDS:
        if aid != user_id:
            try:
                await bot.send_message(chat_id=aid, text=admin_log)
            except Exception:
                pass

    await remove_reply_keyboard(message)

    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        post_code = parts[1].strip()
        post = await get_post_by_code(post_code)
        if post:
            buttons_data = json.loads(post["buttons_json"]) if post.get("buttons_json") else []
            inline_kb = build_inline_keyboard(buttons_data)
            
            c_type = post.get("content_type", "text")
            file_id = post.get("file_id")
            caption = post.get("text") or ""
            text_pos = post.get("text_position", "below")
            show_above = (text_pos == "above")
            
            if c_type == "photo" and file_id:
                await message.answer_photo(photo=file_id, caption=caption, show_caption_above_media=show_above, reply_markup=inline_kb)
            elif c_type == "video" and file_id:
                await message.answer_video(video=file_id, caption=caption, show_caption_above_media=show_above, reply_markup=inline_kb)
            elif c_type == "animation" and file_id:
                await message.answer_animation(animation=file_id, caption=caption, show_caption_above_media=show_above, reply_markup=inline_kb)
            elif c_type == "document" and file_id:
                await message.answer_document(document=file_id, caption=caption, reply_markup=inline_kb)
            elif c_type == "audio" and file_id:
                await message.answer_audio(audio=file_id, caption=caption, reply_markup=inline_kb)
            elif c_type == "voice" and file_id:
                await message.answer_voice(voice=file_id, caption=caption, reply_markup=inline_kb)
            else:
                await message.answer(text=caption or f"Post: {post_code}", reply_markup=inline_kb)
            return

    welcome_text = t("welcome", lang, bot_username=BOT_USERNAME or "bot")
    welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang)
    
    await send_cached_banner(message, "welcome", welcome_text, reply_markup=welcome_inline_kb)

@router.callback_query(F.data == "back_to_menu", StateFilter("*"))
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    welcome_text = t("welcome", lang, bot_username=BOT_USERNAME or "bot")
    welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang)
    await send_cached_banner(callback.message, "welcome", welcome_text, reply_markup=welcome_inline_kb)

@router.message(F.text.lower().in_(MENU_TRIGGERS), StateFilter("*"))
async def msg_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(message.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    await remove_reply_keyboard(message)
        
    welcome_text = t("welcome", lang, bot_username=BOT_USERNAME or "bot")
    welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang)
    await send_cached_banner(message, "welcome", welcome_text, reply_markup=welcome_inline_kb)
