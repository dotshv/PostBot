import time
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramRetryAfter,
    TelegramAPIError
)

from config import is_admin, ADMIN_IDS
from database import get_all_user_ids, get_total_users_count
from states import BroadcastState
from keyboards.inline import get_cancel_inline_keyboard

router = Router(name="broadcast_router")

@router.message(Command("cast", "broadcast"), StateFilter("*"))
async def start_broadcast_command(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    if not ADMIN_IDS:
        await message.answer(
            f"Admin ID not configured in .env.\nAdd your Telegram ID to .env:\nADMIN_IDS={user_id}\nThen restart the bot."
        )
        return
        
    if not is_admin(user_id):
        await message.answer("Access Denied. Only administrators can use this command.")
        return
        
    total_users = await get_total_users_count()
    await state.set_state(BroadcastState.waiting_for_content)
    await state.update_data(admin_id=user_id, total_users=total_users)
    
    prompt = (
        "Broadcast Panel\n\n"
        f"Total Registered Users: {total_users}\n\n"
        "Send the message or media to broadcast.\n"
        "Supports text, photo, video, document, audio, voice, GIF, sticker and buttons.\n\n"
        "Send content now or click Cancel:"
    )
    
    cancel_kb = get_cancel_inline_keyboard("en", callback_data="cancel_broadcast")
    await message.answer(prompt, reply_markup=cancel_kb)

@router.message(BroadcastState.waiting_for_content)
async def process_broadcast_content(message: Message, state: FSMContext, bot: Bot):
    if message.text and ("cancel" in message.text.lower()):
        await state.clear()
        menu_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Menu", callback_data="back_to_menu", style="danger")]])
        await message.answer("Broadcast canceled.", reply_markup=menu_kb)
        return
        
    data = await state.get_data()
    total_users = data.get("total_users", 0)
    
    await state.update_data(broadcast_msg_id=message.message_id)
    await state.set_state(BroadcastState.confirm_send)
    
    await message.answer("Broadcast Preview:")
    
    try:
        await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        await message.answer(f"Preview error: {e}")
        
    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Confirm & Send to {total_users} Users",
                    callback_data="confirm_broadcast",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Cancel",
                    callback_data="cancel_broadcast",
                    style="danger"
                )
            ]
        ]
    )
    
    await message.answer(
        f"Confirm Broadcast:\nSend to {total_users} registered users?",
        reply_markup=confirm_kb
    )

@router.callback_query(F.data == "cancel_broadcast", StateFilter("*"))
async def cb_cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Broadcast canceled.")
    try:
        await callback.message.delete()
    except Exception:
        pass
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Menu", callback_data="back_to_menu", style="danger")]])
    await callback.message.answer("Broadcast canceled.", reply_markup=menu_kb)

@router.callback_query(F.data == "confirm_broadcast", StateFilter("*"))
async def cb_confirm_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    broadcast_msg_id = data.get("broadcast_msg_id")
    admin_id = callback.from_user.id
    
    await state.clear()
    
    if not broadcast_msg_id:
        await callback.answer("Broadcast message not found.", show_alert=True)
        return
        
    await callback.answer("Starting broadcast...")
    
    user_ids = await get_all_user_ids()
    total_users = len(user_ids)
    
    status_msg = await callback.message.answer(f"Broadcasting...\n0 / {total_users} (0%)")
    
    sent_count = 0
    blocked_count = 0
    start_time = time.time()
    last_update_time = time.time()
    
    for idx, uid in enumerate(user_ids, 1):
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=admin_id,
                message_id=broadcast_msg_id
            )
            sent_count += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(
                    chat_id=uid,
                    from_chat_id=admin_id,
                    message_id=broadcast_msg_id
                )
                sent_count += 1
            except Exception:
                blocked_count += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            blocked_count += 1
        except TelegramAPIError:
            blocked_count += 1
            
        await asyncio.sleep(0.04)
        
        current_time = time.time()
        if (current_time - last_update_time >= 3.0) or (idx == total_users):
            percent = int((idx / total_users) * 100) if total_users > 0 else 100
            try:
                await status_msg.edit_text(
                    f"Broadcasting...\n{idx} / {total_users} ({percent}%)\n\nDelivered: {sent_count}\nBlocked: {blocked_count}"
                )
                last_update_time = current_time
            except Exception:
                pass
                
    elapsed = time.time() - start_time
    summary = (
        "Broadcast Completed.\n\n"
        f"Total Users: {total_users}\n"
        f"Delivered: {sent_count}\n"
        f"Blocked: {blocked_count}\n"
        f"Duration: {elapsed:.1f}s"
    )
    
    try:
        await status_msg.edit_text(summary)
    except Exception:
        await callback.message.answer(summary)
        
    menu_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Menu", callback_data="back_to_menu", style="danger")]])
    await callback.message.answer("Broadcast finished.", reply_markup=menu_kb)
