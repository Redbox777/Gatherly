from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core import places_service
from telegram.keyboards import main_kb, skip_kb, cancel_kb, inline
from telegram.states import PlaceForm
from telegram.utils import cb_answer

def register(dp: Dispatcher):

    @dp.message(F.text == "📍 Места")
    async def btn_places(m: Message):
        await m.answer("📍 <b>Места</b>", parse_mode="HTML",
            reply_markup=inline(
                ("➕ Сохранить место", "places:new"),
                ("📋 Мои места",       "places:list"),
            ))

    @dp.message(PlaceForm.name)
    async def fsm_name(m: Message, state: FSMContext):
        await state.update_data(name=m.text)
        await state.set_state(PlaceForm.note)
        await m.answer("📝 Заметка? (или /skip)", reply_markup=skip_kb())

    @dp.message(PlaceForm.note)
    async def fsm_note(m: Message, state: FSMContext):
        val = None if m.text=="/skip" else m.text
        data = await state.get_data()
        await state.clear()
        places_service.save_place(m.from_user.id, data['name'], val)
        await m.answer(f"✅ Место <b>{data['name']}</b> сохранено!",
            reply_markup=main_kb(), parse_mode="HTML")

    @dp.callback_query(F.data == "places:new")
    async def cb_new(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        await state.set_state(PlaceForm.name)
        await cb.message.answer("📍 Название или адрес:", reply_markup=cancel_kb())

    @dp.callback_query(F.data == "places:list")
    async def cb_list(cb: CallbackQuery):
        await cb_answer(cb)
        places = places_service.list_places(cb.from_user.id)
        if not places:
            await cb.message.answer("Мест пока нет."); return
        lines = [f"📍 <b>{p['name']}</b>" + (f"\n   {p['note']}" if p['note'] else "") for p in places]
        await cb.message.answer("\n\n".join(lines), parse_mode="HTML")
