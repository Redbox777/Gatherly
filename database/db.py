import sqlite3, sys, os
from contextlib import contextmanager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_FILE

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL, creator INTEGER NOT NULL,
                title TEXT NOT NULL, date_str TEXT, place TEXT, note TEXT, remind_at TEXT,
                created TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS participants (
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL, username TEXT,
                status TEXT DEFAULT 'going',
                PRIMARY KEY (event_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL, name TEXT NOT NULL,
                note TEXT, created TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL, item TEXT NOT NULL, done INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                question TEXT NOT NULL, created TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS poll_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER REFERENCES polls(id) ON DELETE CASCADE,
                text TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS poll_votes (
                poll_id INTEGER REFERENCES polls(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL,
                option_id INTEGER REFERENCES poll_options(id) ON DELETE CASCADE,
                PRIMARY KEY (poll_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL, username TEXT,
                amount REAL NOT NULL, description TEXT,
                created TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL, remind_at TEXT NOT NULL, sent INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL, title TEXT NOT NULL,
                created TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS route_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
                order_num INTEGER NOT NULL, name TEXT NOT NULL, note TEXT
            );
            CREATE TABLE IF NOT EXISTS event_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL, username TEXT,
                url TEXT NOT NULL, title TEXT,
                created TEXT DEFAULT (datetime('now'))
            );
        """)
