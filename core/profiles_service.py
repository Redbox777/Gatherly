from database.db import get_db

def get_profile(user_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM user_profiles WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None

def save_profile(user_id: int, name=None, city=None, timezone=None, interests=None):
    existing = get_profile(user_id)
    with get_db() as db:
        if existing:
            db.execute(
                "UPDATE user_profiles SET "
                "name=COALESCE(?, name), city=COALESCE(?, city), "
                "timezone=COALESCE(?, timezone), interests=COALESCE(?, interests), "
                "updated=datetime('now') WHERE user_id=?",
                (name, city, timezone, interests, user_id)
            )
        else:
            db.execute(
                "INSERT INTO user_profiles (user_id, name, city, timezone, interests) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, name, city, timezone, interests)
            )

def delete_profile_field(user_id: int, field: str):
    if field not in ("name", "city", "timezone", "interests"):
        return
    with get_db() as db:
        db.execute(f"UPDATE user_profiles SET {field}=NULL WHERE user_id=?", (user_id,))
