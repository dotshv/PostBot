import json
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from config import BOT_USERNAME
from database import (
    get_or_create_user,
    get_post_by_code,
    get_user_channels,
    add_user_channel
)
from states import ChannelPost
from keyboards.inline import build_inline_keyboard, get_channel_post_keyboard, get_post_ready_keyboard, get_cancel_inline_keyboard
from locales.strings import t

router = Router(name="channel_post_router")

@router.callback_query(F.data.startswith("sendchan:"), StateFilter("*"))
async def prompt_channel_target(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    post_code = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    post = await get_post_by_code(post_code)
    if not post:
        await callback.answer("Post not found.", show_alert=True)
        return
        
    await state.set_state(ChannelPost.waiting_for_channel)
    await state.update_data(target_post_code=post_code, lang=lang)
    
    saved_channels = await get_user_channels(user_id)
    kb = get_channel_post_keyboard(BOT_USERNAME, saved_channels, post_code)
    prompt_text = t("prompt_send_channel", lang, bot_username=BOT_USERNAME or "bot")
    
    await callback.message.answer(prompt_text, reply_markup=kb)

@router.callback_query(F.data.startswith("postto:"), StateFilter("*"))
async def handle_quick_post_to_channel(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await callback.answer("Publishing...")
    parts = callback.data.split(":", 2)
    channel_id = parts[1]
    post_code = parts[2]
    
    await execute_channel_post(bot, callback.from_user.id, channel_id, post_code, callback)

@router.message(ChannelPost.waiting_for_channel)
async def handle_channel_input(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "en")
    post_code = data.get("target_post_code")
    raw = (message.text or "").strip()
    
    if "cancel" in raw.lower():
        await state.clear()
        if post_code:
            ready_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=False, lang=lang)
            await message.answer(t("canceled", lang), reply_markup=ready_kb)
        else:
            await message.answer(t("canceled", lang))
        return
        
    if not raw.startswith("@") and not raw.startswith("-100") and not raw.startswith("-"):
        channel_id = f"@{raw}"
    else:
        channel_id = raw
        
    await state.clear()
    await execute_channel_post(bot, message.from_user.id, channel_id, post_code, message)

async def execute_channel_post(bot: Bot, user_id: int, channel_target: str, post_code: str, event: Message | CallbackQuery):
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    target_msg = event if isinstance(event, Message) else event.message
    post = await get_post_by_code(post_code)
    
    if not post:
        await target_msg.answer("Post not found.")
        return
        
    buttons_data = json.loads(post["buttons_json"]) if post.get("buttons_json") else []
    reply_markup = build_inline_keyboard(buttons_data)
    
    c_type = post.get("content_type", "text")
    file_id = post.get("file_id")
    caption = post.get("text") or ""
    text_pos = post.get("text_position", "below")
    show_above = (text_pos == "above")
    
    try:
        sent_msg = None
        if c_type == "photo" and file_id:
            sent_msg = await bot.send_photo(chat_id=channel_target, photo=file_id, caption=caption or None, show_caption_above_media=show_above, reply_markup=reply_markup)
        elif c_type == "video" and file_id:
            sent_msg = await bot.send_video(chat_id=channel_target, video=file_id, caption=caption or None, show_caption_above_media=show_above, reply_markup=reply_markup)
        elif c_type == "animation" and file_id:
            sent_msg = await bot.send_animation(chat_id=channel_target, animation=file_id, caption=caption or None, show_caption_above_media=show_above, reply_markup=reply_markup)
        elif c_type == "document" and file_id:
            sent_msg = await bot.send_document(chat_id=channel_target, document=file_id, caption=caption or None, reply_markup=reply_markup)
        elif c_type == "audio" and file_id:
            sent_msg = await bot.send_audio(chat_id=channel_target, audio=file_id, caption=caption or None, reply_markup=reply_markup)
        elif c_type == "voice" and file_id:
            sent_msg = await bot.send_voice(chat_id=channel_target, voice=file_id, caption=caption or None, reply_markup=reply_markup)
        elif c_type == "sticker" and file_id:
            sent_msg = await bot.send_sticker(chat_id=channel_target, sticker=file_id)
            if caption or reply_markup:
                await bot.send_message(chat_id=channel_target, text=caption or "Post", reply_markup=reply_markup)
        else:
            sent_msg = await bot.send_message(chat_id=channel_target, text=caption or f"Post: {post_code}", reply_markup=reply_markup)

        channel_title = channel_target
        try:
            chat_info = await bot.get_chat(channel_target)
            if chat_info and chat_info.title:
                channel_title = chat_info.title
        except Exception:
            pass
            
        await add_user_channel(user_id, channel_target, channel_title)
        success_text = t("channel_success", lang, channel=channel_title)
        
        if isinstance(event, CallbackQuery):
            try:
                await event.answer(success_text, show_alert=True)
            except Exception:
                pass
                
        action_buttons = []
        if str(channel_target).startswith("@"):
            chan_username = channel_target.lstrip("@")
            msg_link = f"https://t.me/{chan_username}/{sent_msg.message_id}" if sent_msg else f"https://t.me/{chan_username}"
            action_buttons.append([InlineKeyboardButton(text="View Post", url=msg_link, style="success")])
            
        action_buttons.append([InlineKeyboardButton(text="Menu", callback_data="back_to_menu", style="danger")])
        
        await target_msg.answer(
            success_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=action_buttons)
        )
        
    except TelegramAPIError as e:
        error_text = t("channel_error", lang, channel=channel_target, bot_username=BOT_USERNAME or "bot")
        if isinstance(event, CallbackQuery):
            try:
                await event.answer(error_text, show_alert=True)
            except Exception:
                pass
        chan_url = f"https://t.me/{BOT_USERNAME}?startchannel=botstart&admin=post_messages+edit_messages+delete_messages"
        err_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Add to Channel", url=chan_url, style="primary")],
                [InlineKeyboardButton(text="Try Again", callback_data=f"sendchan:{post_code}", style="success")],
                [InlineKeyboardButton(text="Menu", callback_data="back_to_menu", style="danger")]
            ]
        )
        await target_msg.answer(f"{error_text}\n\nDetails: {e}", reply_markup=err_kb)
