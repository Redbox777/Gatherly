from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core import events_service
from core.event_parser import parse_event_message, format_example
from telegram.keyboards import main_kb, cancel_kb, inline, inline_grid
from telegram.states import EventForm
from telegram.utils import safe_edit, cb_answer, fmt_event

async def _notify(bot, user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
    except Exception:
        pass

def register(dp: Dispatcher):

    @dp.message(F.text == "📅 Встречи")
    async def btn_events(m: Message):
        await m.answer("📅 <b>Встречи</b>", parse_mode="HTML",
            reply_markup=inline(
                ("➕ Создать встречу", "events:new"),
                ("📋 Мои встречи",     "events:list"),
            ))

    @dp.message(Command("join"))
    async def cmd_join(m: Message):
        parts = (m.text or "").split()
        if len(parts) < 2 or not parts[1].isdigit():
            await m.answer("Использование: /join <ID встречи>"); return
        eid = int(parts[1])
        ok = events_service.join_event(eid, m.from_user.id, m.from_user.username)
        if not ok:
            await m.answer("❌ Встреча не найдена"); return
        ev = events_service.get_event(eid)

        notif = events_service.get_new_participant_notification(
            eid, m.from_user.id, m.from_user.username
        )
        if notif:
            await _notify(m.bot, notif['creator_id'], notif['text'])

        await m.answer(f"✅ Ты в встрече!\n\n" + fmt_event(ev),
            reply_markup=inline(
                ("✅ Иду", f"rsvp:{eid}:going"),
                ("🤔 Может", f"rsvp:{eid}:maybe"),
                ("❌ Не иду", f"rsvp:{eid}:no"),
            ), parse_mode="HTML")

    @dp.message(EventForm.all_in_one)
    async def fsm_all_in_one(m: Message, state: FSMContext):
        await state.clear()
        parsed = parse_event_message(m.text)

        if not parsed['title']:
            await m.answer(
                "❌ Не понял название встречи.\n\n" + format_example(),
                reply_markup=cancel_kb(), parse_mode="HTML"
            )
            await state.set_state(EventForm.all_in_one)
            return

        event_id = events_service.create_event(
            chat_id=m.chat.id,
            creator_id=m.from_user.id,
            creator_username=m.from_user.username,
            title=parsed['title'],
            date_str=parsed['date_str'],
            place=parsed['place'],
            note=parsed['note'],
            remind_at=parsed['remind_at'],
        )

        remind_txt = f"\n⏰ Напомню: {parsed['remind_at']}" if parsed['remind_at'] else ""
        await m.answer(
            f"✅ Встреча создана!\n\n📅 <b>{parsed['title']}</b>\n"
            f"ID: <code>{event_id}</code>{remind_txt}\n\n"
            f"Друзья: <code>/join {event_id}</code>",
            reply_markup=main_kb(), parse_mode="HTML"
        )

    @dp.callback_query(F.data == "events:new")
    async def cb_new(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        await state.set_state(EventForm.all_in_one)
        await cb.message.answer(format_example(),
            reply_markup=cancel_kb(), parse_mode="HTML")

    @dp.callback_query(F.data == "events:list")
    async def cb_list(cb: CallbackQuery):
        await cb_answer(cb)
        events = events_service.list_user_events(cb.from_user.id)
        if not events:
            await cb.message.answer("Встреч пока нет."); return
        await cb.message.answer("📋 <b>Твои встречи:</b>", parse_mode="HTML",
            reply_markup=inline_grid([(f"📅 {e['title']}", f"event:view:{e['id']}") for e in events], 1))

    @dp.callback_query(F.data.startswith("event:view:"))
    async def cb_view(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        ev = events_service.get_event(eid)
        if not ev: return
        parts = events_service.get_participants(eid)
        await safe_edit(cb, fmt_event(ev, parts),
            reply_markup=inline(
                ("✅ Иду",           f"rsvp:{eid}:going"),
                ("🤔 Может",        f"rsvp:{eid}:maybe"),
                ("❌ Не иду",       f"rsvp:{eid}:no"),
                ("📋 Чек-лист",     f"cl:event:{eid}"),
                ("🗳 Голосование",   f"poll:list:{eid}"),
                ("💰 Расходы",      f"exp:view:{eid}"),
                ("🗺 Маршрут",      f"route:list:{eid}"),
                ("🔗 Ссылки",       f"links:view:{eid}"),
                ("🔔 Уведомить всех", f"event:notify:{eid}"),
                ("🗑 Удалить",      f"event:del:{eid}"),
            ))

    @dp.callback_query(F.data.startswith("rsvp:"))
    async def cb_rsvp(cb: CallbackQuery):
        _, eid, status = cb.data.split(":")
        eid = int(eid)
        events_service.set_rsvp(eid, cb.from_user.id, cb.from_user.username, status)

        notif = events_service.get_rsvp_change_notification(
            eid, cb.from_user.id, cb.from_user.username, status
        )
        if notif:
            await _notify(cb.bot, notif['creator_id'], notif['text'])

        labels = {"going":"✅ Иду!", "maybe":"🤔 Может быть", "no":"❌ Не иду"}
        await cb_answer(cb, labels.get(status, "Сохранено"))

    @dp.callback_query(F.data.startswith("event:notify:"))
    async def cb_notify(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        uid = cb.from_user.id
        ev = events_service.get_event(eid)
        if not ev or ev['creator'] != uid:
            await cb_answer(cb, "Только создатель может отправить уведомление", alert=True); return

        recipient_ids = events_service.get_going_participant_ids(eid, exclude_user_id=uid)
        count = 0
        for recipient_id in recipient_ids:
            try:
                await cb.bot.send_message(
                    recipient_id,
                    f"🔔 <b>Напоминание от организатора!</b>\n\n"
                    f"Встреча <b>{ev['title']}</b>\n" +
                    (f"🗓 {ev['date_str']}\n" if ev['date_str'] else "") +
                    (f"📍 {ev['place']}" if ev['place'] else ""),
                    parse_mode="HTML"
                )
                count += 1
            except Exception:
                pass
        await cb.message.answer(f"✅ Уведомление отправлено {count} участникам.")

    @dp.callback_query(F.data.startswith("event:del:"))
    async def cb_del(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        ok = events_service.delete_event(eid, cb.from_user.id)
        if ok:
            try:
                await cb.message.edit_text("🗑 Встреча удалена.")
            except Exception:
                pass
        else:
            await cb_answer(cb, "Только создатель может удалить", alert=True)
