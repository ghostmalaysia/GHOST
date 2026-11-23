import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from core.autonomy.tool_discovery import TOOL_CATEGORIES

INVENTORY_FILE = BASE_DIR / "memory" / "tool_inventory.json"
OUTPUT_FILE = BASE_DIR / "memory" / "tool_knowledge.json"

TOOL_INFO = {
    "bash": ("Command-line shell", "Run shell commands and scripts", 3),
    "sh": ("POSIX shell", "Run basic shell commands and scripts", 3),
    "python": ("Python interpreter", "Automation, analysis and development", 2),
    "python3": ("Python 3 interpreter", "Automation, analysis and development", 2),
    "git": ("Version control", "Track source code and project history", 2),
    "gcc": ("C compiler", "Compile C programs", 2),
    "clang": ("C/C++ compiler", "Compile and develop native software", 2),
    "cmake": ("Build system generator", "Configure software builds", 2),
    "make": ("Build automation", "Run project build instructions", 2),
    "node": ("JavaScript runtime", "Run JavaScript applications", 2),
    "npm": ("Node package manager", "Manage JavaScript packages", 3),
    "curl": ("Network transfer tool", "Send HTTP requests and retrieve data", 2),
    "wget": ("Download utility", "Retrieve files from network sources", 2),
    "ssh": ("Secure remote shell", "Connect to authorized remote systems", 3),
    "ping": ("Network diagnostic", "Check network reachability", 1),
    "nmap": ("Network scanner", "Discover hosts and services in authorized scope", 3),
    "ip": ("Network configuration utility", "Inspect and manage network interfaces", 2),
    "ss": ("Socket inspection", "Inspect network connections and listening ports", 1),
    "netstat": ("Network statistics", "Inspect network connections and routes", 1),
    "ps": ("Process viewer", "Inspect running processes", 1),
    "top": ("System monitor", "Monitor processes and resource usage", 1),
    "df": ("Disk space utility", "Inspect filesystem capacity", 1),
    "free": ("Memory monitor", "Inspect RAM and swap usage", 1),
    "du": ("Disk usage utility", "Inspect directory storage usage", 1),
    "uptime": ("System status utility", "Inspect uptime and load", 1),
    "uname": ("System information", "Identify kernel and system architecture", 1),
    "whoami": ("Identity utility", "Inspect current user identity", 1),
    "sqlite3": ("SQLite database tool", "Inspect and manage SQLite databases", 3),
    "psql": ("PostgreSQL client", "Connect to authorized PostgreSQL databases", 3),
    "mysql": ("MySQL client", "Connect to authorized MySQL databases", 3),
    "openssl": ("Cryptography toolkit", "Inspect certificates and perform cryptographic operations", 3),
    "gpg": ("Encryption and signing tool", "Verify signatures and manage encrypted data", 3),
    "tcpdump": ("Packet capture tool", "Capture network traffic in authorized environments", 3),
    "tshark": ("Network protocol analyzer", "Analyze packet captures and network traffic", 3),
    "pkg": ("Termux package manager", "Manage packages in Termux", 3),
    "apt": ("Package manager", "Install and manage system packages", 3),
    "apt-get": ("Package manager interface", "Manage system packages", 3),
    "dpkg": ("Package management utility", "Inspect and manage Debian packages", 3),
    "pip": ("Python package manager", "Manage Python packages", 3),
    "tar": ("Archive utility", "Create and inspect archive files", 2),
    "zip": ("Archive utility", "Create ZIP archives", 2),
    "unzip": ("Archive utility", "Extract ZIP archives", 2),
    "jq": ("JSON processor", "Read and transform JSON data", 2),
    "find": ("File search utility", "Locate files and directories", 2),
    "grep": ("Text search utility", "Search text and source files", 1),
    "termux-info": ("Termux diagnostics", "Inspect Termux environment information", 1),
    "termux-setup-storage": ("Android storage permission tool", "Request access to shared Android storage", 3),
    "nethunter": ("Kali NetHunter launcher", "Access the configured Kali environment", 3),
    "php": ("PHP interpreter", "Run PHP applications and scripts", 2),
    "ruby": ("Ruby interpreter", "Run Ruby applications and scripts", 2),
    "traceroute": ("Network route diagnostic", "Inspect network paths to a destination", 2),
}

def build_knowledge_base():
    if not INVENTORY_FILE.exists():
        raise FileNotFoundError("Tool inventory not found. Run tool_inventory.py first.")

    inventory = json.loads(INVENTORY_FILE.read_text())
    environments = inventory.get("environments", {})
    categories_by_tool = {}

    for category, names in TOOL_CATEGORIES.items():
        for name in names:
            categories_by_tool.setdefault(name, []).append(category)

    tools = {}

    for name, categories in categories_by_tool.items():
        description, purpose, risk = TOOL_INFO.get(
            name,
            ("Unclassified tool", "Purpose requires further research", 2)
        )

        availability = {}
        for env, entries in environments.items():
            details = entries.get(name, {})
            availability[env] = {
                "available": bool(details.get("available")),
                "path": details.get("path")
            }

        tools[name] = {
            "name": name,
            "categories": categories,
            "description": description,
            "typical_uses": purpose,
            "risk_level": risk,
            "availability": availability,
            "execution_status": "not_executed",
            "permission_required": (
                "Owner authorization according to task scope and risk"
            ),
            "knowledge_status": (
                "basic" if name in TOOL_INFO else "needs_research"
            )
        }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_inventory": str(INVENTORY_FILE.relative_to(BASE_DIR)),
        "tool_count": len(tools),
        "tools": tools
    }

    OUTPUT_FILE.write_text(json.dumps(result, indent=2))
    return result

def search_tools(keyword):
    data = json.loads(OUTPUT_FILE.read_text())
    keyword = keyword.lower()
    return [
        item for item in data["tools"].values()
        if keyword in item["name"].lower()
        or keyword in item["description"].lower()
        or any(keyword in c for c in item["categories"])
        or keyword in item["typical_uses"].lower()
    ]

def report():
    data = build_knowledge_base()
    print("=== GHOST TOOL KNOWLEDGE BASE ===")
    print("Tools recorded:", data["tool_count"])
    print("Knowledge file:", OUTPUT_FILE)
    print("Basic descriptions:", sum(
        1 for item in data["tools"].values()
        if item["knowledge_status"] == "basic"
    ))
    print("Needs further research:", sum(
        1 for item in data["tools"].values()
        if item["knowledge_status"] == "needs_research"
    ))
    print("Tools executed: 0")
    print("Mode: KNOWLEDGE ONLY — no tool execution")

if __name__ == "__main__":
    report()
