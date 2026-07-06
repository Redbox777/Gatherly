from database.db import get_db

def add_expense(event_id: int, user_id: int, username: str,
                 amount: float, description: str = None) -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO expenses (event_id,user_id,username,amount,description) VALUES (?,?,?,?,?)",
            (event_id, user_id, username, amount, description)
        )
    return cur.lastrowid

def list_expenses(event_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM expenses WHERE event_id=? ORDER BY created DESC", (event_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def calculate_balance(event_id: int) -> dict:
    """
    Возвращает {total, per_person, by_user: {username: {spent, diff}}}
    diff > 0  — переплатил
    diff < 0  — должен
    """
    expenses = list_expenses(event_id)
    totals = {}
    for e in expenses:
        totals[e['username']] = totals.get(e['username'], 0) + e['amount']

    total_sum  = sum(totals.values())
    per_person = total_sum / len(totals) if totals else 0

    by_user = {
        name: {"spent": spent, "diff": spent - per_person}
        for name, spent in totals.items()
    }

    return {
        "total": total_sum,
        "per_person": per_person,
        "by_user": by_user,
        "expenses": expenses,
    }
