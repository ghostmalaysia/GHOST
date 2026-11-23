import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from core.autonomy import owner_auth

DB_FILE = BASE_DIR / "memory" / "ghost_autonomy.db"
KNOWLEDGE_FILE = BASE_DIR / "memory" / "tool_knowledge.json"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def owner_confirmation(action):
    phrases = {
        "grant": "AUTHORIZE GHOST PERMISSION",
        "revoke": "REVOKE GHOST PERMISSION"
    }

    if action not in phrases:
        return False

    print("\\nOWNER AUTHENTICATION REQUIRED")

    if not owner_auth.verify_owner_auth():
        print("OWNER AUTHENTICATION FAILED. ACTION BLOCKED.")
        return False

    expected = phrases[action]
    print("\\nOWNER ACTION CONFIRMATION REQUIRED")
    entered = input(f"Type exactly: {expected}\\n> ").strip()

    if entered != expected:
        print("OWNER CONFIRMATION FAILED.")
        return False

    return True

def validate_tool(tool_name, environment):
    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError("Tool Knowledge Base not found.")

    knowledge = json.loads(KNOWLEDGE_FILE.read_text())
    tool = knowledge.get("tools", {}).get(tool_name)

    if not tool:
        raise ValueError("Tool is not registered.")

    availability = tool.get("availability", {}).get(environment)

    if not availability or not availability.get("available"):
        raise ValueError("Tool is not available in this environment.")

    return True


def grant_permission(
    permission_name,
    tool_name,
    environment,
    scope_value,
    max_risk_level,
    expires_hours=None
):
    if not all(isinstance(x, str) and x.strip() for x in (
        permission_name, tool_name, environment, scope_value
    )):
        raise ValueError("All text fields must be non-empty.")

    if not 1 <= int(max_risk_level) <= 3:
        raise ValueError("Only risk levels 1 to 3 may be authorized.")

    if expires_hours is not None:
        if not 1 <= int(expires_hours) <= 8760:
            raise ValueError("Expiry must be between 1 and 8760 hours.")

    validate_tool(tool_name, environment)

    if not owner_confirmation("grant"):
        return False

    created = now()
    expires = None

    if expires_hours is not None:
        expires = (
            datetime.now(timezone.utc)
            + timedelta(hours=int(expires_hours))
        ).isoformat(timespec="seconds")

    conn = connect()

    try:
        cursor = conn.execute("""
            INSERT INTO owner_permissions (
                permission_name, tool_name, environment,
                scope_type, scope_value, max_risk_level,
                granted_by, created_at, expires_at, status
            )
            VALUES (?, ?, ?, 'exact_task', ?, ?, 'owner', ?, ?, 'active')
        """, (
            permission_name.strip(),
            tool_name,
            environment,
            scope_value.strip(),
            int(max_risk_level),
            created,
            expires
        ))

        permission_id = cursor.lastrowid

        conn.execute("""
            INSERT INTO authorization_audit (
                permission_id, event, details, created_at
            )
            VALUES (?, 'permission_granted', ?, ?)
        """, (
            permission_id,
            json.dumps({
                "tool": tool_name,
                "environment": environment,
                "scope": scope_value,
                "max_risk_level": int(max_risk_level)
            }),
            created
        ))

        conn.commit()
        print("Permission granted. ID:", permission_id)
        return True

    finally:
        conn.close()


def check_permission(task, tool_name, environment, risk_level):
    if not isinstance(task, str) or not task.strip():
        return False

    if not 1 <= int(risk_level) <= 3:
        return False

    conn = connect()

    try:
        rows = conn.execute("""
            SELECT * FROM owner_permissions
            WHERE tool_name = ?
              AND environment = ?
              AND scope_type = 'exact_task'
              AND scope_value = ?
              AND status = 'active'
              AND max_risk_level >= ?
        """, (
            tool_name,
            environment,
            task.strip(),
            int(risk_level)
        )).fetchall()

        current = datetime.now(timezone.utc)

        for row in rows:
            expiry = row["expires_at"]

            if expiry:
                try:
                    expiry_time = datetime.fromisoformat(expiry)
                    if expiry_time.tzinfo is None:
                        continue
                    if expiry_time <= current:
                        continue
                except ValueError:
                    continue

            return True

        return False

    finally:
        conn.close()


def revoke_permission(permission_id):
    if int(permission_id) <= 0:
        raise ValueError("Invalid permission ID.")

    conn = connect()

    try:
        row = conn.execute("""
            SELECT id, status FROM owner_permissions WHERE id = ?
        """, (int(permission_id),)).fetchone()

        if not row:
            print("Permission not found.")
            return False

        if row["status"] != "active":
            print("Permission is not active.")
            return False

        if not owner_confirmation("revoke"):
            return False

        timestamp = now()

        conn.execute("""
            UPDATE owner_permissions
            SET status = 'revoked', revoked_at = ?
            WHERE id = ?
        """, (timestamp, int(permission_id)))

        conn.execute("""
            INSERT INTO authorization_audit (
                permission_id, event, details, created_at
            )
            VALUES (?, 'permission_revoked', ?, ?)
        """, (
            int(permission_id),
            "Owner revoked permission.",
            timestamp
        ))

        conn.commit()
        print("Permission revoked.")
        return True

    finally:
        conn.close()


def list_permissions():
    conn = connect()

    try:
        rows = conn.execute("""
            SELECT id, permission_name, tool_name, environment,
                   scope_value, max_risk_level, status, expires_at
            FROM owner_permissions
            ORDER BY id DESC
        """).fetchall()

        print("=== OWNER PERMISSIONS ===")

        if not rows:
            print("No permission records.")
            return

        for row in rows:
            print(dict(row))

    finally:
        conn.close()


def positive_id(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("ID must be an integer.")

    if number <= 0:
        raise argparse.ArgumentTypeError("ID must be greater than zero.")

    return number


def valid_expiry_hours(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Expiry must be an integer.")

    if not 1 <= number <= 8760:
        raise argparse.ArgumentTypeError(
            "Expiry must be between 1 and 8760 hours."
        )

    return number


def main():
    parser = argparse.ArgumentParser(
        description="GHOST Owner Authorization Manager"
    )

    sub = parser.add_subparsers(dest="action", required=True)

    grant = sub.add_parser("grant")
    grant.add_argument("--name", required=True)
    grant.add_argument("--tool", required=True)
    grant.add_argument("--environment", required=True)
    grant.add_argument("--task", required=True)
    grant.add_argument("--max-risk", type=int, choices=[1, 2, 3], required=True)
    grant.add_argument("--expires-hours", type=valid_expiry_hours)

    revoke = sub.add_parser("revoke")
    revoke.add_argument("--id", type=positive_id, required=True)

    sub.add_parser("list")

    args = parser.parse_args()

    if args.action == "grant":
        grant_permission(
            args.name,
            args.tool,
            args.environment,
            args.task,
            args.max_risk,
            args.expires_hours
        )

    elif args.action == "revoke":
        revoke_permission(args.id)

    elif args.action == "list":
        list_permissions()


if __name__ == "__main__":
    main()
