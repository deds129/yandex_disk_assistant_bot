from aiogram.fsm.state import StatesGroup, State


class BotStates(StatesGroup):
    input_code = State()
    ready_to_work = State()
    change_save_dir = State()
