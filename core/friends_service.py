from database.db import get_db

def send_friend_request(from_user_id, from_username, to_user_id):
    if from_user_id == to_user_id:
        return "self"

    with get_db() as db:
        existing = db.execute(
            "SELECT status FROM friendships WHERE "
            "(user_a=? AND user_b=?) OR (user_a=? AND user_b=?)",
            (from_user_id, to_user_id, to_user_id, from_user_id)
        ).fetchone()

        if existing:
            if existing['status'] == 'accepted':
                return "already_friends"
            if existing['status'] == 'pending':
                return "already_pending"

        db.execute(
            "INSERT INTO friendships (user_a, user_b, requested_by, status) "
            "VALUES (?, ?, ?, 'pending')",
            (from_user_id, to_user_id, from_user_id)
        )
    return "sent"

def respond_to_request(request_user_a, request_user_b, responder_id, accept):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM friendships WHERE user_a=? AND user_b=? AND status='pending'",
            (request_user_a, request_user_b)
        ).fetchone()
        if not row:
            return False
        if row['requested_by'] == responder_id:
            return False

        if accept:
            db.execute(
                "UPDATE friendships SET status='accepted' WHERE user_a=? AND user_b=?",
                (request_user_a, request_user_b)
            )
        else:
            db.execute(
                "DELETE FROM friendships WHERE user_a=? AND user_b=?",
                (request_user_a, request_user_b)
            )
    return True

def get_pending_requests(user_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM friendships WHERE status='pending' AND "
            "((user_a=? AND requested_by!=?) OR (user_b=? AND requested_by!=?))",
            (user_id, user_id, user_id, user_id)
        ).fetchall()
    result = []
    for r in rows:
        other_id = r['user_b'] if r['user_a'] == user_id else r['user_a']
        result.append({"other_user_id": other_id, "requested_by": r['requested_by']})
    return result

def get_friends_list(user_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT user_a, user_b FROM friendships WHERE status='accepted' "
            "AND (user_a=? OR user_b=?)",
            (user_id, user_id)
        ).fetchall()
    return [r['user_b'] if r['user_a'] == user_id else r['user_a'] for r in rows]

def find_user_by_username(username):
    username = username.lstrip('@')
    with get_db() as db:
        row = db.execute(
            "SELECT user_id FROM participants WHERE username=? LIMIT 1",
            (username,)
        ).fetchone()
        if not row:
            row = db.execute(
                "SELECT user_id FROM event_links WHERE username=? LIMIT 1",
                (username,)
            ).fetchone()
    return row['user_id'] if row else None

def remove_friend(user_id, friend_id):
    with get_db() as db:
        db.execute(
            "DELETE FROM friendships WHERE "
            "(user_a=? AND user_b=?) OR (user_a=? AND user_b=?)",
            (user_id, friend_id, friend_id, user_id)
        )
