from aiogram.fsm.state import StatesGroup, State

class TransactionStates(StatesGroup):
    type = State()
    category = State()
    amount = State()
    date = State()
    cancel_id = State()