from aiogram.fsm.state import State, StatesGroup

class AddAdmin(StatesGroup):
    waiting_user = State()

class AddChannel(StatesGroup):
    waiting_channel = State()

class AddContent(StatesGroup):
    waiting_message = State()
    waiting_title = State()

class AttachContent(StatesGroup):
    waiting_content = State()
    waiting_channel = State()

class AssignChannel(StatesGroup):
    waiting_admin = State()

class Broadcast(StatesGroup):
    waiting_message = State()

class AdminContent(StatesGroup):
    waiting_message = State()
    waiting_title = State()

class AdminBroadcast(StatesGroup):
    waiting_message = State()
