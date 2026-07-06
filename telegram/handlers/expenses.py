from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core import expenses_service
from core.events_service import get_event
from telegram.keyboards import main_kb, skip_kb, cancel_kb, inline
from telegram.states import ExpenseForm
from telegram.utils import safe_edit, cb_answer, pick_event_kb

def register(dp: Dispatcher):

    @dp.message(F.text == "💰 Расходы")
    async def btn_expenses(m: Message):
        kb, events = pick_event_kb(m.from_user.id, "exp:view")
        if not events:
            await m.answer("Сначала создай встречу — нажми 📅 Встречи"); return
        await m.answer("💰 <b>Расходы</b>\nВыбери встречу:", parse_mode="HTML", reply_markup=kb)

    @dp.message(ExpenseForm.amount)
    async def fsm_amount(m: Message, state: FSMContext):
        try:
            amount = float(m.text.replace(",", "."))
        except ValueError:
            await m.answer("❌ Напиши сумму числом, например: 500"); return
        await state.update_data(amount=amount)
        await state.set_state(ExpenseForm.description)
        await m.answer("📝 За что? (или /skip)", reply_markup=skip_kb())

    @dp.message(ExpenseForm.description)
    async def fsm_desc(m: Message, state: FSMContext):
        val = None if m.text=="/skip" else m.text
        data = await state.get_data()
        await state.clear()
        uname = m.from_user.username or f"user{m.from_user.id}"
        expenses_service.add_expense(data['event_id'], m.from_user.id, uname, data['amount'], val)
        await m.answer(
            f"✅ Записано: <b>{data['amount']:.0f} ₽</b>" + (f" — {val}" if val else ""),
            reply_markup=main_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data.startswith("exp:view:"))
    async def cb_view(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        ev = get_event(eid)
        if not ev: return
        balance = expenses_service.calculate_balance(eid)
        if not balance['expenses']:
            await safe_edit(cb, f"💰 <b>{ev['title']}</b>\n\nПока пусто.",
                reply_markup=inline(("➕ Добавить", f"exp:add:{eid}"))); return

        lines = [f"💰 <b>{ev['title']}</b>\n"]
        for e in balance['expenses']:
            desc = f" — {e['description']}" if e['description'] else ""
            lines.append(f"• @{e['username']}: {e['amount']:.0f} ₽{desc}")
        lines.append(f"\n<b>Итого: {balance['total']:.0f} ₽</b>")
        lines.append(f"На человека: {balance['per_person']:.0f} ₽\n")
        lines.append("<b>Баланс:</b>")
        for name, info in balance['by_user'].items():
            diff = info['diff']
            if diff > 1:    lines.append(f"✅ @{name} переплатил {diff:.0f} ₽")
            elif diff < -1: lines.append(f"💸 @{name} должен {abs(diff):.0f} ₽")
            else:           lines.append(f"👌 @{name} в балансе")

        await safe_edit(cb, "\n".join(lines),
            reply_markup=inline(("➕ Добавить расход", f"exp:add:{eid}")))

    @dp.callback_query(F.data.startswith("exp:add:"))
    async def cb_add(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(ExpenseForm.amount)
        await state.update_data(event_id=eid)
        await cb.message.answer("💰 Сколько потратил? (в рублях):", reply_markup=cancel_kb())
