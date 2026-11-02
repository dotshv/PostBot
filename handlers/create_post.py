import json
import secrets
import string
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME
from database import get_or_create_user, create_post
from keyboards.inline import (
    get_post_ready_keyboard,
    get_welcome_inline_keyboard,
    get_cancel_inline_keyboard,
    get_back_inline_keyboard,
    get_skip_cancel_inline_keyboard
)
from locales.strings import t, get_button_variants
from states import PostCreation
from handlers.preview_helper import send_post_preview, send_cached_banner, remove_reply_keyboard

router = Router(name="create_post_router")

CREATE_POST_TRIGGERS = get_button_variants("btn_create_post", ["create post", "create", "/new", "new post", "new"])
ADD_TEXT_TRIGGERS = get_button_variants("btn_add_text") | get_button_variants("btn_edit_text") | {"text", "add text", "edit text"}
DRAFT_TRIGGERS = get_button_variants("btn_save_drafts", ["draft", "save draft", "save"])
DONE_TRIGGERS = get_button_variants("btn_done", ["done", "finish", "ready"])
CANCEL_TRIGGERS = get_button_variants("btn_cancel", ["cancel", "abort", "back"])
SKIP_TRIGGERS = get_button_variants("btn_skip", ["skip"])

def generate_post_code() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))

@router.message(F.text.lower().in_(CREATE_POST_TRIGGERS), StateFilter("*"))
@router.callback_query(F.data == "btn_create_post", StateFilter("*"))
async def start_create_post(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    if isinstance(event, Message):
        await remove_reply_keyboard(event)
        
    await state.set_state(PostCreation.waiting_for_content)
    await state.update_data(
        lang=lang,
        content_type="text",
        file_id=None,
        text="",
        buttons=[],
        text_pos="below"
    )
    
    prompt = t("prompt_what_posting", lang)
    cancel_kb = get_cancel_inline_keyboard(lang, callback_data="cancel_creation")
    
    msg_target = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()
        
    await send_cached_banner(msg_target, "create", prompt, reply_markup=cancel_kb)

@router.callback_query(F.data == "cancel_creation", StateFilter("*"))
async def cb_cancel_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    await callback.answer(t("canceled", lang), show_alert=False)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    welcome_text = t("welcome", lang, bot_username=BOT_USERNAME or "bot")
    welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang)
    await send_cached_banner(callback.message, "welcome", welcome_text, reply_markup=welcome_inline_kb)

@router.callback_query(F.data == "back_to_post", StateFilter("*"))
async def cb_back_to_post(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.set_state(PostCreation.editing_post)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_post_preview(callback.message, state, lang)

@router.message(F.forward_origin != None)
async def handle_forwarded_post(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    content_type = "text"
    file_id = None
    text = ""
    entities = []
    
    if message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.animation:
        content_type = "animation"
        file_id = message.animation.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.document:
        content_type = "document"
        file_id = message.document.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.audio:
        content_type = "audio"
        file_id = message.audio.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.voice:
        content_type = "voice"
        file_id = message.voice.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.sticker:
        content_type = "sticker"
        file_id = message.sticker.file_id
        text = ""
    elif message.text:
        content_type = "text"
        text = message.text
        entities = message.entities or []
        
    entities_serialized = [e.model_dump(exclude_none=True) for e in entities] if entities else []
    
    if user_dict.get("auto_save_forwards"):
        post_code = generate_post_code()
        await create_post(
            post_code=post_code,
            user_id=user_id,
            name="Forwarded post",
            content_type=content_type,
            file_id=file_id,
            text=text,
            entities_json=json.dumps(entities_serialized),
            buttons_json="[]",
            text_position="below"
        )
        ready_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=False, lang=lang)
        await message.answer(f"🎉 Post saved! Code: @{BOT_USERNAME} {post_code}", reply_markup=ready_kb)
    else:
        await state.clear()
        await state.set_state(PostCreation.editing_post)
        await state.update_data(
            lang=lang,
            content_type=content_type,
            file_id=file_id,
            text=text,
            entities=entities_serialized,
            buttons=[],
            text_pos="below"
        )
        await send_post_preview(message, state, lang)

@router.message(PostCreation.waiting_for_content)
async def process_post_content(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if message.text and (message.text.lower() in CANCEL_TRIGGERS or "cancel" in message.text.lower()):
        await state.clear()
        welcome_text = t("welcome", lang, bot_username=BOT_USERNAME or "bot")
        welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang)
        await send_cached_banner(message, "welcome", welcome_text, reply_markup=welcome_inline_kb)
        return
        
    content_type = "text"
    file_id = None
    text = ""
    entities = []
    
    if message.photo:
        content_type = "photo"
        file_id = message.photo[-1].file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.animation:
        content_type = "animation"
        file_id = message.animation.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.document:
        content_type = "document"
        file_id = message.document.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.audio:
        content_type = "audio"
        file_id = message.audio.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.voice:
        content_type = "voice"
        file_id = message.voice.file_id
        text = message.caption or ""
        entities = message.caption_entities or []
    elif message.sticker:
        content_type = "sticker"
        file_id = message.sticker.file_id
        text = ""
    elif message.text:
        content_type = "text"
        text = message.text
        entities = message.entities or []
    else:
        await message.answer("Unsupported format. Send photo, video, document, audio or text.")
        return
        
    entities_serialized = [e.model_dump(exclude_none=True) for e in entities] if entities else []
    
    await state.update_data(
        content_type=content_type,
        file_id=file_id,
        text=text,
        entities=entities_serialized
    )
    
    await state.set_state(PostCreation.editing_post)
    await send_post_preview(message, state, lang)

@router.message(PostCreation.editing_post, F.text.lower().in_(ADD_TEXT_TRIGGERS) | F.text.lower().contains("text"))
@router.callback_query(F.data == "btn_add_text", StateFilter("*"))
async def prompt_add_text(event: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.set_state(PostCreation.waiting_for_text)
    
    msg_target = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()
        
    await msg_target.answer(
        t("prompt_send_text", lang),
        reply_markup=get_back_inline_keyboard(lang, callback_data="back_to_post")
    )

@router.message(PostCreation.waiting_for_text)
async def process_added_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    if message.text and (message.text.lower() in CANCEL_TRIGGERS or "back" in message.text.lower() or "cancel" in message.text.lower()):
        await state.set_state(PostCreation.editing_post)
        await send_post_preview(message, state, lang)
        return
        
    entities = message.entities or []
    entities_serialized = [e.model_dump(exclude_none=True) for e in entities] if entities else []
    
    await state.update_data(
        text=message.text,
        entities=entities_serialized
    )
    
    await state.set_state(PostCreation.editing_post)
    await send_post_preview(message, state, lang)

@router.message(PostCreation.editing_post, F.text.lower().in_(DRAFT_TRIGGERS) | F.text.lower().contains("draft"))
@router.callback_query(F.data == "btn_save_drafts", StateFilter("*"))
async def save_to_drafts(event: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_id = event.from_user.id
    
    post_code = generate_post_code()
    buttons_json = json.dumps(data.get("buttons", []))
    entities_json = json.dumps(data.get("entities", []))
    
    await create_post(
        post_code=post_code,
        user_id=user_id,
        name="Draft",
        content_type=data.get("content_type", "text"),
        file_id=data.get("file_id"),
        text=data.get("text", ""),
        entities_json=entities_json,
        buttons_json=buttons_json,
        text_position=data.get("text_pos", "below")
    )
    
    await state.clear()
    msg_target = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer("Post saved to drafts!", show_alert=True)
        try:
            await event.message.delete()
        except Exception:
            pass
            
    welcome_text = t("welcome", lang, bot_username=BOT_USERNAME or "bot")
    welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang)
    await send_cached_banner(msg_target, "welcome", welcome_text, reply_markup=welcome_inline_kb)

@router.message(PostCreation.editing_post, F.text.lower().in_(DONE_TRIGGERS) | F.text.lower().contains("done"))
@router.callback_query(F.data == "btn_done", StateFilter("*"))
async def prompt_post_done(event: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.set_state(PostCreation.waiting_for_post_name)
    
    msg_target = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()
        
    await msg_target.answer(
        t("prompt_post_name", lang),
        reply_markup=get_skip_cancel_inline_keyboard(lang)
    )

@router.callback_query(F.data == "skip_post_name", StateFilter("*"))
async def cb_skip_post_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_id = callback.from_user.id
    
    post_code = generate_post_code()
    buttons_json = json.dumps(data.get("buttons", []))
    entities_json = json.dumps(data.get("entities", []))
    
    await create_post(
        post_code=post_code,
        user_id=user_id,
        name=None,
        content_type=data.get("content_type", "text"),
        file_id=data.get("file_id"),
        text=data.get("text", ""),
        entities_json=entities_json,
        buttons_json=buttons_json,
        text_position=data.get("text_pos", "below")
    )
    
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    ready_text = t("post_ready_title", lang, bot_username=BOT_USERNAME or "bot", post_code=post_code)
    ready_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=False, lang=lang)
    await send_cached_banner(callback.message, "ready", ready_text, reply_markup=ready_kb)

@router.message(PostCreation.waiting_for_post_name)
async def finalize_post_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    user_id = message.from_user.id
    raw_text = (message.text or "").strip()
    
    if raw_text.lower() in CANCEL_TRIGGERS or "cancel" in raw_text.lower():
        await state.clear()
        welcome_text = t("welcome", lang, bot_username=BOT_USERNAME or "bot")
        welcome_inline_kb = get_welcome_inline_keyboard(BOT_USERNAME, lang)
        await send_cached_banner(message, "welcome", welcome_text, reply_markup=welcome_inline_kb)
        return
        
    post_name = None
    if raw_text.lower() not in SKIP_TRIGGERS and "skip" not in raw_text.lower() and raw_text:
        post_name = raw_text[:50]
        
    post_code = generate_post_code()
    buttons_json = json.dumps(data.get("buttons", []))
    entities_json = json.dumps(data.get("entities", []))
    
    await create_post(
        post_code=post_code,
        user_id=user_id,
        name=post_name,
        content_type=data.get("content_type", "text"),
        file_id=data.get("file_id"),
        text=data.get("text", ""),
        entities_json=entities_json,
        buttons_json=buttons_json,
        text_position=data.get("text_pos", "below")
    )
    
    await state.clear()
    
    ready_text = t("post_ready_title", lang, bot_username=BOT_USERNAME or "bot", post_code=post_code)
    ready_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=False, lang=lang)
    await send_cached_banner(message, "ready", ready_text, reply_markup=ready_kb)
