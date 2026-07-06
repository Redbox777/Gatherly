from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core import links_service
from core.events_service import get_event
from telegram.keyboards import main_kb, skip_kb, cancel_kb, inline
from telegram.states import LinkForm
from telegram.utils import safe_edit, cb_answer

def register(dp: Dispatcher):

    @dp.message(LinkForm.url)
    async def fsm_url(m: Message, state: FSMContext):
        await state.update_data(url=m.text.strip())
        await state.set_state(LinkForm.title)
        await m.answer("📝 Название ссылки? (или /skip)", reply_markup=skip_kb())

    @dp.message(LinkForm.title)
    async def fsm_title(m: Message, state: FSMContext):
        val = None if m.text=="/skip" else m.text
        data = await state.get_data()
        await state.clear()
        uname = m.from_user.username or f"user{m.from_user.id}"
        links_service.add_link(data['event_id'], m.from_user.id, uname, data['url'], val)
        await m.answer("✅ Ссылка добавлена!", reply_markup=main_kb())

    @dp.callback_query(F.data.startswith("links:view:"))
    async def cb_view(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        ev = get_event(eid)
        if not ev: return
        links = links_service.list_links(eid)
        if not links:
            await safe_edit(cb, f"🔗 <b>{ev['title']}</b>\n\nПока пусто.",
                reply_markup=inline(("➕ Добавить ссылку", f"links:add:{eid}"))); return
        lines = [f"🔗 <b>Ссылки: {ev['title']}</b>\n"]
        for lnk in links:
            title = lnk['title'] or lnk['url']
            lines.append(f"• <a href='{lnk['url']}'>{title}</a> (@{lnk['username']})")
        await safe_edit(cb, "\n".join(lines),
            reply_markup=inline(("➕ Добавить ссылку", f"links:add:{eid}")))

    @dp.callback_query(F.data.startswith("links:add:"))
    async def cb_add(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(LinkForm.url)
        await state.update_data(event_id=eid)
        await cb.message.answer("🔗 Вставь ссылку:", reply_markup=cancel_kb())
