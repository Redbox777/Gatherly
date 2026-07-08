from database.db import get_db

def add_message(event_id, user_id, username, text):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO event_discussion (event_id, user_id, username, text) VALUES (?,?,?,?)",
            (event_id, user_id, username, text)
        )
    return cur.lastrowid

def get_messages(event_id, limit=50):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM event_discussion WHERE event_id=? "
            "ORDER BY id DESC LIMIT ?",
            (event_id, limit)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]

def get_message_count(event_id):
    with get_db() as db:
        row = db.execute(
            "SELECT COUNT(*) as c FROM event_discussion WHERE event_id=?", (event_id,)
        ).fetchone()
    return row['c']
