import os
import sqlite3
import tempfile
from pathlib import Path

# fest.db is created in the project root folder locally, or in temp directory on Vercel serverless
BASE_DIR = Path(__file__).resolve().parent.parent
if os.environ.get("VERCEL"):
    DB_PATH = Path(tempfile.gettempdir()) / "fest.db"
else:
    DB_PATH = BASE_DIR / "fest.db"

def init_db_schema(conn):
    """Creates tables if they don't already exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            venue TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            fee INTEGER NOT NULL DEFAULT 0,
            icon TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES events(id),
            student_name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            registered_at TEXT NOT NULL,
            UNIQUE(event_id, email)
        )
    """)
    conn.commit()

def get_db_connection():
    """Returns a SQLite connection with row_factory set to sqlite3.Row."""
    is_new = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    if is_new:
        init_db_schema(conn)
        try:
            from backend.seed_data import seed_events
            seed_events()
        except Exception as e:
            print(f"Auto-seed exception: {e}")

    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db_schema(conn)
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully at {DB_PATH}")
