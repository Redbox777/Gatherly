	from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from telegram.keyboards import main_kb, cancel_kb
from telegram.states import WeatherForm
from services.weather import get_weather

def register(dp: Dispatcher):

    @dp.message(F.text == "🌤 Погода")
    async def btn_weather(m: Message, state: FSMContext):
        await state.set_state(WeatherForm.city)
        await m.answer("🌤 Напиши название города:", reply_markup=cancel_kb())

    @dp.message(WeatherForm.city)
    async def fsm_city(m: Message, state: FSMContext):
        await state.clear()
        await m.answer("⏳ Получаю погоду...", reply_markup=main_kb())
        w = await get_weather(m.text.strip())
        if not w:
            await m.answer("❌ Город не найден. Попробуй по-английски: Moscow"); return
        await m.answer(
            f"🌤 <b>{w['name']}</b>, {w['country']}\n\n"
            f"{w['desc']}\n"
            f"🌡 {w['temp']}°C, ощущается {w['feels']}°C\n"
            f"💨 Ветер {w['wind']} км/ч · 💧 {w['humidity']}%",
            parse_mode="HTML"
        )
