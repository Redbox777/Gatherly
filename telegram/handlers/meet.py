from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core import events_service, polls_service, routes_service, checklists_service, discussion_service
from core.event_parser import parse_event_message, format_example
from telegram.keyboards import main_kb, cancel_kb, inline, inline_grid
from telegram.states import EventForm, PollForm, RouteForm, ChecklistForm, DiscussionForm
from telegram.utils import safe_edit, cb_answer, fmt_event

async def _notify(bot, user_id, text):
    try:
        await bot.send_message(user_id, text)
    except Exception:
        pass

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

    @dp.message(F.text == "📅 Meet")
    async def btn_meet(m: Message):
        await m.answer("📅 <b>Meet</b>", parse_mode="HTML",
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
            chat_id=m.chat.id, creator_id=m.from_user.id,
            creator_username=m.from_user.username,
            title=parsed['title'], date_str=parsed['date_str'],
            place=parsed['place'], note=parsed['note'],
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
        msg_count = discussion_service.get_message_count(eid)
        discuss_label = f"💬 Обсуждение ({msg_count})" if msg_count else "💬 Обсуждение"
        await safe_edit(cb, fmt_event(ev, parts),
            reply_markup=inline(
                ("✅ Иду",           f"rsvp:{eid}:going"),
                ("🤔 Может",        f"rsvp:{eid}:maybe"),
                ("❌ Не иду",       f"rsvp:{eid}:no"),
                ("📋 Чек-лист",     f"cl:event:{eid}"),
                ("🗳 Голосование",   f"poll:list:{eid}"),
                ("🗺 Маршрут",      f"route:list:{eid}"),
                (discuss_label,     f"discuss:view:{eid}"),
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

    def _render_checklist(eid):
        ev = events_service.get_event(eid)
        if not ev: return None, None
        items = checklists_service.list_items(eid)
        lines = [f"{'✅' if i['done'] else '⬜'} {i['item']}" for i in items] or ["Список пуст"]
        btns  = [(f"{'☑' if i['done'] else '☐'} {i['item'][:18]}", f"cl:toggle:{i['id']}:{eid}") for i in items]
        btns.append(("➕ Добавить", f"cl:add:{eid}"))
        return f"✅ <b>{ev['title']}</b>\n\n" + "\n".join(lines), inline_grid(btns, 1)

    @dp.callback_query(F.data.startswith("cl:event:"))
    async def cb_cl_view(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        text, kb = _render_checklist(eid)
        if text: await safe_edit(cb, text, reply_markup=kb)

    @dp.callback_query(F.data.startswith("cl:toggle:"))
    async def cb_cl_toggle(cb: CallbackQuery):
        await cb_answer(cb)
        parts = cb.data.split(":")
        item_id, eid = int(parts[2]), int(parts[3])
        checklists_service.toggle_item(item_id)
        text, kb = _render_checklist(eid)
        if text: await safe_edit(cb, text, reply_markup=kb)

    @dp.callback_query(F.data.startswith("cl:add:"))
    async def cb_cl_add(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(ChecklistForm.item)
        await state.update_data(event_id=eid)
        await cb.message.answer("✅ Что добавить?", reply_markup=cancel_kb())

    @dp.message(ChecklistForm.item)
    async def fsm_cl_item(m: Message, state: FSMContext):
        data = await state.get_data()
        await state.clear()
        checklists_service.add_item(data.get('event_id'), m.from_user.id, m.text)
        await m.answer(f"✅ Добавлено: <b>{m.text}</b>", reply_markup=main_kb(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("poll:list:"))
    async def cb_poll_list(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        polls = polls_service.list_polls(eid)
        btns = [(f"🗳 {p['question'][:25]}", f"poll:view:{p['id']}") for p in polls]
        btns.append(("➕ Создать голосование", f"poll:new:{eid}"))
        await safe_edit(cb, "🗳 <b>Голосования</b>", reply_markup=inline_grid(btns, 1))

    @dp.callback_query(F.data.startswith("poll:new:"))
    async def cb_poll_new(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(PollForm.question)
        await state.update_data(event_id=eid)
        await cb.message.answer("🗳 Тема голосования:", reply_markup=cancel_kb())

    @dp.message(PollForm.question)
    async def fsm_poll_question(m: Message, state: FSMContext):
        await state.update_data(question=m.text)
        await state.set_state(PollForm.options)
        await m.answer(
            "📝 Варианты — каждый с новой строки:\n\n<code>Парк\nКафе\nКино</code>",
            reply_markup=cancel_kb(), parse_mode="HTML"
        )

    @dp.message(PollForm.options)
    async def fsm_poll_options(m: Message, state: FSMContext):
        options = [o.strip() for o in m.text.split("\n") if o.strip()]
        if len(options) < 2:
            await m.answer("Нужно минимум 2 варианта:"); return
        data = await state.get_data()
        await state.clear()
        poll_id = polls_service.create_poll(data['event_id'], data['question'], options)
        text, btns = _fmt_poll(poll_id)
        await m.answer(text, reply_markup=inline_grid(btns, 1) if btns else None, parse_mode="HTML")
        await m.answer("✅ Голосование создано!", reply_markup=main_kb())

    @dp.callback_query(F.data.startswith("poll:view:"))
    async def cb_poll_view(cb: CallbackQuery):
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

    @dp.callback_query(F.data.startswith("route:list:"))
    async def cb_route_list(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        routes = routes_service.list_routes(eid)
        btns = [(f"🗺 {r['title']}", f"route:view:{r['id']}") for r in routes]
        btns.append(("➕ Создать маршрут", f"route:new:{eid}"))
        await safe_edit(cb, "🗺 <b>Маршруты</b>", reply_markup=inline_grid(btns, 1))

    @dp.callback_query(F.data.startswith("route:new:"))
    async def cb_route_new(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(RouteForm.title)
        await state.update_data(event_id=eid)
        await cb.message.answer("🗺 Название маршрута:", reply_markup=cancel_kb())

    @dp.message(RouteForm.title)
    async def fsm_route_title(m: Message, state: FSMContext):
        await state.update_data(title=m.text)
        await state.set_state(RouteForm.points)
        await m.answer(
            "📍 Точки маршрута — каждая с новой строки:\n\n<code>Парковка\nПарк\nКафе</code>",
            reply_markup=cancel_kb(), parse_mode="HTML"
        )

    @dp.message(RouteForm.points)
    async def fsm_route_points(m: Message, state: FSMContext):
        points = [p.strip() for p in m.text.split("\n") if p.strip()]
        if not points:
            await m.answer("Напиши хотя бы одну точку:"); return
        data = await state.get_data()
        await state.clear()
        routes_service.create_route(data['event_id'], m.from_user.id, data['title'], points)
        lines = [f"🗺 <b>{data['title']}</b>\n"]
        for i, pt in enumerate(points, 1):
            lines.append(f"{i}. 📍 {pt}")
        await m.answer("\n".join(lines), reply_markup=main_kb(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("route:view:"))
    async def cb_route_view(cb: CallbackQuery):
        await cb_answer(cb)
        rid = int(cb.data.split(":")[2])
        data = routes_service.get_route_with_points(rid)
        if not data: return
        lines = [f"🗺 <b>{data['route']['title']}</b>\n"]
        for pt in data['points']:
            lines.append(f"{pt['order_num']}. 📍 {pt['name']}")
        await safe_edit(cb, "\n".join(lines))

    @dp.callback_query(F.data.startswith("discuss:view:"))
    async def cb_discuss_view(cb: CallbackQuery):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        ev = events_service.get_event(eid)
        if not ev: return
        messages = discussion_service.get_messages(eid, limit=20)
        if not messages:
            lines = [f"💬 <b>Обсуждение: {ev['title']}</b>\n", "Пока пусто. Напиши первое сообщение!"]
        else:
            lines = [f"💬 <b>Обсуждение: {ev['title']}</b>\n"]
            for msg in messages:
                name = msg['username'] or f"user{msg['user_id']}"
                lines.append(f"<b>{name}:</b> {msg['text']}")
        await cb.message.answer("\n".join(lines), parse_mode="HTML",
            reply_markup=inline(("✏️ Написать сообщение", f"discuss:write:{eid}")))

    @dp.callback_query(F.data.startswith("discuss:write:"))
    async def cb_discuss_write(cb: CallbackQuery, state: FSMContext):
        await cb_answer(cb)
        eid = int(cb.data.split(":")[2])
        await state.set_state(DiscussionForm.message)
        await state.update_data(event_id=eid)
        await cb.message.answer("💬 Напиши сообщение для обсуждения встречи:", reply_markup=cancel_kb())

    @dp.message(DiscussionForm.message)
    async def fsm_discuss_message(m: Message, state: FSMContext):
        data = await state.get_data()
        eid = data['event_id']
        await state.clear()

        uname = m.from_user.username or f"user{m.from_user.id}"
        discussion_service.add_message(eid, m.from_user.id, uname, m.text)

        recipient_ids = events_service.get_going_participant_ids(eid, exclude_user_id=m.from_user.id)
        ev = events_service.get_event(eid)
        for rid in recipient_ids:
            await _notify(
                m.bot, rid,
                f"💬 Новое сообщение в обсуждении «{ev['title']}»:\n{uname}: {m.text}"
            )

        await m.answer("✅ Сообщение отправлено в обсуждение!", reply_markup=main_kb())
