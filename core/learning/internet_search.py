
import json
import sys
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.paths import CONFIG_DIR

CONFIG = CONFIG_DIR / "tavily.env"


def search_web(query, max_results=5):
    if not CONFIG.exists():
        return {"error": "Tavily configuration not found"}

    api_key = ""
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            if key.strip().removeprefix("export ").strip() == "TAVILY_API_KEY":
                api_key = value.strip().strip("\"'")
                break
    if not api_key or api_key.startswith("YOUR_"):
        return {"error": "TAVILY_API_KEY is missing from config/tavily.env"}

    data = json.dumps({
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True
    }).encode()

    request = urllib.request.Request(
        "https://api.tavily.com/search",
        data=data,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Cara guna: python internet_search.py "topik carian"')
        sys.exit(0)

    query = " ".join(sys.argv[1:])
    result = search_web(query)

    if "error" in result:
        print("Carian gagal:", result["error"])
        sys.exit(1)

    print("\nGHOST INTERNET SEARCH")
    print("Carian:", query)

    if result.get("answer"):
        print("\nRingkasan Tavily:")
        print(result["answer"])

    for i, item in enumerate(result.get("results", []), 1):
        print(f"\n{i}. {item.get('title')}")
        print("URL:", item.get("url"))
        print("Ringkasan:", item.get("content", "")[:400])
