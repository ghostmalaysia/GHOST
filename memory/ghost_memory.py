import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path.home() / "GHOST/memory/ghost_memory.db"

def connect():
    conn = sqlite3.connect(DB)
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
