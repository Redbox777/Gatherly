from datetime import datetime
from database.db import get_db

def get_due_reminders(now_str: str = None) -> list[dict]:
    """Возвращает напоминания которые пора отправить (JOIN с events для заголовка)."""
    now_str = now_str or datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_db() as db:
        rows = db.execute(
            "SELECT r.*, e.title FROM reminders r "
            "JOIN events e ON e.id=r.event_id "
            "WHERE r.sent=0 AND r.remind_at<=?", (now_str,)
        ).fetchall()
    return [dict(r) for r in rows]

def mark_sent(reminder_id: int) -> None:
    with get_db() as db:
        db.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))
