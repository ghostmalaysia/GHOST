"""Static tool registry used for policy decisions.

Registry availability describes environments where GHOST recognises a tool.
Actual binary availability is verified separately against tool_inventory.json
before any dry-run command can be prepared.
"""

import json
from pathlib import Path

from core.autonomy.tool_discovery import TOOL_CATEGORIES
from core.autonomy.tool_knowledge import TOOL_INFO


BASE_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_FILE = BASE_DIR / "memory" / "tool_knowledge.json"
ENVIRONMENTS = ("termux", "kali")
KALI_CATEGORIES = (
    "system", "programming", "networking", "security", "file_management"
)
KALI_TOOLS = {
    tool
    for category in KALI_CATEGORIES
    for tool in TOOL_CATEGORIES.get(category, [])
}


def build_registry():
    names = dict.fromkeys(
        tool
        for category in TOOL_CATEGORIES.values()
        for tool in category
    )

    tools = {}
    for name in names:
        description, purpose, risk = TOOL_INFO.get(
            name,
            ("Unclassified tool", "Purpose requires further research", 2)
        )
        tools[name] = {
            "name": name,
            "categories": [
                category for category, entries in TOOL_CATEGORIES.items()
                if name in entries
            ],
            "description": description,
            "typical_uses": purpose,
            "risk_level": risk,
            "availability": {
                environment: {
                    "available": (
                        True if environment == "termux"
                        else name in KALI_TOOLS
                    ),
                    "path": None,
                }
                for environment in ENVIRONMENTS
            },
            "execution_status": "not_executed",
            "permission_required": (
                "Owner authorization according to task scope and risk"
            ),
            "knowledge_status": (
                "basic" if name in TOOL_INFO else "needs_research"
            ),
        }

    return {
        "source": "static_registry",
        "tool_count": len(tools),
        "tools": tools,
    }


def load_knowledge():
    if KNOWLEDGE_FILE.is_file():
        try:
            return json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Tool Knowledge Base tidak sah: {error}"
            ) from error
    return build_registry()
