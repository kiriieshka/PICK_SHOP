from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    waiting_full_name = State()
    waiting_address = State()
