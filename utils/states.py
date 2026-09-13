from aiogram.fsm.state import State, StatesGroup

class AdminAddState(StatesGroup):
    waiting_for_user = State()
