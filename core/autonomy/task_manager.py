import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parents[2] / "memory" / "ghost_autonomy.db"

PRIORITIES = {"low", "normal", "high", "urgent"}
STATUSES = {"pending", "in_progress", "completed", "failed", "blocked"}
RISK_LEVELS = {1, 2, 3, 4}


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'normal',
                status TEXT NOT NULL DEFAULT 'pending',
                risk_level INTEGER NOT NULL DEFAULT 1,
                approval_required INTEGER NOT NULL DEFAULT 0,
                approval_status TEXT NOT NULL DEFAULT 'not_required',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
    return True


def add_task(title, description="", priority="normal", risk_level=1):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Task title is required.")

    if priority not in PRIORITIES:
        raise ValueError("Invalid priority.")

    if type(risk_level) is not int or risk_level not in RISK_LEVELS:
        raise ValueError("Risk level must be between 1 and 4.")

    approval_required = risk_level == 4
    approval_status = "pending" if approval_required else "not_required"
    timestamp = now()

    with connect() as db:
        cursor = db.execute("""
            INSERT INTO tasks (
                title, description, priority, status,
                risk_level, approval_required, approval_status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?)
        """, (
            title.strip(),
            description.strip() if isinstance(description, str) else "",
            priority,
            risk_level,
            int(approval_required),
            approval_status,
            timestamp,
            timestamp
        ))
        return cursor.lastrowid


def list_tasks(status=None):
    if status is not None and status not in STATUSES:
        raise ValueError("Invalid task status.")

    with connect() as db:
        if status:
            rows = db.execute("""
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'normal' THEN 3
                        ELSE 4
                    END,
                    id ASC
            """, (status,)).fetchall()
        else:
            rows = db.execute("""
                SELECT * FROM tasks
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'normal' THEN 3
                        ELSE 4
                    END,
                    id ASC
            """).fetchall()

    return [dict(row) for row in rows]


def update_status(task_id, status):
    if type(task_id) is not int or task_id < 1:
        raise ValueError("Invalid task ID.")

    if status not in STATUSES:
        raise ValueError("Invalid task status.")

    with connect() as db:
        task = db.execute(
            "SELECT risk_level, approval_status FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if task is None:
            raise ValueError("Task not found.")

        if status == "in_progress":
            if task["risk_level"] == 4:
                raise PermissionError(
                    "Level 4 task requires owner approval first."
                )

        db.execute("""
            UPDATE tasks
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, now(), task_id))

    return True


def summary():
    with connect() as db:
        rows = db.execute("""
            SELECT status, COUNT(*) AS total
            FROM tasks
            GROUP BY status
        """).fetchall()

    result = {status: 0 for status in STATUSES}
    for row in rows:
        result[row["status"]] = row["total"]

    result["total"] = sum(result.values())
    return result


if __name__ == "__main__":
    initialize()
    print("GHOST Task Manager initialized.")
    print("Database:", DB_PATH)
    print("Summary:", summary())
