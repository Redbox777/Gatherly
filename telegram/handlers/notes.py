from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import notes_service, events_service
from telegram.keyboards import main_kb, cancel_kb, inline, inline_grid
from telegram.utils import safe_edit, cb_answer

class NoteForm(StatesGroup):
    text = State()
    attachment = State()

def _fmt_note(n):
    lines = [n['text']]
    if n.get('attachment_url'):
        lines.append(f"📎 {n['attachment_url']}")
    if n.get('is_shared'):
        lines.append("🌍 общая")
    return "\n".join(lines)

def register(dp: Dispatcher):

    @dp.message(F.text == "📝 Notes")
    async def btn_notes(m: Message):
        await m.answer("📝 <b>Notes</b>", parse_mode="HTML",
            reply_markup=inline(
                ("➕ Личная заметка", "notes:new:personal"),
                ("📋 Мои заметки",    "notes:list:personal"),
            ))

    @dp.callback_query(F.data == "notes:list:personal")
    async def cb_list_personal(cb: CallbackQuery):
        await cb_answer(cb)
        notes = notes_service.list_personal_notes(cb.from_user.id)
        if not notes:
            await cb.message.answer("📝 Личных заметок пока нет."); return
        lines = ["📝 <b>Твои заметки:</b>\n"]
        for n in notes:
            lines.append(f"• {_fmt_note(n)}")
        btns = [(f"🗑 Удалить #{n['id']}", f"notes:del:{n['id']}") for n in notes]
        await cb.message.answer("\n\n".join(lines), parse_mode="HTML",
            reply_markup=inline_grid(btns, 1) if btns else None)

    @dp.callback_query(F.data == "notes:new:personal")
    async def cb_new_personal(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        await state.set_state(NoteForm.text)
        await state.update_data(event_id=None, is_shared=False)
        await cb.message.answer("📝 Напиши текст заметки:", reply_markup=cancel_kb())

    @dp.callback_query(F.data.startswith("notes:event:"))
    async def cb_event_notes(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        ev = events_service.get_event(eid)
        if not ev: return
        notes = notes_service.list_event_notes(eid, cb.from_user.id)
        if not notes:
            lines = [f"📝 <b>Заметки: {ev['title']}</b>\n", "Пока пусто."]
        else:
            lines = [f"📝 <b>Заметки: {ev['title']}</b>\n"]
            for n in notes:
                mark = "🌍" if n['is_shared'] else "🔒"
                lines.append(f"{mark} {_fmt_note(n)}")
        await cb.message.answer("\n\n".join(lines), parse_mode="HTML",
            reply_markup=inline(
                ("➕ Личная заметка к встрече", f"notes:new:private:{eid}"),
                ("🌍 Общая заметка (видят все)", f"notes:new:shared:{eid}"),
            ))

    @dp.callback_query(F.data.startswith("notes:new:private:"))
    async def cb_new_private(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[3])
        await state.set_state(NoteForm.text)
        await state.update_data(event_id=eid, is_shared=False)
        await cb.message.answer("📝 Напиши текст личной заметки к встрече:", reply_markup=cancel_kb())

    @dp.callback_query(F.data.startswith("notes:new:shared:"))
    async def cb_new_shared(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[3])
        await state.set_state(NoteForm.text)
        await state.update_data(event_id=eid, is_shared=True)
        await cb.message.answer(
            "🌍 Напиши текст общей заметки (её увидят все участники встречи):",
            reply_markup=cancel_kb()
        )

    @dp.message(NoteForm.text)
    async def fsm_note_text(m: Message, state: FSMContext):
        await state.update_data(text=m.text)
        await state.set_state(NoteForm.attachment)
        await m.answer(
            "📎 Хочешь прикрепить ссылку или файл?\n"
            "Пришли ссылку текстом, или напиши /skip чтобы пропустить.",
            reply_markup=cancel_kb()
        )

    @dp.message(NoteForm.attachment)
    async def fsm_note_attachment(m: Message, state: FSMContext):
        data = await state.get_data()
        await state.clear()

        attachment_url = None if m.text == "/skip" else m.text.strip()

        notes_service.add_note(
            user_id=m.from_user.id,
            text=data['text'],
            event_id=data.get('event_id'),
            is_shared=data.get('is_shared', False),
            attachment_url=attachment_url,
        )

        label = "🌍 Общая заметка" if data.get('is_shared') else "📝 Заметка"
        await m.answer(f"✅ {label} сохранена!", reply_markup=main_kb())

    @dp.callback_query(F.data.startswith("notes:del:"))
    async def cb_delete(cb: CallbackQuery):
        note_id = int(cb.data.split(":")[2])
        ok = notes_service.delete_note(note_id, cb.from_user.id)
        if ok:
            await cb_answer(cb, "🗑 Удалено")
            try:
                await cb.message.edit_text("🗑 Заметка удалена.")
            except Exception:
                pass
        else:
            await cb_answer(cb, "Можно удалять только свои заметки", alert=True)
