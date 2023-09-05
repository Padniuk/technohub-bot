from aiogram.fsm.state import StatesGroup, State


class ApplicationCreatingStates(StatesGroup):
    service_type = State()
    problem = State()
    name = State()
    contacts = State()
    address = State()

class WorkerStates(StatesGroup):
    name = State()
    phone = State()

class CancelStates(StatesGroup):
    application_id = State()
    comment = State()

class CompleteStates(StatesGroup):
    application_id = State()
    price = State()
    report = State()