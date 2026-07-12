from database.db import get_db

def add_note(user_id, text, event_id=None, is_shared=False, attachment_url=None):
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO notes (user_id, event_id, text, is_shared, attachment_url) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, event_id, text, 1 if (event_id and is_shared) else 0, attachment_url)
        )
    return cur.lastrowid

def list_personal_notes(user_id, limit=30):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM notes WHERE user_id=? AND event_id IS NULL "
            "ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]

def list_event_notes(event_id, requesting_user_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM notes WHERE event_id=? AND "
            "(is_shared=1 OR user_id=?) "
            "ORDER BY id DESC",
            (event_id, requesting_user_id)
        ).fetchall()
    return [dict(r) for r in rows]

def delete_note(note_id, requester_id):
    with get_db() as db:
        row = db.execute("SELECT user_id FROM notes WHERE id=?", (note_id,)).fetchone()
        if not row or row['user_id'] != requester_id:
            return False
        db.execute("DELETE FROM notes WHERE id=?", (note_id,))
    return True

def get_note(note_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    return dict(row) if row else None
