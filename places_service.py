from database.db import get_db

def save_place(user_id: int, name: str, note: str = None) -> int:
    with get_db() as db:
        cur = db.execute("INSERT INTO places (user_id,name,note) VALUES (?,?,?)",
            (user_id, name, note))
    return cur.lastrowid

def list_places(user_id: int, limit: int = 20) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM places WHERE user_id=? ORDER BY created DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]

def get_latest_place(user_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM places WHERE user_id=? ORDER BY created DESC LIMIT 1", (user_id,)
        ).fetchone()
    return dict(row) if row else None
