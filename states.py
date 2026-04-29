from aiogram.fsm.state import StatesGroup, State

class TransactionStates(StatesGroup):
    type = State()
    category = State()
    custom_category = State()
    amount = State()
    date = State()
    cancel_id = State()
    report_from = State()
    report_to = State()