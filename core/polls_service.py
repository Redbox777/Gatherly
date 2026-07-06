from database.db import get_db

def create_poll(event_id: int, question: str, options: list[str]) -> int:
    with get_db() as db:
        cur = db.execute("INSERT INTO polls (event_id,question) VALUES (?,?)",
            (event_id, question))
        poll_id = cur.lastrowid
        for opt in options:
            db.execute("INSERT INTO poll_options (poll_id,text) VALUES (?,?)", (poll_id, opt))
    return poll_id

def list_polls(event_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM polls WHERE event_id=?", (event_id,)).fetchall()
    return [dict(r) for r in rows]

def get_poll_results(poll_id: int) -> dict | None:
    """Возвращает {question, options: [{id, text, votes}]}"""
    with get_db() as db:
        poll = db.execute("SELECT * FROM polls WHERE id=?", (poll_id,)).fetchone()
        if not poll:
            return None
        opts = db.execute("SELECT * FROM poll_options WHERE poll_id=?", (poll_id,)).fetchall()
        votes = db.execute(
            "SELECT option_id, COUNT(*) as cnt FROM poll_votes WHERE poll_id=? GROUP BY option_id",
            (poll_id,)
        ).fetchall()
    vcnt = {v['option_id']: v['cnt'] for v in votes}
    return {
        "id": poll['id'],
        "question": poll['question'],
        "options": [
            {"id": o['id'], "text": o['text'], "votes": vcnt.get(o['id'], 0)}
            for o in opts
        ]
    }

def cast_vote(poll_id: int, user_id: int, option_id: int) -> None:
    with get_db() as db:
        db.execute(
            "INSERT INTO poll_votes (poll_id,user_id,option_id) VALUES (?,?,?) "
            "ON CONFLICT(poll_id,user_id) DO UPDATE SET option_id=excluded.option_id",
            (poll_id, user_id, option_id)
        )
