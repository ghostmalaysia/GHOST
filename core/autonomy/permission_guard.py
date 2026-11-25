import re
import sys
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from core.autonomy.owner_authorization import check_permission
from core.autonomy.tool_registry import KNOWLEDGE_FILE, load_knowledge as _load_knowledge

LEVEL4_PATTERNS = [
    "delete", "wipe", "format", "destroy", "overwrite",
    "drop database", "remove all",
    "padam", "hapus semua", "format cakera",
    "ubah firewall", "disable firewall",
    "dedahkan ke internet", "expose to internet",
    "hantar wang", "transfer funds", "bayar",
    "serang sistem luar", "attack external system"
]


def load_knowledge():
    return _load_knowledge()


def classify_risk(task, tool_risk):
    text = task.lower()

    for pattern in LEVEL4_PATTERNS:
        expression = (
            r"\b"
            + re.escape(pattern).replace(r"\ ", r"\s+")
            + r"\b"
        )
        if re.search(expression, text):
            return 4

    return max(1, min(3, int(tool_risk)))


def evaluate_tool_request(
    task,
    tool_name,
    environment,
    authorized_scope=False,
    preauthorized_scope=False
):
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Task description cannot be empty.")

    knowledge = load_knowledge()
    tool = knowledge["tools"].get(tool_name)

    if tool is None:
        return {
            "status": "blocked_unknown_tool",
            "reason": "Tool is not registered.",
            "execution_allowed": False,
            "execution_performed": False
        }

    availability = tool["availability"].get(environment)

    if availability is None:
        return {
            "status": "blocked_unknown_environment",
            "execution_allowed": False,
            "execution_performed": False
        }

    if not availability.get("available"):
        return {
            "status": "blocked_tool_unavailable",
            "execution_allowed": False,
            "execution_performed": False
        }

    risk = classify_risk(task, tool["risk_level"])

    result = {
        "tool": tool_name,
        "environment": environment,
        "risk_level": risk,
        "approval_required": False,
        "execution_allowed": False,
        "execution_performed": False
    }

    if risk == 4:
        result.update({
            "status": "blocked_level4_approval_required",
            "approval_required": True,
            "approval_status": "specific_owner_approval_required",
            "reason": "Level 4 requires specific owner approval. GHOST cannot approve itself."
        })
        return result

    if not check_permission(task, tool_name, environment, risk):
        result.update({
            "status": "blocked_owner_permission_required",
            "reason": "No matching active owner permission exists."
        })
        return result

    result.update({
        "status": "policy_passed_not_executed",
        "execution_allowed": True,
        "reason": "Owner permission verified. No command has been executed."
    })

    return result


def run_tests():
    tests = []

    tests.append((
        "Unknown tool",
        evaluate_tool_request("Check system", "unknown_tool", "termux"),
        "blocked_unknown_tool"
    ))

    tests.append((
        "Unavailable tool",
        evaluate_tool_request("Use SQLite", "sqlite3", "kali"),
        "blocked_tool_unavailable"
    ))

    tests.append((
        "Unknown environment",
        evaluate_tool_request("Check system", "uname", "unknown"),
        "blocked_unknown_environment"
    ))

    tests.append((
        "No owner permission",
        evaluate_tool_request("Check connectivity", "ping", "termux", True, True),
        "blocked_owner_permission_required"
    ))

    tests.append((
        "Level 3 without owner permission",
        evaluate_tool_request("Scan authorized network", "nmap", "kali", True, True),
        "blocked_owner_permission_required"
    ))

    tests.append((
        "Level 4 cannot self-approve",
        evaluate_tool_request("Delete project files", "python3", "termux", True, True),
        "blocked_level4_approval_required"
    ))

    tests.append((
        "Information is not format",
        evaluate_tool_request("Inspect system information", "uname", "termux"),
        "blocked_owner_permission_required"
    ))

    with patch.object(
        sys.modules[__name__],
        "check_permission",
        return_value=True
    ):
        tests.append((
            "Matching owner permission",
            evaluate_tool_request("Check system information", "uname", "termux"),
            "policy_passed_not_executed"
        ))

    passed = 0
    print("=== GHOST PERMISSION GUARD TESTS ===")

    for name, result, expected in tests:
        success = result["status"] == expected
        print("[PASS]" if success else "[FAIL]", name)

        if not success:
            print(" Expected:", expected)
            print(" Actual:", result["status"])

        passed += int(success)

    print(f"\nRESULT: {passed}/{len(tests)} tests passed")
    print("Actual commands executed: 0")
    print("Real permission records created: 0")


if __name__ == "__main__":
    run_tests()
