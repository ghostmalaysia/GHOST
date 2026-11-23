import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import sys

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from core.autonomy.tool_discovery import TOOL_CATEGORIES

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_FILE = BASE_DIR / "memory" / "tool_inventory.json"

TOOLS = list(dict.fromkeys(
    tool
    for category in TOOL_CATEGORIES.values()
    for tool in category
))


def scan_termux():
    results = {}

    for tool in TOOLS:
        path = shutil.which(tool)
        results[tool] = {
            "available": path is not None,
            "path": path
        }

    return results


def scan_kali():
    command = (
        "for tool in " + " ".join(TOOLS) + "; do "
        'path=$(command -v "$tool" 2>/dev/null); '
        'if [ -n "$path" ]; then '
        'printf "%s\\t%s\\n" "$tool" "$path"; '
        "fi; done"
    )

    try:
        result = subprocess.run(
            ["nethunter", command],
            capture_output=True,
            text=True,
            timeout=45,
            check=False
        )

        if result.returncode != 0:
            return None, result.stderr.strip()

        found = {}

        for line in result.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                found[parts[0]] = parts[1]

        results = {}

        for tool in TOOLS:
            path = found.get(tool)
            results[tool] = {
                "available": path is not None,
                "path": path
            }

        return results, None

    except (OSError, subprocess.TimeoutExpired) as error:
        return None, str(error)


def build_inventory():
    termux = scan_termux()
    kali, kali_error = scan_kali()

    inventory = {
        "scanned_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "tool_count": len(TOOLS),
        "environments": {
            "termux": termux,
            "kali": kali
        },
        "errors": {
            "kali": kali_error
        }
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(inventory, indent=2),
        encoding="utf-8"
    )

    return inventory


def report():
    inventory = build_inventory()

    print("=== GHOST UNIFIED TOOL INVENTORY ===")

    for environment, tools in inventory["environments"].items():
        if tools is None:
            print(environment.upper(), "SCAN FAILED")
            continue

        available = sum(
            item["available"] for item in tools.values()
        )

        print(
            environment.upper(),
            ":", available, "/", len(tools), "tools"
        )

    print("Saved:", OUTPUT_FILE)

    if inventory["errors"]["kali"]:
        print("Kali scan warning:", inventory["errors"]["kali"])

    print("Inventory scan completed.")


if __name__ == "__main__":
    report()
