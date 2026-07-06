from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from telegram.keyboards import main_kb, cancel_kb
from telegram.states import SunForm
from services.weather import get_sun

def register(dp: Dispatcher):

    @dp.message(F.text == "🌅 Восход/закат")
    async def btn_sun(m: Message, state: FSMContext):
        await state.set_state(SunForm.city)
        await m.answer("🌅 Напиши город:", reply_markup=cancel_kb())

    @dp.message(SunForm.city)
    async def fsm_city(m: Message, state: FSMContext):
        await state.clear()
        await m.answer("⏳ Считаю...", reply_markup=main_kb())
        sun = await get_sun(m.text.strip())
        if not sun:
            await m.answer("❌ Город не найден. Попробуй по-английски."); return
        await m.answer(
            f"🌅 <b>{sun['name']}</b>, {sun['country']}\n"
            f"📅 {sun['date']}\n\n"
            f"🌄 Восход: <b>{sun['sunrise']}</b>\n"
            f"🌇 Закат:  <b>{sun['sunset']}</b>",
            parse_mode="HTML"
        )
