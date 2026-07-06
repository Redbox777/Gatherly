from database.db import get_db

def create_route(event_id: int, user_id: int, title: str, points: list[str]) -> int:
    with get_db() as db:
        cur = db.execute("INSERT INTO routes (event_id,user_id,title) VALUES (?,?,?)",
            (event_id, user_id, title))
        route_id = cur.lastrowid
        for i, pt in enumerate(points, 1):
            db.execute("INSERT INTO route_points (route_id,order_num,name) VALUES (?,?,?)",
                (route_id, i, pt))
    return route_id

def list_routes(event_id: int) -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT * FROM routes WHERE event_id=?", (event_id,)).fetchall()
    return [dict(r) for r in rows]

def get_route_with_points(route_id: int) -> dict | None:
    with get_db() as db:
        route = db.execute("SELECT * FROM routes WHERE id=?", (route_id,)).fetchone()
        if not route:
            return None
        points = db.execute(
            "SELECT * FROM route_points WHERE route_id=? ORDER BY order_num", (route_id,)
        ).fetchall()
    return {"route": dict(route), "points": [dict(p) for p in points]}
