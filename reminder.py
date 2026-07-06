import asyncio, logging
from aiogram import Bot
from core.reminders_service import get_due_reminders, mark_sent

log = logging.getLogger(__name__)

async def reminder_loop(bot: Bot):
    """Фоновая задача — каждую минуту проверяет напоминания через core-сервис."""
    while True:
        try:
            for r in get_due_reminders():
                try:
                    await bot.send_message(
                        r['user_id'],
                        f"⏰ <b>Напоминание!</b>\n\n"
                        f"Встреча <b>{r['title']}</b> скоро начнётся!\nНе забудь 😊",
                        parse_mode="HTML"
                    )
                    mark_sent(r['id'])
                except Exception as e:
                    log.error(f"Reminder send error: {e}")
        except Exception as e:
            log.error(f"Reminder loop error: {e}")
        await asyncio.sleep(60)
