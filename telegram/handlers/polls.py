from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core import polls_service
from telegram.keyboards import main_kb, cancel_kb, inline_grid
from telegram.states import PollForm
from telegram.utils import safe_edit, cb_answer, pick_event_kb

def _fmt_poll(poll_id):
    result = polls_service.get_poll_results(poll_id)
    if not result:
        return None, None
    total = sum(o['votes'] for o in result['options']) or 1
    lines = [f"🗳 <b>{result['question']}</b>\n"]
    btns = []
    for o in result['options']:
        pct = round(o['votes'] / total * 100)
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(f"{o['text']}\n{bar} {pct}% ({o['votes']})")
        btns.append((o['text'], f"vote:{poll_id}:{o['id']}"))
    return "\n".join(lines), btns

def register(dp: Dispatcher):

    @dp.message(F.text == "🗳 Голосования")
    async def btn_polls(m: Message):
        kb, events = pick_event_kb(m.from_user.id, "poll:list")
        if not events:
            await m.answer("Сначала создай встречу — нажми 📅 Встречи"); return
        await m.answer("🗳 <b>Голосования</b>\nВыбери встречу:", parse_mode="HTML", reply_markup=kb)

    @dp.message(PollForm.question)
    async def fsm_question(m: Message, state: FSMContext):
        await state.update_data(question=m.text)
        await state.set_state(PollForm.options)
        await m.answer(
            "📝 Варианты — каждый с новой строки:\n\n<code>Парк\nКафе\nКино</code>",
            reply_markup=cancel_kb(), parse_mode="HTML"
        )

    @dp.message(PollForm.options)
    async def fsm_options(m: Message, state: FSMContext):
        options = [o.strip() for o in m.text.split("\n") if o.strip()]
        if len(options) < 2:
            await m.answer("Нужно минимум 2 варианта:"); return
        data = await state.get_data()
        await state.clear()
        poll_id = polls_service.create_poll(data['event_id'], data['question'], options)
        text, btns = _fmt_poll(poll_id)
        await m.answer(text, reply_markup=inline_grid(btns, 1) if btns else None, parse_mode="HTML")
        await m.answer("✅ Голосование создано!", reply_markup=main_kb())

    @dp.callback_query(F.data.startswith("poll:list:"))
    async def cb_list(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        polls = polls_service.list_polls(eid)
        btns = [(f"🗳 {p['question'][:25]}", f"poll:view:{p['id']}") for p in polls]
        btns.append(("➕ Создать голосование", f"poll:new:{eid}"))
        await safe_edit(cb, "🗳 <b>Голосования</b>", reply_markup=inline_grid(btns, 1))

    @dp.callback_query(F.data.startswith("poll:new:"))
    async def cb_new(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(PollForm.question)
        await state.update_data(event_id=eid)
        await cb.message.answer("🗳 Тема голосования:", reply_markup=cancel_kb())

    @dp.callback_query(F.data.startswith("poll:view:"))
    async def cb_view(cb: CallbackQuery):
        await cb_answer(cb)
        pid = int(cb.data.split(":")[2])
        text, btns = _fmt_poll(pid)
        if not text: return
        await safe_edit(cb, text, reply_markup=inline_grid(btns, 1) if btns else None)

    @dp.callback_query(F.data.startswith("vote:"))
    async def cb_vote(cb: CallbackQuery):
        _, pid, opt_id = cb.data.split(":")
        polls_service.cast_vote(int(pid), cb.from_user.id, int(opt_id))
        text, btns = _fmt_poll(int(pid))
        await safe_edit(cb, text, reply_markup=inline_grid(btns, 1) if btns else None)
        await cb_answer(cb, "✅ Голос принят!")
