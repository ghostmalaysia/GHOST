import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "memory"
    / "ghost_autonomy.db"
)


def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                run_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY(task_id) REFERENCES tasks(id)
            )
        """)
    return True


def schedule_task(task_id, run_at):
    if type(task_id) is not int or task_id < 1:
        raise ValueError("Invalid task ID.")

    if not isinstance(run_at, str):
        raise ValueError("run_at must be an ISO 8601 string.")

    try:
        scheduled_time = datetime.fromisoformat(
            run_at.replace("Z", "+00:00")
        )
    except ValueError:
        raise ValueError("Invalid ISO 8601 date/time.")

    if scheduled_time.tzinfo is None:
        raise ValueError("Timezone is required. Use UTC offset.")

    with connect() as db:
        task = db.execute(
            "SELECT id FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        if task is None:
            raise ValueError("Task not found.")

        cursor = db.execute("""
            INSERT INTO schedules (
                task_id, run_at, status, created_at
            )
            VALUES (?, ?, 'scheduled', ?)
        """, (
            task_id,
            scheduled_time.astimezone(timezone.utc).isoformat(),
            now()
        ))

        return cursor.lastrowid


def due_schedules():
    current = now()

    with connect() as db:
        rows = db.execute("""
            SELECT
                schedules.id AS schedule_id,
                schedules.task_id,
                schedules.run_at,
                schedules.status,
                tasks.title,
                tasks.priority,
                tasks.risk_level,
                tasks.approval_required
            FROM schedules
            JOIN tasks ON tasks.id = schedules.task_id
            WHERE schedules.status = 'scheduled'
              AND schedules.run_at <= ?
            ORDER BY schedules.run_at ASC, schedules.id ASC
        """, (current,)).fetchall()

    return [dict(row) for row in rows]


def mark_completed(schedule_id):
    if type(schedule_id) is not int or schedule_id < 1:
        raise ValueError("Invalid schedule ID.")

    with connect() as db:
        cursor = db.execute("""
            UPDATE schedules
            SET status = 'completed',
                completed_at = ?
            WHERE id = ?
              AND status = 'scheduled'
        """, (now(), schedule_id))

        if cursor.rowcount != 1:
            raise ValueError(
                "Schedule not found or already processed."
            )

    return True


if __name__ == "__main__":
    initialize()
    print("GHOST Scheduler initialized.")
    print("Due schedules:", len(due_schedules()))
