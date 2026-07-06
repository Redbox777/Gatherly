from database.db import get_db

def add_link(event_id: int, user_id: int, username: str, url: str, title: str = None) -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO event_links (event_id,user_id,username,url,title) VALUES (?,?,?,?,?)",
            (event_id, user_id, username, url, title)
        )
    return cur.lastrowid

def list_links(event_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM event_links WHERE event_id=? ORDER BY created DESC", (event_id,)
        ).fetchall()
    return [dict(r) for r in rows]
