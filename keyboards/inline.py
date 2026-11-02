from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any, Optional
from locales.strings import t, LANGUAGES

def normalize_url(link: str) -> str:
    link = link.strip()
    if link.startswith("@"):
        return f"https://t.me/{link.lstrip('@')}"
    if link.startswith("t.me/"):
        return f"https://{link}"
    if not (link.startswith("http://") or link.startswith("https://") or link.startswith("tg://")):
        return f"https://{link}"
    return link

def build_inline_keyboard(buttons_matrix: List[List[Dict[str, Any]]]) -> Optional[InlineKeyboardMarkup]:
    if not buttons_matrix:
        return None
        
    keyboard = []
    for row in buttons_matrix:
        kb_row = []
        for btn in row:
            text = btn.get("text", "Button")
            url = normalize_url(btn.get("url", "https://t.me"))
            style = btn.get("style")
            if style in {"primary", "success", "danger"}:
                kb_row.append(InlineKeyboardButton(text=text, url=url, style=style))
            else:
                kb_row.append(InlineKeyboardButton(text=text, url=url))
        if kb_row:
            keyboard.append(kb_row)
            
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None

def get_welcome_inline_keyboard(bot_username: str, lang: str = "en") -> InlineKeyboardMarkup:
    chan_url = f"https://t.me/{bot_username}?startchannel=botstart&admin=post_messages+edit_messages+delete_messages"
    group_url = f"https://t.me/{bot_username}?startgroup=botstart&admin=post_messages+delete_messages"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📝 {t('btn_create_post', lang)}",
                    callback_data="btn_create_post",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📁 {t('btn_my_posts', lang)}",
                    callback_data="btn_my_posts",
                    style="primary"
                ),
                InlineKeyboardButton(
                    text=f"👤 {t('btn_profile', lang)}",
                    callback_data="btn_profile",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"❤️ {t('btn_donate', lang)}",
                    callback_data="open_donate",
                    style="success"
                ),
                InlineKeyboardButton(
                    text=f"📖 {t('btn_help', lang)}",
                    callback_data="show_help",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🌐 {t('btn_language', lang)}",
                    callback_data="settings_lang",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Add to Channel",
                    url=chan_url,
                    style="primary"
                ),
                InlineKeyboardButton(
                    text="👥 Add to Group",
                    url=group_url,
                    style="primary"
                )
            ]
        ]
    )

def get_post_ready_keyboard(bot_username: str, post_code: str, is_favorite: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    fav_text = "Saved in Library" if is_favorite else t("btn_add_to_posts", lang)
    chan_url = f"https://t.me/{bot_username}?startchannel=botstart&admin=post_messages+edit_messages+delete_messages"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📢 {t('btn_post_to_channel', lang)}",
                    callback_data=f"sendchan:{post_code}",
                    style="success"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🔗 {t('btn_share', lang)}",
                    switch_inline_query=post_code,
                    style="primary"
                ),
                InlineKeyboardButton(
                    text="📢 Add to Channel",
                    url=chan_url,
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ {fav_text}",
                    callback_data=f"fav:{post_code}",
                    style="primary"
                ),
                InlineKeyboardButton(
                    text=f"✏️ {t('btn_custom_name', lang)}",
                    callback_data=f"rename:{post_code}",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🗑️ {t('btn_delete_post', lang)}",
                    callback_data=f"del:{post_code}",
                    style="danger"
                ),
                InlineKeyboardButton(
                    text="🏠 Menu",
                    callback_data="back_to_menu",
                    style="danger"
                )
            ]
        ]
    )

def get_profile_keyboard(user_settings: Dict[str, Any], lang: str = "en") -> InlineKeyboardMarkup:
    preview_status = "On" if user_settings.get("link_preview") else "Off"
    forwards_status = "On" if user_settings.get("auto_save_forwards") else "Off"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Language", callback_data="settings_lang", style="primary"),
                InlineKeyboardButton(text=f"🔗 Link Preview: {preview_status}", callback_data="toggle_preview", style="success")
            ],
            [
                InlineKeyboardButton(text=f"📥 Auto-save Forwards: {forwards_status}", callback_data="toggle_autoforwards", style="success")
            ],
            [
                InlineKeyboardButton(text="📖 Help", callback_data="show_help", style="primary"),
                InlineKeyboardButton(text="🏠 Menu", callback_data="back_to_menu", style="danger")
            ]
        ]
    )

def get_language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text=LANGUAGES["en"], callback_data="setlang_en", style="primary"),
            InlineKeyboardButton(text=LANGUAGES["hi"], callback_data="setlang_hi", style="success")
        ],
        [
            InlineKeyboardButton(text=LANGUAGES["ru"], callback_data="setlang_ru", style="primary"),
            InlineKeyboardButton(text=LANGUAGES["ur"], callback_data="setlang_ur", style="success")
        ],
        [
            InlineKeyboardButton(text=LANGUAGES["zh"], callback_data="setlang_zh", style="danger")
        ],
        [
            InlineKeyboardButton(text="🏠 Menu", callback_data="back_to_menu", style="danger")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_my_posts_keyboard(posts: List[Dict[str, Any]], page: int, total_posts: int, per_page: int = 5, lang: str = "en") -> InlineKeyboardMarkup:
    keyboard = []
    
    for p in posts:
        name = p.get("name") or p["post_code"]
        keyboard.append([
            InlineKeyboardButton(text=name[:18], callback_data=f"view:{p['post_code']}"),
            InlineKeyboardButton(text="Post", callback_data=f"sendchan:{p['post_code']}", style="success"),
            InlineKeyboardButton(text="Share", switch_inline_query=p['post_code'], style="primary"),
            InlineKeyboardButton(text="Delete", callback_data=f"del:{p['post_code']}", style="danger")
        ])
        
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="Previous", callback_data=f"myposts_page_{page-1}", style="primary"))
    
    total_pages = max(1, (total_posts + per_page - 1) // per_page)
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    
    if (page + 1) * per_page < total_posts:
        nav_row.append(InlineKeyboardButton(text="Next", callback_data=f"myposts_page_{page+1}", style="primary"))
        
    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([InlineKeyboardButton(text=f"📝 {t('btn_create_post', lang)}", callback_data="btn_create_post", style="success")])
    keyboard.append([InlineKeyboardButton(text="🏠 Menu", callback_data="back_to_menu", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_channel_post_keyboard(bot_username: str, saved_channels: List[Dict[str, Any]], post_code: str) -> InlineKeyboardMarkup:
    keyboard = []
    for ch in saved_channels:
        title = ch.get("channel_title") or ch["channel_id"]
        cid = ch["channel_id"]
        keyboard.append([
            InlineKeyboardButton(
                text=str(title)[:25],
                callback_data=f"postto:{cid}:{post_code}",
                style="success"
            )
        ])
    
    chan_url = f"https://t.me/{bot_username}?startchannel=botstart&admin=post_messages+edit_messages+delete_messages"
    keyboard.append([
        InlineKeyboardButton(text="📢 Add Bot to Channel", url=chan_url, style="primary")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Back to Post", callback_data=f"view:{post_code}", style="danger")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_donate_inline_keyboard(donate_url: str = "") -> InlineKeyboardMarkup:
    buttons = []
    if donate_url:
        buttons.append([InlineKeyboardButton(text="❤️ Donate Online", url=donate_url, style="success")])
    buttons.append([InlineKeyboardButton(text="🏠 Close", callback_data="close_donate", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_inline_keyboard(lang: str = "en", callback_data: str = "cancel_creation") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"❌ {t('btn_cancel', lang)}", callback_data=callback_data, style="danger")]
        ]
    )

def get_back_inline_keyboard(lang: str = "en", callback_data: str = "back_to_post") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔙 {t('btn_back_to_post', lang)}", callback_data=callback_data, style="danger")]
        ]
    )

def get_post_settings_inline_keyboard(lang: str = "en", has_text: bool = False, has_buttons: bool = False, text_pos: str = "below") -> InlineKeyboardMarkup:
    text_btn = t("btn_edit_text", lang) if has_text else t("btn_add_text", lang)
    btn_btn = t("btn_edit_buttons", lang) if has_buttons else t("btn_add_buttons", lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"✍️ {text_btn}", callback_data="btn_add_text", style="primary"),
                InlineKeyboardButton(text=f"🔘 {btn_btn}", callback_data="btn_add_buttons", style="primary")
            ],
            [
                InlineKeyboardButton(text=f"💾 {t('btn_save_drafts', lang)}", callback_data="btn_save_drafts", style="primary")
            ],
            [
                InlineKeyboardButton(text=f"✅ {t('btn_done', lang)}", callback_data="btn_done", style="success"),
                InlineKeyboardButton(text=f"❌ {t('btn_cancel', lang)}", callback_data="cancel_creation", style="danger")
            ]
        ]
    )

def get_buttons_menu_inline_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"➕ {t('btn_create_button_wizard', lang)}", callback_data="wizard_create_btn", style="success")],
            [InlineKeyboardButton(text=f"🔙 {t('btn_back_to_post', lang)}", callback_data="back_to_post", style="danger")]
        ]
    )

def get_color_picker_inline_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Green", callback_data="pick_color_green", style="success"),
                InlineKeyboardButton(text="🔵 Blue", callback_data="pick_color_blue", style="primary"),
                InlineKeyboardButton(text="🔴 Red", callback_data="pick_color_red", style="danger")
            ],
            [
                InlineKeyboardButton(text="⚪ No Color", callback_data="pick_color_none")
            ],
            [
                InlineKeyboardButton(text=f"🔙 {t('btn_back_to_post', lang)}", callback_data="back_to_post", style="danger")
            ]
        ]
    )

def get_button_builder_actions_inline_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"➕ {t('btn_add_to_row', lang)}", callback_data="wizard_add_row", style="primary")],
            [
                InlineKeyboardButton(text=f"➕ {t('btn_create_button_wizard', lang)}", callback_data="wizard_create_btn", style="primary"),
                InlineKeyboardButton(text=f"💾 {t('btn_save_buttons', lang)}", callback_data="wizard_save_buttons", style="success")
            ],
            [InlineKeyboardButton(text=f"🔙 {t('btn_back_to_post', lang)}", callback_data="back_to_post", style="danger")]
        ]
    )

def get_skip_cancel_inline_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"⏭️ {t('btn_skip', lang)}", callback_data="skip_post_name", style="primary"),
                InlineKeyboardButton(text=f"❌ {t('btn_cancel', lang)}", callback_data="cancel_creation", style="danger")
            ]
        ]
    )
