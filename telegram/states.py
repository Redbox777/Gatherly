from aiogram.fsm.state import State, StatesGroup

class EventForm(StatesGroup):
    all_in_one = State()

class PlaceForm(StatesGroup):
    name = State()
    note = State()

class ChecklistForm(StatesGroup):
    event_id = State()
    item = State()

class WeatherForm(StatesGroup):
    city = State()

class SunForm(StatesGroup):
    city = State()

class PollForm(StatesGroup):
    event_id = State()
    question = State()
    options = State()

class ExpenseForm(StatesGroup):
    event_id = State()
    amount = State()
    description = State()

class RouteForm(StatesGroup):
    event_id = State()
    title = State()
    points = State()

class LinkForm(StatesGroup):
    event_id = State()
    url = State()
    title = State()
