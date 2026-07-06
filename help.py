from aiogram import Dispatcher, F
from aiogram.types import Message

def register(dp: Dispatcher):

    @dp.message(F.text == "❓ Помощь")
    async def btn_help(m: Message):
        await m.answer(
            "📖 <b>Gatherly — как пользоваться</b>\n\n"
            "📅 <b>Встречи</b> — создай встречу, пригласи через /join ID\n"
            "📍 <b>Места</b> — сохраняй интересные места\n"
            "✅ <b>Чек-листы</b> — список дел для встречи\n"
            "🌤 <b>Погода</b> — погода в любом городе\n"
            "🌅 <b>Восход/закат</b> — время рассвета и заката\n"
            "🗳 <b>Голосования</b> — голосуй внутри встречи\n"
            "💰 <b>Расходы</b> — кто сколько потратил\n"
            "🗺 <b>Маршруты</b> — точки маршрута поездки\n"
            "📊 <b>Статистика</b> — твои данные\n\n"
            "/start — главное меню\n"
            "/join ID — вступить в встречу",
            parse_mode="HTML"
        )
