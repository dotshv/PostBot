from aiogram.fsm.state import State, StatesGroup

class PostCreation(StatesGroup):
    waiting_for_content = State()
    editing_post = State()
    waiting_for_text = State()
    waiting_for_buttons_text = State()
    btn_waiting_text = State()
    btn_waiting_url = State()
    btn_waiting_color = State()
    btn_review = State()
    waiting_for_post_name = State()

class PostRename(StatesGroup):
    waiting_for_new_name = State()

class ChannelPost(StatesGroup):
    waiting_for_channel = State()

class BroadcastState(StatesGroup):
    waiting_for_content = State()
    confirm_send = State()
