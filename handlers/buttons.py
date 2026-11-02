import re
from typing import List, Dict, Any, Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from states import PostCreation
from locales.strings import t
from keyboards.inline import (
    build_inline_keyboard,
    get_buttons_menu_inline_keyboard,
    get_color_picker_inline_keyboard,
    get_button_builder_actions_inline_keyboard,
    get_back_inline_keyboard
)
from handlers.preview_helper import send_post_preview

router = Router(name="buttons_router")

def parse_buttons_text(text: str) -> List[List[Dict[str, Any]]]:
    rows = []
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        row_buttons = []
        raw_buttons = line.split("|")
        for raw_btn in raw_buttons:
            raw_btn = raw_btn.strip()
            if not raw_btn:
                continue
            parts = [p.strip() for p in re.split(r'\s*-\s*', raw_btn) if p.strip()]
            if len(parts) >= 2:
                btn_text = parts[0]
                btn_url = parts[1]
                color = parts[2].lower() if len(parts) >= 3 else None
                style = None
                if color in {"green", "success", "g"}:
                    style = "success"
                elif color in {"blue", "primary", "b"}:
                    style = "primary"
                elif color in {"red", "danger", "r"}:
                    style = "danger"
                row_buttons.append({"text": btn_text, "url": btn_url, "style": style})
        if row_buttons:
            rows.append(row_buttons)
    return rows

@router.callback_query(F.data == "btn_add_buttons", StateFilter("*"))
@router.message(PostCreation.editing_post, F.text.lower().contains("button"))
async def enter_button_mode(event: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    await state.set_state(PostCreation.waiting_for_buttons_text)
    
    prompt = t("prompt_buttons_instructions", lang)
    kb = get_buttons_menu_inline_keyboard(lang)
    
    msg_target = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.answer()
        try:
            await event.message.delete()
        except Exception:
            pass
            
    await msg_target.answer(prompt, reply_markup=kb)

@router.callback_query(F.data == "wizard_create_btn", StateFilter("*"))
async def start_wizard_create_btn(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    await state.update_data(append_mode="new_row")
    await state.set_state(PostCreation.btn_waiting_text)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        t("prompt_btn_text", lang),
        reply_markup=get_back_inline_keyboard(lang, callback_data="back_to_post")
    )

@router.callback_query(F.data == "wizard_add_row", StateFilter("*"))
async def start_wizard_add_row(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang", "en")
    
    await state.update_data(append_mode="same_row")
    await state.set_state(PostCreation.btn_waiting_text)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        t("prompt_btn_text", lang),
        reply_markup=get_back_inline_keyboard(lang, callback_data="back_to_post")
    )

@router.message(PostCreation.waiting_for_buttons_text)
async def handle_buttons_input(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    raw_text = (message.text or "").lower().strip()
    
    if "back" in raw_text or "cancel" in raw_text:
        await state.set_state(PostCreation.editing_post)
        await send_post_preview(message, state, lang)
        return
        
    if "create" in raw_text:
        await state.set_state(PostCreation.btn_waiting_text)
        await state.update_data(append_mode="new_row")
        await message.answer(
            t("prompt_btn_text", lang),
            reply_markup=get_back_inline_keyboard(lang, callback_data="back_to_post")
        )
        return
        
    parsed = parse_buttons_text(message.text or "")
    if not parsed:
        await message.answer(
            "Format error. Example:\nWebsite - https://example.com - blue\nChannel - @mychannel - green",
            reply_markup=get_buttons_menu_inline_keyboard(lang)
        )
        return
        
    await state.update_data(buttons=parsed)
    preview_kb = build_inline_keyboard(parsed)
    await state.set_state(PostCreation.btn_review)
    
    if preview_kb:
        await message.answer(t("btn_preview_header", lang), reply_markup=preview_kb)
    await message.answer(
        t("btn_ready_info", lang),
        reply_markup=get_button_builder_actions_inline_keyboard(lang)
    )

@router.message(PostCreation.btn_waiting_text)
async def wizard_step_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    raw_text = (message.text or "").lower().strip()
    
    if "back" in raw_text or "cancel" in raw_text:
        await state.set_state(PostCreation.editing_post)
        await send_post_preview(message, state, lang)
        return
        
    btn_text = (message.text or "").strip()
    await state.update_data(wizard_btn_text=btn_text)
    await state.set_state(PostCreation.btn_waiting_url)
    
    await message.answer(
        t("prompt_btn_url", lang),
        reply_markup=get_back_inline_keyboard(lang, callback_data="back_to_post")
    )

@router.message(PostCreation.btn_waiting_url)
async def wizard_step_url(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    raw_text = (message.text or "").lower().strip()
    
    if "back" in raw_text or "cancel" in raw_text:
        await state.set_state(PostCreation.editing_post)
        await send_post_preview(message, state, lang)
        return
        
    btn_url = (message.text or "").strip()
    await state.update_data(wizard_btn_url=btn_url)
    await state.set_state(PostCreation.btn_waiting_color)
    
    await message.answer(
        t("prompt_btn_color", lang),
        reply_markup=get_color_picker_inline_keyboard(lang)
    )

@router.callback_query(F.data.startswith("pick_color_"), StateFilter("*"))
async def wizard_step_color_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    lang = data.get("lang", "en")
    color_choice = callback.data.replace("pick_color_", "")
    
    style = None
    if color_choice == "green":
        style = "success"
    elif color_choice == "blue":
        style = "primary"
    elif color_choice == "red":
        style = "danger"
    else:
        style = None
        
    wizard_text = data.get("wizard_btn_text", "Button")
    wizard_url = data.get("wizard_btn_url", "https://t.me")
    append_mode = data.get("append_mode", "new_row")
    
    new_btn = {"text": wizard_text, "url": wizard_url, "style": style}
    buttons = data.get("buttons", [])
    
    if append_mode == "same_row" and buttons:
        buttons[-1].append(new_btn)
    else:
        buttons.append([new_btn])
        
    await state.update_data(buttons=buttons, append_mode="new_row")
    await state.set_state(PostCreation.btn_review)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    preview_kb = build_inline_keyboard(buttons)
    if preview_kb:
        await callback.message.answer(t("btn_preview_header", lang), reply_markup=preview_kb)
    await callback.message.answer(
        t("btn_ready_info", lang),
        reply_markup=get_button_builder_actions_inline_keyboard(lang)
    )

@router.message(PostCreation.btn_waiting_color)
async def wizard_step_color_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    raw_text = (message.text or "").lower().strip()
    
    if "back" in raw_text or "cancel" in raw_text:
        await state.set_state(PostCreation.editing_post)
        await send_post_preview(message, state, lang)
        return
        
    style = None
    if "green" in raw_text:
        style = "success"
    elif "blue" in raw_text:
        style = "primary"
    elif "red" in raw_text:
        style = "danger"
    else:
        style = None
        
    wizard_text = data.get("wizard_btn_text", "Button")
    wizard_url = data.get("wizard_btn_url", "https://t.me")
    append_mode = data.get("append_mode", "new_row")
    
    new_btn = {"text": wizard_text, "url": wizard_url, "style": style}
    buttons = data.get("buttons", [])
    
    if append_mode == "same_row" and buttons:
        buttons[-1].append(new_btn)
    else:
        buttons.append([new_btn])
        
    await state.update_data(buttons=buttons, append_mode="new_row")
    await state.set_state(PostCreation.btn_review)
    
    preview_kb = build_inline_keyboard(buttons)
    if preview_kb:
        await message.answer(t("btn_preview_header", lang), reply_markup=preview_kb)
    await message.answer(
        t("btn_ready_info", lang),
        reply_markup=get_button_builder_actions_inline_keyboard(lang)
    )

@router.callback_query(F.data == "wizard_save_buttons", StateFilter("*"))
async def wizard_save_buttons_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    await callback.answer(t("btn_ready_info", lang), show_alert=False)
    await state.set_state(PostCreation.editing_post)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_post_preview(callback.message, state, lang)

@router.message(PostCreation.btn_review)
async def handle_button_review(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    text = (message.text or "").lower().strip()
    
    if "row" in text:
        await state.update_data(append_mode="same_row")
        await state.set_state(PostCreation.btn_waiting_text)
        await message.answer(
            t("prompt_btn_text", lang),
            reply_markup=get_back_inline_keyboard(lang, callback_data="back_to_post")
        )
        return
        
    if "create" in text:
        await state.update_data(append_mode="new_row")
        await state.set_state(PostCreation.btn_waiting_text)
        await message.answer(
            t("prompt_btn_text", lang),
            reply_markup=get_back_inline_keyboard(lang, callback_data="back_to_post")
        )
        return
        
    if "save" in text or "back" in text:
        await state.set_state(PostCreation.editing_post)
        await send_post_preview(message, state, lang)
        return
        
    await message.answer(
        "Choose an action:",
        reply_markup=get_button_builder_actions_inline_keyboard(lang)
    )
