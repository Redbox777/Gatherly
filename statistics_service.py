from database.db import get_db

def get_user_statistics(user_id: int) -> dict:
    with get_db() as db:
        total_events = db.execute(
            "SELECT COUNT(*) as c FROM events WHERE creator=?", (user_id,)
        ).fetchone()['c']
        joined = db.execute(
            "SELECT COUNT(*) as c FROM participants WHERE user_id=? AND status='going'", (user_id,)
        ).fetchone()['c']
        total_places = db.execute(
            "SELECT COUNT(*) as c FROM places WHERE user_id=?", (user_id,)
        ).fetchone()['c']
        total_polls = db.execute(
            "SELECT COUNT(*) as c FROM polls p JOIN events e ON e.id=p.event_id WHERE e.creator=?",
            (user_id,)
        ).fetchone()['c']
        total_spent = db.execute(
            "SELECT COALESCE(SUM(amount),0) as s FROM expenses WHERE user_id=?", (user_id,)
        ).fetchone()['s']
        fav_place = db.execute(
            "SELECT name FROM places WHERE user_id=? ORDER BY created DESC LIMIT 1", (user_id,)
        ).fetchone()

    return {
        "total_events": total_events,
        "joined_events": joined,
        "total_places": total_places,
        "total_polls": total_polls,
        "total_spent": total_spent,
        "favorite_place": fav_place['name'] if fav_place else None,
    }
