import tempfile
import sqlite3
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import sys
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from core.autonomy import owner_authorization as auth


class TestOwnerAuthorization(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = auth.DB_FILE
        auth.DB_FILE = Path(self.temp.name) / "test.db"

        conn = auth.connect()
        conn.executescript("""
            CREATE TABLE owner_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_name TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                environment TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                scope_value TEXT NOT NULL,
                max_risk_level INTEGER NOT NULL,
                granted_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                status TEXT NOT NULL,
                revoked_at TEXT
            );

            CREATE TABLE authorization_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_id INTEGER NOT NULL,
                event TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    def tearDown(self):
        auth.DB_FILE = self.old_db
        self.temp.cleanup()

    def add_permission(self, **overrides):
        data = {
            "permission_name": "Test permission",
            "tool_name": "uname",
            "environment": "termux",
            "scope_type": "exact_task",
            "scope_value": "Inspect system information",
            "max_risk_level": 2,
            "granted_by": "owner",
            "created_at": auth.now(),
            "expires_at": None,
            "status": "active",
            "revoked_at": None
        }
        data.update(overrides)

        conn = auth.connect()
        cursor = conn.execute("""
            INSERT INTO owner_permissions (
                permission_name, tool_name, environment,
                scope_type, scope_value, max_risk_level,
                granted_by, created_at, expires_at,
                status, revoked_at
            ) VALUES (
                :permission_name, :tool_name, :environment,
                :scope_type, :scope_value, :max_risk_level,
                :granted_by, :created_at, :expires_at,
                :status, :revoked_at
            )
        """, data)
        permission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return permission_id

    def test_no_permission(self):
        self.assertFalse(auth.check_permission(
            "Inspect system information", "uname", "termux", 1
        ))

    def test_valid_permission(self):
        self.add_permission()
        self.assertTrue(auth.check_permission(
            "Inspect system information", "uname", "termux", 1
        ))

    def test_wrong_task(self):
        self.add_permission()
        self.assertFalse(auth.check_permission(
            "Delete files", "uname", "termux", 1
        ))

    def test_wrong_tool(self):
        self.add_permission()
        self.assertFalse(auth.check_permission(
            "Inspect system information", "nmap", "termux", 1
        ))

    def test_wrong_environment(self):
        self.add_permission()
        self.assertFalse(auth.check_permission(
            "Inspect system information", "uname", "kali", 1
        ))

    def test_risk_limit_exceeded(self):
        self.add_permission(max_risk_level=1)
        self.assertFalse(auth.check_permission(
            "Inspect system information", "uname", "termux", 2
        ))

    def test_expired_permission(self):
        expired = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat(timespec="seconds")
        self.add_permission(expires_at=expired)
        self.assertFalse(auth.check_permission(
            "Inspect system information", "uname", "termux", 1
        ))

    def test_revoked_permission(self):
        self.add_permission(status="revoked")
        self.assertFalse(auth.check_permission(
            "Inspect system information", "uname", "termux", 1
        ))

    def test_level4_never_authorized(self):
        self.add_permission(max_risk_level=3)
        self.assertFalse(auth.check_permission(
            "Inspect system information", "uname", "termux", 4
        ))

    def test_grant_permission(self):
        with patch.object(auth, "validate_tool", return_value=True), \
             patch.object(auth, "owner_confirmation", return_value=True):
            result = auth.grant_permission(
                "Temporary test",
                "uname",
                "termux",
                "Inspect system information",
                1,
                1
            )

        self.assertTrue(result)

        conn = auth.connect()
        row = conn.execute(
            "SELECT * FROM owner_permissions"
        ).fetchone()
        audit = conn.execute(
            "SELECT * FROM authorization_audit"
        ).fetchall()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["status"], "active")
        self.assertEqual(len(audit), 1)

    def test_revoke_permission(self):
        permission_id = self.add_permission()

        with patch.object(auth, "owner_confirmation", return_value=True):
            result = auth.revoke_permission(permission_id)

        self.assertTrue(result)
        self.assertFalse(auth.check_permission(
            "Inspect system information", "uname", "termux", 1
        ))

        conn = auth.connect()
        row = conn.execute(
            "SELECT status FROM owner_permissions WHERE id = ?",
            (permission_id,)
        ).fetchone()
        audit = conn.execute(
            "SELECT event FROM authorization_audit WHERE permission_id = ?",
            (permission_id,)
        ).fetchall()
        conn.close()

        self.assertEqual(row["status"], "revoked")
        self.assertEqual(audit[-1]["event"], "permission_revoked")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestOwnerAuthorization
    )
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    print("\n=== GHOST OWNER AUTHORIZATION TESTS ===")
    print(f"RESULT: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
    print("Real GHOST database modified: NO")
    print("Real permission records created: 0")
    print("Real commands executed: 0")
    if not result.wasSuccessful():
        raise SystemExit(1)
