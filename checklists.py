from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core import checklists_service
from core.events_service import get_event
from telegram.keyboards import main_kb, cancel_kb, inline_grid
from telegram.states import ChecklistForm
from telegram.utils import safe_edit, cb_answer, pick_event_kb

def _render(event_id):
    ev = get_event(event_id)
    if not ev:
        return None, None
    items = checklists_service.list_items(event_id)
    lines = [f"{'✅' if i['done'] else '⬜'} {i['item']}" for i in items] or ["Список пуст"]
    btns  = [(f"{'☑' if i['done'] else '☐'} {i['item'][:18]}", f"cl:toggle:{i['id']}:{event_id}") for i in items]
    btns.append(("➕ Добавить", f"cl:add:{event_id}"))
    return f"✅ <b>{ev['title']}</b>\n\n" + "\n".join(lines), inline_grid(btns, 1)

def register(dp: Dispatcher):

    @dp.message(F.text == "✅ Чек-листы")
    async def btn_checklists(m: Message):
        kb, events = pick_event_kb(m.from_user.id, "cl:event")
        if not events:
            await m.answer("Сначала создай встречу — нажми 📅 Встречи"); return
        await m.answer("✅ <b>Чек-листы</b>\nВыбери встречу:", parse_mode="HTML", reply_markup=kb)

    @dp.message(ChecklistForm.item)
    async def fsm_item(m: Message, state: FSMContext):
        data = await state.get_data()
        await state.clear()
        checklists_service.add_item(data.get('event_id'), m.from_user.id, m.text)
        await m.answer(f"✅ Добавлено: <b>{m.text}</b>", reply_markup=main_kb(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("cl:event:"))
    async def cb_view(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        text, kb = _render(eid)
        if text: await safe_edit(cb, text, reply_markup=kb)

    @dp.callback_query(F.data.startswith("cl:toggle:"))
    async def cb_toggle(cb: CallbackQuery):
        await cb_answer(cb)
        parts = cb.data.split(":")
        item_id, eid = int(parts[2]), int(parts[3])
        checklists_service.toggle_item(item_id)
        text, kb = _render(eid)
        if text: await safe_edit(cb, text, reply_markup=kb)

    @dp.callback_query(F.data.startswith("cl:add:"))
    async def cb_add(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(ChecklistForm.item)
        await state.update_data(event_id=eid)
        await cb.message.answer("✅ Что добавить?", reply_markup=cancel_kb())
