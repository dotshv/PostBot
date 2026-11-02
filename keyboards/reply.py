from aiogram.types import ReplyKeyboardRemove

def get_main_keyboard(lang: str = "en") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

def get_cancel_keyboard(lang: str = "en") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

def get_back_to_post_keyboard(lang: str = "en") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

def get_post_settings_keyboard(lang: str = "en", has_text: bool = False, has_buttons: bool = False, text_pos: str = "below") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

def get_buttons_menu_keyboard(lang: str = "en") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

def get_color_picker_keyboard(lang: str = "en") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

def get_button_builder_actions_keyboard(lang: str = "en") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()

def get_skip_cancel_keyboard(lang: str = "en") -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
