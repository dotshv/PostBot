import json
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedPhoto,
    InlineQueryResultCachedVideo,
    InlineQueryResultCachedGif,
    InlineQueryResultCachedDocument,
    InlineQueryResultCachedAudio,
    InlineQueryResultCachedVoice,
    InlineQueryResultCachedSticker,
    InputTextMessageContent
)

from database import get_post_by_code, get_user_posts
from keyboards.inline import build_inline_keyboard

router = Router(name="inline_query_router")

@router.inline_query()
async def handle_inline_query(query: InlineQuery):
    raw_query = query.query.strip()
    user_id = query.from_user.id
    results = []

    if raw_query:
        post = await get_post_by_code(raw_query)
        if post:
            res = build_inline_result(post)
            if res:
                results.append(res)
        else:
            results.append(
                InlineQueryResultArticle(
                    id="not_found",
                    title="Post not found",
                    description=f"No post found for code: {raw_query}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"Post not found for ID: {raw_query}"
                    )
                )
            )
    else:
        user_posts = await get_user_posts(user_id=user_id, limit=10, offset=0)
        for post in user_posts:
            res = build_inline_result(post)
            if res:
                results.append(res)
                
        if not results:
            results.append(
                InlineQueryResultArticle(
                    id="empty_posts",
                    title="No saved posts yet",
                    description="Open the bot to create your first post template",
                    input_message_content=InputTextMessageContent(
                        message_text="Create posts with buttons using PostBot."
                    )
                )
            )

    await query.answer(results=results, cache_time=1, is_personal=True)

def build_inline_result(post: dict):
    post_code = post["post_code"]
    name = post.get("name") or post_code
    c_type = post.get("content_type", "text")
    file_id = post.get("file_id")
    text = post.get("text") or ""
    text_pos = post.get("text_position", "below")
    show_above = (text_pos == "above")
    
    buttons_data = json.loads(post["buttons_json"]) if post.get("buttons_json") else []
    reply_markup = build_inline_keyboard(buttons_data) if buttons_data else None

    try:
        if c_type == "photo" and file_id:
            return InlineQueryResultCachedPhoto(
                id=post_code,
                photo_file_id=file_id,
                title=name,
                caption=text or None,
                show_caption_above_media=show_above,
                reply_markup=reply_markup
            )
        elif c_type == "video" and file_id:
            return InlineQueryResultCachedVideo(
                id=post_code,
                video_file_id=file_id,
                title=name,
                caption=text or None,
                show_caption_above_media=show_above,
                reply_markup=reply_markup
            )
        elif c_type == "animation" and file_id:
            return InlineQueryResultCachedGif(
                id=post_code,
                gif_file_id=file_id,
                title=name,
                caption=text or None,
                show_caption_above_media=show_above,
                reply_markup=reply_markup
            )
        elif c_type == "document" and file_id:
            return InlineQueryResultCachedDocument(
                id=post_code,
                document_file_id=file_id,
                title=name,
                caption=text or None,
                reply_markup=reply_markup
            )
        elif c_type == "audio" and file_id:
            return InlineQueryResultCachedAudio(
                id=post_code,
                audio_file_id=file_id,
                caption=text or None,
                reply_markup=reply_markup
            )
        elif c_type == "voice" and file_id:
            return InlineQueryResultCachedVoice(
                id=post_code,
                voice_file_id=file_id,
                title=name,
                caption=text or None,
                reply_markup=reply_markup
            )
        elif c_type == "sticker" and file_id:
            return InlineQueryResultCachedSticker(
                id=post_code,
                sticker_file_id=file_id,
                reply_markup=reply_markup
            )
        else:
            return InlineQueryResultArticle(
                id=post_code,
                title=name,
                description=text[:80] if text else "Text post",
                input_message_content=InputTextMessageContent(
                    message_text=text or f"Post: {name}"
                ),
                reply_markup=reply_markup
            )
    except Exception:
        return None
