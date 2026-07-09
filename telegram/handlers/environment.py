from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telegram.keyboards import main_kb, cancel_kb
from services.weather import get_weather, get_sun

class EnvironmentForm(StatesGroup):
    city = State()

def register(dp: Dispatcher):

    @dp.message(F.text == "🌤 Environment")
    async def btn_environment(m: Message, state: FSMContext):
        await state.set_state(EnvironmentForm.city)
        await m.answer("🌤 Напиши название города:", reply_markup=cancel_kb())

    @dp.message(EnvironmentForm.city)
    async def fsm_city(m: Message, state: FSMContext):
        await state.clear()
        city = m.text.strip()
        await m.answer("⏳ Собираю данные...", reply_markup=main_kb())

        w = await get_weather(city)
        s = await get_sun(city)

        if not w and not s:
            await m.answer("❌ Город не найден. Попробуй по-английски: Moscow")
            return

        lines = []
        if w:
            lines.append(f"🌤 <b>{w['name']}</b>, {w['country']}\n")
            lines.append(f"{w['desc']}")
            lines.append(f"🌡 {w['temp']}°C, ощущается {w['feels']}°C")
            lines.append(f"💨 Ветер {w['wind']} км/ч · 💧 {w['humidity']}%")
        else:
            lines.append(f"🌤 <b>{city}</b>\n")
            lines.append("Погода недоступна для этого города.")

        if s:
            lines.append("")
            lines.append(f"🌄 Восход: <b>{s['sunrise']}</b>")
            lines.append(f"🌇 Закат: <b>{s['sunset']}</b>")

        await m.answer("\n".join(lines), parse_mode="HTML")
