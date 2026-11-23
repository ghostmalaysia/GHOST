import os
import json
import sys
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from core.autonomy import permission_guard

INVENTORY_FILE = BASE_DIR / "memory" / "tool_inventory.json"

# Fixed read-only commands.
# No user-supplied arguments and no shell execution.
SAFE_COMMANDS = {
    "uname": ["-a"],
    "whoami": [],
    "uptime": [],
    "df": ["-h"],
    "free": ["-h"],
    "ps": [],
}


def prepare_execution(task, tool_name, environment="termux"):
    if tool_name not in SAFE_COMMANDS:
        return {
            "status": "blocked_command_not_allowlisted",
            "execution_performed": False
        }

    if environment != "termux":
        return {
            "status": "blocked_environment_not_enabled",
            "execution_performed": False
        }

    policy = permission_guard.evaluate_tool_request(
        task=task,
        tool_name=tool_name,
        environment=environment
    )

    if not policy.get("execution_allowed"):
        return {
            **policy,
            "execution_performed": False
        }

    if not INVENTORY_FILE.exists():
        return {
            "status": "blocked_inventory_missing",
            "execution_performed": False
        }

    inventory = json.loads(INVENTORY_FILE.read_text())

    details = (
        inventory.get("environments", {})
        .get(environment, {})
        .get(tool_name, {})
    )

    tool_path = details.get("path")

    if not details.get("available") or not tool_path:
        return {
            "status": "blocked_tool_unavailable",
            "execution_performed": False
        }

    executable = Path(tool_path)

    if not executable.is_file() or not os.access(tool_path, os.X_OK):
        return {
            "status": "blocked_executable_invalid",
            "execution_performed": False
        }

    command = [tool_path] + SAFE_COMMANDS[tool_name]

    return {
        "status": "dry_run_ready",
        "task": task,
        "tool": tool_name,
        "environment": environment,
        "command_preview": command,
        "shell": False,
        "risk_level": policy["risk_level"],
        "execution_mode": "dry_run",
        "execution_performed": False
    }


def run_tests():
    tests = []

    tests.append((
        "No owner permission",
        prepare_execution(
            "Inspect system information", "uname"
        ),
        "blocked_owner_permission_required"
    ))

    tests.append((
        "Tool not allowlisted",
        prepare_execution("Run network scan", "nmap"),
        "blocked_command_not_allowlisted"
    ))

    tests.append((
        "Kali execution not enabled",
        prepare_execution(
            "Inspect system information", "uname", "kali"
        ),
        "blocked_environment_not_enabled"
    ))

    tests.append((
        "Level 4 action blocked",
        prepare_execution("Delete project files", "uname"),
        "blocked_level4_approval_required"
    ))

    with patch.object(
        permission_guard,
        "check_permission",
        return_value=True
    ):
        authorized = prepare_execution(
            "Inspect system information", "uname"
        )

        disk = prepare_execution(
            "Inspect disk space", "df"
        )

    tests.append((
        "Matching owner permission (simulated)",
        authorized,
        "dry_run_ready"
    ))

    tests.append((
        "No shell execution",
        disk,
        "dry_run_ready"
    ))

    passed = 0
    print("=== GHOST TOOL EXECUTOR TESTS ===")

    for name, result, expected in tests:
        success = result["status"] == expected

        if name == "No shell execution" and success:
            success = result.get("shell") is False

        print("[PASS]" if success else "[FAIL]", name)

        if not success:
            print("Expected:", expected)
            print("Actual:", result)

        passed += int(success)

    print(f"\nRESULT: {passed}/{len(tests)} tests passed")
    print("Actual commands executed: 0")
    print("Real permission records created: 0")


if __name__ == "__main__":
    run_tests()
