"""
Точка входа. Только: запуск бота, инициализация БД, загрузка handlers, фоновые задачи.
Вся бизнес-логика — в core/. Весь Telegram-интерфейс — в telegram/.
"""
import asyncio, logging, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from database.db import init_db
from telegram.loader import load_handlers
from telegram.reminder import reminder_loop
from telegram.keyboards import main_kb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

async def main():
    init_db()
    bot = Bot(token=TOKEN)
    dp  = Dispatcher(storage=MemoryStorage())

    @dp.message(Command("start"))
    async def cmd_start(m: Message, state: FSMContext):
        await state.clear()
        await m.answer(
            "👋 <b>Gatherly</b> — помощник для встреч и путешествий\n\n"
            "Выбери раздел на клавиатуре внизу 👇",
            reply_markup=main_kb(), parse_mode="HTML"
        )

    @dp.message(F.text == "❌ Отмена")
    async def cmd_cancel(m: Message, state: FSMContext):
        await state.clear()
        await m.answer("Отменено.", reply_markup=main_kb())

    load_handlers(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(reminder_loop(bot))

    log.info("🚀 Gatherly Core v1 запущен")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    asyncio.run(main())
