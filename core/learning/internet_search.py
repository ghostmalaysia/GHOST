
import json
import sys
import urllib.request
from pathlib import Path

CONFIG = Path.home() / "GHOST/config/tavily.env"


def search_web(query, max_results=5):
    if not CONFIG.exists():
        return {"error": "Tavily configuration not found"}

    line = CONFIG.read_text().strip()
    api_key = line.split("=", 1)[1].strip()

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
