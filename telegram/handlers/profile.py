from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core import profiles_service
from telegram.keyboards import main_kb, cancel_kb, inline

class ProfileForm(StatesGroup):
    name = State()
    city = State()
    timezone = State()
    interests = State()

def _fmt_profile(p):
    if not p:
        return "👤 <b>Твой профиль</b>\n\nПока пусто. Заполни его!"
    lines = ["👤 <b>Твой профиль</b>\n"]
    lines.append(f"Имя: {p.get('name') or '—'}")
    lines.append(f"Город: {p.get('city') or '—'}")
    lines.append(f"Часовой пояс: {p.get('timezone') or '—'}")
    lines.append(f"Интересы: {p.get('interests') or '—'}")
    return "\n".join(lines)

def register(dp: Dispatcher):

    @dp.message(F.text == "👤 Профиль")
    async def btn_profile(m: Message):
        p = profiles_service.get_profile(m.from_user.id)
        await m.answer(_fmt_profile(p), parse_mode="HTML",
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
            "name": ProfileForm.name,
            "city": ProfileForm.city,
            "timezone": ProfileForm.timezone,
            "interests": ProfileForm.interests,
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
