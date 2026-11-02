import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME
from database import (
    get_or_create_user,
    get_user_posts,
    count_user_posts,
    get_post_by_code,
    delete_post,
    toggle_favorite,
    update_post_name
)
from keyboards.inline import (
    get_my_posts_keyboard,
    get_post_ready_keyboard,
    build_inline_keyboard,
    get_cancel_inline_keyboard
)
from locales.strings import t, get_button_variants
from states import PostRename
from handlers.preview_helper import remove_reply_keyboard

router = Router(name="my_posts_router")

MY_POSTS_TRIGGERS = get_button_variants("btn_my_posts", ["my posts", "posts", "my post", "/posts"])

@router.callback_query(F.data == "btn_my_posts", StateFilter("*"))
@router.message(F.text.lower().in_(MY_POSTS_TRIGGERS) | F.text.lower().contains("my post") | F.text.lower().contains("posts"), StateFilter("*"))
async def view_my_posts(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    if isinstance(event, Message):
        await remove_reply_keyboard(event)
        
    user_id = event.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    total = await count_user_posts(user_id)
    posts = await get_user_posts(user_id, limit=5, offset=0)
    
    msg_target = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()
        
    kb = get_my_posts_keyboard(posts, page=0, total_posts=total, per_page=5, lang=lang)
    header = f"Your Saved Posts ({total}):" if posts else "No saved posts yet. Click Create Post below to create one."
    
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(header, reply_markup=kb)
            return
        except Exception:
            try:
                await event.message.delete()
            except Exception:
                pass
                
    await msg_target.answer(header, reply_markup=kb)

@router.callback_query(F.data.startswith("myposts_page_"), StateFilter("*"))
async def paginate_my_posts(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user = await get_or_create_user(user_id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    page = int(callback.data.split("_")[-1])
    total = await count_user_posts(user_id)
    posts = await get_user_posts(user_id, limit=5, offset=page * 5)
    
    kb = get_my_posts_keyboard(posts, page=page, total_posts=total, per_page=5, lang=lang)
    try:
        await callback.message.edit_text(
            f"Your Saved Posts ({total}):",
            reply_markup=kb
        )
    except Exception:
        pass

@router.callback_query(F.data == "noop", StateFilter("*"))
async def cb_noop(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(F.data.startswith("view:"), StateFilter("*"))
async def preview_saved_post(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    post_code = callback.data.split(":", 1)[1]
    post = await get_post_by_code(post_code)
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    if not post:
        await callback.answer("Post not found.", show_alert=True)
        return
        
    buttons_data = json.loads(post["buttons_json"]) if post.get("buttons_json") else []
    inline_kb = build_inline_keyboard(buttons_data)
    
    c_type = post.get("content_type", "text")
    file_id = post.get("file_id")
    caption = post.get("text") or ""
    text_pos = post.get("text_position", "below")
    show_above = (text_pos == "above")
    
    if c_type == "photo" and file_id:
        await callback.message.answer_photo(photo=file_id, caption=caption or None, show_caption_above_media=show_above, reply_markup=inline_kb)
    elif c_type == "video" and file_id:
        await callback.message.answer_video(video=file_id, caption=caption or None, show_caption_above_media=show_above, reply_markup=inline_kb)
    elif c_type == "animation" and file_id:
        await callback.message.answer_animation(animation=file_id, caption=caption or None, show_caption_above_media=show_above, reply_markup=inline_kb)
    elif c_type == "document" and file_id:
        await callback.message.answer_document(document=file_id, caption=caption or None, reply_markup=inline_kb)
    elif c_type == "audio" and file_id:
        await callback.message.answer_audio(audio=file_id, caption=caption or None, reply_markup=inline_kb)
    elif c_type == "voice" and file_id:
        await callback.message.answer_voice(voice=file_id, caption=caption or None, reply_markup=inline_kb)
    else:
        await callback.message.answer(text=caption or f"Post: {post_code}", reply_markup=inline_kb)
        
    action_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=bool(post.get("is_favorite")), lang=lang)
    await callback.message.answer(
        f"Post: {post.get('name') or post_code}\nCode: @{BOT_USERNAME} {post_code}",
        reply_markup=action_kb
    )

@router.callback_query(F.data.startswith("fav:"), StateFilter("*"))
async def handle_toggle_fav(callback: CallbackQuery):
    post_code = callback.data.split(":", 1)[1]
    is_fav = await toggle_favorite(post_code, callback.from_user.id)
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    new_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=is_fav, lang=lang)
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except Exception:
        pass
        
    msg = "Saved to library." if is_fav else "Removed from library."
    await callback.answer(msg)

@router.callback_query(F.data.startswith("rename:"), StateFilter("*"))
async def start_rename_post(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    post_code = callback.data.split(":", 1)[1]
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    await state.set_state(PostRename.waiting_for_new_name)
    await state.update_data(rename_post_code=post_code, lang=lang)
    
    await callback.message.answer(
        "Enter new name for this post (max 50 chars):",
        reply_markup=get_cancel_inline_keyboard(lang, callback_data="cancel_rename")
    )

@router.callback_query(F.data == "cancel_rename", StateFilter("*"))
async def cb_cancel_rename(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    post_code = data.get("rename_post_code")
    await state.clear()
    await callback.answer("Canceled.")
    try:
        await callback.message.delete()
    except Exception:
        pass
    if post_code:
        ready_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=False, lang=lang)
        await callback.message.answer(f"Post: {post_code}", reply_markup=ready_kb)

@router.message(PostRename.waiting_for_new_name)
async def process_rename_post(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    post_code = data.get("rename_post_code")
    raw = (message.text or "").strip()
    
    if "cancel" in raw.lower():
        await state.clear()
        if post_code:
            ready_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=False, lang=lang)
            await message.answer(t("canceled", lang), reply_markup=ready_kb)
        else:
            await message.answer(t("canceled", lang))
        return
        
    new_name = raw[:50]
    await update_post_name(post_code, message.from_user.id, new_name)
    await state.clear()
    
    ready_kb = get_post_ready_keyboard(BOT_USERNAME, post_code, is_favorite=False, lang=lang)
    await message.answer(
        t("post_renamed", lang, name=new_name),
        reply_markup=ready_kb
    )

@router.callback_query(F.data.startswith("del:"), StateFilter("*"))
async def handle_delete_post(callback: CallbackQuery):
    post_code = callback.data.split(":", 1)[1]
    success = await delete_post(post_code, callback.from_user.id)
    user = await get_or_create_user(callback.from_user.id)
    user_dict = user[0] if isinstance(user, tuple) else user
    lang = user_dict.get("language", "en")
    
    if success:
        await callback.answer(t("post_deleted", lang), show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
    else:
        await callback.answer("Could not delete post.", show_alert=True)
