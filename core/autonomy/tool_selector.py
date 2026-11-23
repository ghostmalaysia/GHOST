from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_FILE = BASE_DIR / "memory" / "tool_knowledge.json"

PROFILES = [
    {
        "name": "network_discovery",
        "keywords": ["scan network", "network scan", "discover hosts", "port scan", "nmap"],
        "tools": ["nmap"],
        "reason": "Network and service discovery"
    },
    {
        "name": "network_diagnostics",
        "keywords": ["network connection", "connectivity", "ping", "network diagnostic"],
        "tools": ["ping", "ip", "ss"],
        "reason": "Network connectivity and diagnostics"
    },
    {
        "name": "packet_analysis",
        "keywords": ["packet", "traffic analysis", "pcap", "packet capture", "tshark", "tcpdump"],
        "tools": ["tshark", "tcpdump"],
        "reason": "Network packet capture and analysis"
    },
    {
        "name": "python_development",
        "keywords": ["python", "python script", "automation", "python development"],
        "tools": ["python3", "python", "pip"],
        "reason": "Python development and automation"
    },
    {
        "name": "source_control",
        "keywords": ["git", "version control", "source code history"],
        "tools": ["git"],
        "reason": "Source code version control"
    },
    {
        "name": "postgres_database",
        "keywords": ["postgres", "postgresql", "postgres database"],
        "tools": ["psql"],
        "reason": "PostgreSQL database access"
    },
    {
        "name": "sqlite_database",
        "keywords": ["sqlite", "sqlite database"],
        "tools": ["sqlite3"],
        "reason": "SQLite database access"
    },
    {
        "name": "file_search",
        "keywords": ["find file", "search files", "search text", "find folder"],
        "tools": ["find", "grep"],
        "reason": "File and text searching"
    },
    {
        "name": "secure_transfer",
        "keywords": ["secure remote connection", "ssh connection", "remote shell"],
        "tools": ["ssh"],
        "reason": "Secure remote system connection"
    }
]


def load_knowledge():
    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError("Tool Knowledge Base not found.")
    return json.loads(KNOWLEDGE_FILE.read_text())


def select_tools(task):
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Task description must not be empty.")

    query = task.lower()
    knowledge = load_knowledge()
    selected_profile = None

    for profile in PROFILES:
        if any(keyword in query for keyword in profile["keywords"]):
            selected_profile = profile
            break

    if selected_profile is None:
        return {
            "task": task,
            "status": "needs_clarification",
            "message": "No reliable tool profile matched this task.",
            "tools": [],
            "execution_performed": False
        }

    recommendations = []

    for name in selected_profile["tools"]:
        item = knowledge["tools"].get(name)
        if not item:
            continue

        available = [
            env for env, details in item["availability"].items()
            if details.get("available")
        ]

        recommendations.append({
            "name": name,
            "description": item["description"],
            "available_in": available,
            "risk_level": item["risk_level"],
            "availability_status": "available" if available else "unavailable"
        })

    available_tools = [
        item for item in recommendations
        if item["availability_status"] == "available"
    ]

    return {
        "task": task,
        "profile": selected_profile["name"],
        "reason": selected_profile["reason"],
        "status": "ready" if available_tools else "no_tools_available",
        "recommended_tools": recommendations,
        "available_tools": available_tools,
        "execution_performed": False
    }


if __name__ == "__main__":
    tests = [
        "Analyze network packet capture",
        "Develop a Python script",
        "Scan network",
        "Connect to PostgreSQL database",
        "Use SQLite database"
    ]

    print("=== GHOST TOOL SELECTION ENGINE ===")

    for task in tests:
        result = select_tools(task)
        print("\nTASK:", task)
        print("PROFILE:", result.get("profile", "None"))
        print("STATUS:", result["status"])

        for tool in result.get("recommended_tools", []):
            print(
                " -", tool["name"],
                "| Available:", ", ".join(tool["available_in"]) or "None",
                "| Risk:", tool["risk_level"]
            )

    print("\nExecution performed: False")
