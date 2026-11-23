import platform
import shutil
import sys


TOOL_CATEGORIES = {
    "system": [
        "bash", "sh", "uname", "whoami", "ps", "top",
        "df", "free", "du", "uptime"
    ],
    "programming": [
        "python", "python3", "git", "gcc", "clang",
        "cmake", "make", "node", "npm", "php", "ruby"
    ],
    "networking": [
        "curl", "wget", "ssh", "ping", "traceroute",
        "nmap", "ip", "ss", "netstat"
    ],
    "database": [
        "sqlite3", "psql", "mysql"
    ],
    "security": [
        "openssl", "gpg", "nmap", "tcpdump", "tshark"
    ],
    "package_management": [
        "pkg", "apt", "apt-get", "dpkg", "pip"
    ],
    "file_management": [
        "tar", "zip", "unzip", "jq", "find", "grep"
    ],
    "android": [
        "termux-info", "termux-setup-storage", "nethunter"
    ]
}


def discover_tools():
    results = {}

    for category, tools in TOOL_CATEGORIES.items():
        results[category] = {}

        for tool in tools:
            path = shutil.which(tool)
            results[category][tool] = {
                "available": path is not None,
                "path": path
            }

    return results


def system_info():
    return {
        "system": platform.system(),
        "platform": sys.platform,
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "release": platform.release()
    }


def report():
    info = system_info()
    tools = discover_tools()

    total = 0
    available = 0

    print("=== GHOST TOOL DISCOVERY ===")
    print("System:", info["system"])
    print("Platform:", info["platform"])
    print("Architecture:", info["architecture"])
    print("Python:", info["python_version"])
    print()

    for category, entries in tools.items():
        print("[" + category.upper() + "]")

        for name, details in entries.items():
            total += 1

            if details["available"]:
                available += 1
                print("  [FOUND]", name, "->", details["path"])
            else:
                print("  [NOT FOUND]", name)

        print()

    print("=== SUMMARY ===")
    print("Tools detected:", available, "/", total)
    print("Discovery mode: READ-ONLY")
    print("No tools installed, removed or executed.")


if __name__ == "__main__":
    report()
