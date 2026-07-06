from aiogram import Dispatcher, F
from aiogram.types import Message
from core.statistics_service import get_user_statistics

def register(dp: Dispatcher):

    @dp.message(F.text == "📊 Статистика")
    async def btn_stats(m: Message):
        stats = get_user_statistics(m.from_user.id)
        fav = stats['favorite_place'] or "—"
        await m.answer(
            f"📊 <b>Твоя статистика</b>\n\n"
            f"📅 Создано встреч: <b>{stats['total_events']}</b>\n"
            f"✅ Участвуешь в: <b>{stats['joined_events']}</b>\n"
            f"📍 Сохранено мест: <b>{stats['total_places']}</b>\n"
            f"🗳 Голосований: <b>{stats['total_polls']}</b>\n"
            f"💰 Потрачено: <b>{stats['total_spent']:.0f} ₽</b>\n\n"
            f"📍 Последнее место: <b>{fav}</b>",
            parse_mode="HTML"
        )
