import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.paths import MEMORY_DIR

DB = MEMORY_DIR / "ghost_memory.db"

def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    try:
        os.chmod(DB, 0o600)
    except OSError:
        # Some Android/PRoot filesystems do not support Unix permission bits.
        pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    return conn

def remember(content, category="general"):
    with connect() as db:
        db.execute(
            "INSERT INTO memories (category, content, created_at) VALUES (?, ?, ?)",
            (category, content, datetime.now().isoformat(timespec="seconds"))
        )

def search(keyword):
    with connect() as db:
        return db.execute(
            "SELECT id, category, content FROM memories WHERE content LIKE ? ORDER BY id DESC",
            (f"%{keyword}%",)
        ).fetchall()

def show_all():
    with connect() as db:
        return db.execute(
            "SELECT id, category, content FROM memories ORDER BY id DESC"
        ).fetchall()

def forget(memory_id):
    with connect() as db:
        cursor = db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0

if __name__ == "__main__":
    connect()
    print("GHOST MEMORY CORE: READY")
    print(f"Database: {DB}")
