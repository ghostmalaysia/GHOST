import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from core.autonomy import owner_authorization, tool_executor


class ToolExecutorIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_file = self.root / "test_autonomy.db"
        self.inventory_file = self.root / "tool_inventory.json"

        executable = shutil.which("uname")
        if not executable:
            self.fail("uname executable not found")

        inventory = {
            "environments": {
                "termux": {
                    "uname": {
                        "available": True,
                        "path": executable
                    }
                }
            }
        }

        self.inventory_file.write_text(json.dumps(inventory))

        conn = sqlite3.connect(self.db_file)
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
                status TEXT NOT NULL DEFAULT 'active',
                revoked_at TEXT
            );

            CREATE TABLE authorization_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_id INTEGER,
                event TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.close()

        self.db_patch = patch.object(
            owner_authorization, "DB_FILE", self.db_file
        )
        self.inventory_patch = patch.object(
            tool_executor, "INVENTORY_FILE", self.inventory_file
        )

        self.db_patch.start()
        self.inventory_patch.start()

    def tearDown(self):
        self.inventory_patch.stop()
        self.db_patch.stop()
        self.temp.cleanup()

    def add_permission(self, task, expires_at=None, status="active"):
        conn = sqlite3.connect(self.db_file)
        conn.execute("""
            INSERT INTO owner_permissions (
                permission_name, tool_name, environment,
                scope_type, scope_value, max_risk_level,
                granted_by, created_at, expires_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Integration test permission",
            "uname",
            "termux",
            "exact_task",
            task,
            3,
            "test_owner",
            datetime.now(timezone.utc).isoformat(),
            expires_at,
            status
        ))
        conn.commit()
        conn.close()

    def test_no_permission_is_blocked(self):
        result = tool_executor.prepare_execution(
            "Inspect system information", "uname"
        )
        self.assertEqual(
            result["status"], "blocked_owner_permission_required"
        )

    def test_exact_active_permission_allows_dry_run(self):
        task = "Inspect system information"
        self.add_permission(task)

        result = tool_executor.prepare_execution(task, "uname")

        self.assertEqual(result["status"], "dry_run_ready")
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["shell"])
        self.assertEqual(result["execution_mode"], "dry_run")

    def test_different_task_is_blocked(self):
        self.add_permission("Inspect another system")

        result = tool_executor.prepare_execution(
            "Inspect system information", "uname"
        )

        self.assertEqual(
            result["status"], "blocked_owner_permission_required"
        )

    def test_expired_permission_is_blocked(self):
        expiry = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat()

        self.add_permission(
            "Inspect system information", expires_at=expiry
        )

        result = tool_executor.prepare_execution(
            "Inspect system information", "uname"
        )

        self.assertEqual(
            result["status"], "blocked_owner_permission_required"
        )

    def test_revoked_permission_is_blocked(self):
        self.add_permission(
            "Inspect system information", status="revoked"
        )

        result = tool_executor.prepare_execution(
            "Inspect system information", "uname"
        )

        self.assertEqual(
            result["status"], "blocked_owner_permission_required"
        )

    def test_level_four_is_blocked(self):
        result = tool_executor.prepare_execution(
            "Delete project files", "uname"
        )

        self.assertEqual(
            result["status"], "blocked_level4_approval_required"
        )
        self.assertTrue(result["approval_required"])
        self.assertFalse(result["execution_performed"])

    def test_no_command_execution(self):
        task = "Inspect system information"
        self.add_permission(task)

        with patch("subprocess.run") as mock_run, \
             patch("os.system") as mock_system:

            result = tool_executor.prepare_execution(task, "uname")

            mock_run.assert_not_called()
            mock_system.assert_not_called()

        self.assertEqual(result["status"], "dry_run_ready")
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["shell"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
