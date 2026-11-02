import json
import asyncio
from aiogram.types import Message, FSInputFile, LinkPreviewOptions, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from config import ASSETS_DIR
from database import get_cached_banner_file_id, set_cached_banner_file_id
from keyboards.inline import build_inline_keyboard, get_post_settings_inline_keyboard
from locales.strings import t

async def remove_reply_keyboard(message: Message):
    try:
        cleaner = await message.answer("🔄", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(0.5)
        await cleaner.delete()
    except Exception:
        pass

async def send_cached_banner(target_message: Message, banner_name: str, caption: str, reply_markup=None, parse_mode: str = None) -> Message:
    cached_id = await get_cached_banner_file_id(banner_name)
    if cached_id:
        try:
            return await target_message.answer_photo(
                photo=cached_id,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception:
            pass

    banner_file = ASSETS_DIR / f"{banner_name}.jpg"
    if banner_file.exists():
        photo_input = FSInputFile(banner_file)
        sent = await target_message.answer_photo(
            photo=photo_input,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        if sent and getattr(sent, "photo", None) and isinstance(sent.photo, list) and len(sent.photo) > 0 and hasattr(sent.photo[-1], "file_id") and isinstance(sent.photo[-1].file_id, str):
            await set_cached_banner_file_id(banner_name, sent.photo[-1].file_id)
        return sent

    return await target_message.answer(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )

async def send_post_preview(target_message: Message, state: FSMContext, lang: str = "en"):
    data = await state.get_data()
    content_type = data.get("content_type", "text")
    file_id = data.get("file_id")
    text = data.get("text", "")
    text_pos = data.get("text_pos", "below")
    buttons = data.get("buttons", [])
    
    inline_kb = build_inline_keyboard(buttons) if buttons else None
    show_above = (text_pos == "above")
    
    if content_type == "photo" and file_id:
        await target_message.answer_photo(
            photo=file_id,
            caption=text or None,
            show_caption_above_media=show_above,
            reply_markup=inline_kb
        )
    elif content_type == "video" and file_id:
        await target_message.answer_video(
            video=file_id,
            caption=text or None,
            show_caption_above_media=show_above,
            reply_markup=inline_kb
        )
    elif content_type == "animation" and file_id:
        await target_message.answer_animation(
            animation=file_id,
            caption=text or None,
            show_caption_above_media=show_above,
            reply_markup=inline_kb
        )
    elif content_type == "document" and file_id:
        await target_message.answer_document(document=file_id, caption=text or None, reply_markup=inline_kb)
    elif content_type == "audio" and file_id:
        await target_message.answer_audio(audio=file_id, caption=text or None, reply_markup=inline_kb)
    elif content_type == "voice" and file_id:
        await target_message.answer_voice(voice=file_id, caption=text or None, reply_markup=inline_kb)
    elif content_type == "sticker" and file_id:
        await target_message.answer_sticker(sticker=file_id)
        if text or inline_kb:
            await target_message.answer(text=text or "Preview", reply_markup=inline_kb)
    else:
        link_opts = LinkPreviewOptions(show_above_text=not show_above) if text else None
        await target_message.answer(
            text=text or "Empty text",
            reply_markup=inline_kb,
            link_preview_options=link_opts
        )
        
    has_text = bool(text)
    has_buttons = bool(buttons)
    settings_kb = get_post_settings_inline_keyboard(lang, has_text=has_text, has_buttons=has_buttons, text_pos=text_pos)
    settings_header = t("post_settings_header", lang)
    
    await target_message.answer(settings_header, reply_markup=settings_kb)
