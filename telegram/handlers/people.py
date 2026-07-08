from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core import profiles_service, friends_service
from telegram.keyboards import main_kb, cancel_kb, inline

class ProfileForm(StatesGroup):
    name = State()
    city = State()
    timezone = State()
    interests = State()

class FriendForm(StatesGroup):
    search = State()

def _fmt_profile(p):
    if not p:
        return "👤 <b>Твой профиль</b>\n\nПока пусто. Заполни его!"
    lines = ["👤 <b>Твой профиль</b>\n"]
    lines.append(f"Имя: {p.get('name') or '—'}")
    lines.append(f"Город: {p.get('city') or '—'}")
    lines.append(f"Часовой пояс: {p.get('timezone') or '—'}")
    lines.append(f"Интересы: {p.get('interests') or '—'}")
    return "\n".join(lines)

def _friend_display_name(user_id):
    p = profiles_service.get_profile(user_id)
    if p and p.get('name'):
        return p['name']
    return f"user{user_id}"

def register(dp: Dispatcher):

    @dp.message(F.text == "👥 People")
    async def btn_people(m: Message):
        pending = friends_service.get_pending_requests(m.from_user.id)
        pending_txt = f" ({len(pending)})" if pending else ""
        await m.answer("👥 <b>People</b>", parse_mode="HTML",
            reply_markup=inline(
                ("👤 Мой профиль", "people:profile"),
                ("👫 Мои друзья", "people:friends"),
                (f"📨 Заявки{pending_txt}", "people:requests"),
                ("🔍 Найти человека", "people:search"),
            ))

    @dp.callback_query(F.data == "people:profile")
    async def cb_profile(cb: CallbackQuery):
        await cb.answer()
        p = profiles_service.get_profile(cb.from_user.id)
        await cb.message.answer(_fmt_profile(p), parse_mode="HTML",
            reply_markup=inline(
                ("✏️ Имя", "profile:edit:name"),
                ("🏙 Город", "profile:edit:city"),
                ("🕐 Часовой пояс", "profile:edit:timezone"),
                ("⭐ Интересы", "profile:edit:interests"),
            ))

    @dp.callback_query(F.data.startswith("profile:edit:"))
    async def cb_edit(cb: CallbackQuery, state: FSMContext):
        await cb.answer()
        field = cb.data.split(":")[2]
        prompts = {
            "name": "✏️ Напиши своё имя:",
            "city": "🏙 Напиши свой город:",
            "timezone": "🕐 Напиши часовой пояс (например: UTC+3 или Москва):",
            "interests": "⭐ Напиши свои интересы через запятую:",
        }
        states = {
            "name": ProfileForm.name, "city": ProfileForm.city,
            "timezone": ProfileForm.timezone, "interests": ProfileForm.interests,
        }
        await state.set_state(states[field])
        await cb.message.answer(prompts[field], reply_markup=cancel_kb())

    @dp.message(ProfileForm.name)
    async def fsm_name(m: Message, state: FSMContext):
        await state.clear()
        profiles_service.save_profile(m.from_user.id, name=m.text)
        await m.answer("✅ Имя сохранено!", reply_markup=main_kb())

    @dp.message(ProfileForm.city)
    async def fsm_city(m: Message, state: FSMContext):
        await state.clear()
        profiles_service.save_profile(m.from_user.id, city=m.text)
        await m.answer("✅ Город сохранён!", reply_markup=main_kb())

    @dp.message(ProfileForm.timezone)
    async def fsm_timezone(m: Message, state: FSMContext):
        await state.clear()
        profiles_service.save_profile(m.from_user.id, timezone=m.text)
        await m.answer("✅ Часовой пояс сохранён!", reply_markup=main_kb())

    @dp.message(ProfileForm.interests)
    async def fsm_interests(m: Message, state: FSMContext):
        await state.clear()
        profiles_service.save_profile(m.from_user.id, interests=m.text)
        await m.answer("✅ Интересы сохранены!", reply_markup=main_kb())

    @dp.callback_query(F.data == "people:friends")
    async def cb_friends_list(cb: CallbackQuery):
        await cb.answer()
        friend_ids = friends_service.get_friends_list(cb.from_user.id)
        if not friend_ids:
            await cb.message.answer(
                "👫 У тебя пока нет друзей.\n\nНайди кого-нибудь через «🔍 Найти человека»!"
            )
            return
        lines = ["👫 <b>Твои друзья:</b>\n"]
        for fid in friend_ids:
            lines.append(f"• {_friend_display_name(fid)}")
        await cb.message.answer("\n".join(lines), parse_mode="HTML")

    @dp.callback_query(F.data == "people:requests")
    async def cb_requests(cb: CallbackQuery):
        await cb.answer()
        pending = friends_service.get_pending_requests(cb.from_user.id)
        if not pending:
            await cb.message.answer("📨 Новых заявок нет.")
            return
        for req in pending:
            other_id = req['other_user_id']
            name = _friend_display_name(other_id)
            await cb.message.answer(
                f"📨 <b>{name}</b> хочет добавить тебя в друзья",
                parse_mode="HTML",
                reply_markup=inline(
                    ("✅ Принять", f"friend:accept:{req['requested_by']}:{cb.from_user.id}"),
                    ("❌ Отклонить", f"friend:decline:{req['requested_by']}:{cb.from_user.id}"),
                )
            )

    @dp.callback_query(F.data.startswith("friend:accept:"))
    async def cb_accept(cb: CallbackQuery):
        parts = cb.data.split(":")
        user_a, user_b = int(parts[2]), int(parts[3])
        ok = friends_service.respond_to_request(user_a, user_b, cb.from_user.id, accept=True)
        if ok:
            await cb.answer("✅ Заявка принята!")
            try:
                await cb.message.edit_text("✅ Вы теперь друзья!")
            except Exception:
                pass
            try:
                requester_id = user_a if user_a != cb.from_user.id else user_b
                await cb.bot.send_message(
                    requester_id,
                    f"🎉 {_friend_display_name(cb.from_user.id)} принял(а) твою заявку в друзья!"
                )
            except Exception:
                pass
        else:
            await cb.answer("Не удалось обработать заявку", show_alert=True)

    @dp.callback_query(F.data.startswith("friend:decline:"))
    async def cb_decline(cb: CallbackQuery):
        parts = cb.data.split(":")
        user_a, user_b = int(parts[2]), int(parts[3])
        ok = friends_service.respond_to_request(user_a, user_b, cb.from_user.id, accept=False)
        if ok:
            await cb.answer("Заявка отклонена")
            try:
                await cb.message.edit_text("❌ Заявка отклонена.")
            except Exception:
                pass
        else:
            await cb.answer("Не удалось обработать заявку", show_alert=True)

    @dp.callback_query(F.data == "people:search")
    async def cb_search(cb: CallbackQuery, state: FSMContext):
        await cb.answer()
        await state.set_state(FriendForm.search)
        await cb.message.answer(
            "🔍 Напиши username (@ivan123) или ID пользователя:",
            reply_markup=cancel_kb()
        )

    @dp.message(FriendForm.search)
    async def fsm_search(m: Message, state: FSMContext):
        await state.clear()
        query = m.text.strip()

        target_id = None
        if query.isdigit():
            target_id = int(query)
        elif query.startswith("@") or query.isalnum():
            target_id = friends_service.find_user_by_username(query)

        if not target_id:
            await m.answer(
                "❌ Не нашёл такого человека.\n\n"
                "Поиск по username работает только для тех, кто уже писал этому боту.",
                reply_markup=main_kb()
            )
            return

        name = _friend_display_name(target_id)
        await m.answer(
            f"Найден: <b>{name}</b>",
            parse_mode="HTML",
            reply_markup=inline(("➕ Отправить заявку в друзья", f"friend:request:{target_id}"))
        )

    @dp.callback_query(F.data.startswith("friend:request:"))
    async def cb_send_request(cb: CallbackQuery):
        await cb.answer()
        target_id = int(cb.data.split(":")[2])
        result = friends_service.send_friend_request(
            cb.from_user.id, cb.from_user.username, target_id
        )
        messages = {
            "sent": "✅ Заявка отправлена!",
            "already_friends": "Вы уже друзья.",
            "already_pending": "Заявка уже отправлена ранее.",
            "self": "Нельзя добавить самого себя.",
        }
        await cb.message.answer(messages.get(result, "Готово"))

        if result == "sent":
            try:
                await cb.bot.send_message(
                    target_id,
                    f"📨 {_friend_display_name(cb.from_user.id)} хочет добавить тебя в друзья!\n"
                    f"Загляни в 👥 People → 📨 Заявки"
                )
            except Exception:
                pass
