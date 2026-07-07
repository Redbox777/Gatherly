from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                            InlineKeyboardMarkup, InlineKeyboardButton)

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Встречи"),    KeyboardButton(text="📍 Места")],
            [KeyboardButton(text="✅ Чек-листы"),  KeyboardButton(text="🌤 Погода")],
            [KeyboardButton(text="🗳 Голосования"), KeyboardButton(text="💰 Расходы")],
            [KeyboardButton(text="🗺 Маршруты"),   KeyboardButton(text="🌅 Восход/закат")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True, persistent=True
    )

def skip_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/skip"), KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def inline(*buttons):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d)] for t, d in buttons]
    )

def inline_grid(buttons, cols=2):
    rows, row = [], []
    for t, d in buttons:
        row.append(InlineKeyboardButton(text=t, callback_data=d))
        if len(row) == cols:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)
