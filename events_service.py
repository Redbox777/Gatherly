"""
Бизнес-логика встреч. Не знает про Telegram, кнопки, сообщения.
Любой клиент (Telegram, Android, Web) вызывает эти функции одинаково.
"""
from database.db import get_db

def create_event(chat_id: int, creator_id: int, creator_username: str,
                  title: str, date_str: str = None, place: str = None,
                  note: str = None, remind_at: str = None) -> int:
    """Создаёт встречу, добавляет создателя как участника. Возвращает event_id."""
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO events (chat_id,creator,title,date_str,place,note,remind_at) VALUES (?,?,?,?,?,?,?)",
            (chat_id, creator_id, title, date_str, place, note, remind_at)
        )
        event_id = cur.lastrowid
        db.execute(
            "INSERT OR IGNORE INTO participants (event_id,user_id,username,status) VALUES (?,?,?,'going')",
            (event_id, creator_id, creator_username)
        )
        if remind_at:
            db.execute(
                "INSERT INTO reminders (event_id,user_id,remind_at) VALUES (?,?,?)",
                (event_id, creator_id, remind_at)
            )
    return event_id

def get_event(event_id: int) -> dict | None:
    with get_db() as db:
        ev = db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    return dict(ev) if ev else None

def get_participants(event_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM participants WHERE event_id=?", (event_id,)).fetchall()
    return [dict(r) for r in rows]

def list_user_events(user_id: int, limit: int = 10) -> list[dict]:
    """Встречи, где пользователь создатель или участник."""
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM events WHERE creator=? OR id IN "
            "(SELECT event_id FROM participants WHERE user_id=?) "
            "ORDER BY created DESC LIMIT ?",
            (user_id, user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]

def join_event(event_id: int, user_id: int, username: str) -> bool:
    """Возвращает False если встреча не найдена."""
    with get_db() as db:
        ev = db.execute("SELECT id FROM events WHERE id=?", (event_id,)).fetchone()
        if not ev:
            return False
        db.execute(
            "INSERT OR IGNORE INTO participants (event_id,user_id,username,status) VALUES (?,?,?,'going')",
            (event_id, user_id, username)
        )
    return True

def set_rsvp(event_id: int, user_id: int, username: str, status: str) -> None:
    """status: 'going' | 'maybe' | 'no'"""
    with get_db() as db:
        db.execute(
            "INSERT INTO participants (event_id,user_id,username,status) VALUES (?,?,?,?) "
            "ON CONFLICT(event_id,user_id) DO UPDATE SET status=excluded.status,username=excluded.username",
            (event_id, user_id, username, status)
        )

def delete_event(event_id: int, requester_id: int) -> bool:
    """Возвращает False если requester не создатель."""
    with get_db() as db:
        ev = db.execute("SELECT creator FROM events WHERE id=?", (event_id,)).fetchone()
        if not ev or ev['creator'] != requester_id:
            return False
        db.execute("DELETE FROM events WHERE id=?", (event_id,))
    return True

def get_going_participant_ids(event_id: int, exclude_user_id: int = None) -> list[int]:
    with get_db() as db:
        if exclude_user_id:
            rows = db.execute(
                "SELECT user_id FROM participants WHERE event_id=? AND status='going' AND user_id!=?",
                (event_id, exclude_user_id)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT user_id FROM participants WHERE event_id=? AND status='going'",
                (event_id,)
            ).fetchall()
    return [r['user_id'] for r in rows]
