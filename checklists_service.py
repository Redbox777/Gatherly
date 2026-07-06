from database.db import get_db

def add_item(event_id: int, user_id: int, item: str) -> int:
    with get_db() as db:
        cur = db.execute("INSERT INTO checklists (event_id,user_id,item) VALUES (?,?,?)",
            (event_id, user_id, item))
    return cur.lastrowid

def list_items(event_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM checklists WHERE event_id=?", (event_id,)).fetchall()
    return [dict(r) for r in rows]

def toggle_item(item_id: int) -> bool | None:
    """Возвращает новое состояние done, или None если не найден."""
    with get_db() as db:
        cur = db.execute("SELECT done FROM checklists WHERE id=?", (item_id,)).fetchone()
        if not cur:
            return None
        new_done = 0 if cur['done'] else 1
        db.execute("UPDATE checklists SET done=? WHERE id=?", (new_done, item_id))
    return bool(new_done)
