
import json
import sys
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.paths import CONFIG_DIR

CONFIG = CONFIG_DIR / "tavily.env"


def read_web(url):
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
        "urls": [url]
    }).encode()

    request = urllib.request.Request(
        "https://api.tavily.com/extract",
        data=data,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode())

    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    url = input("Masukkan URL untuk GHOST baca: ").strip()

    result = read_web(url)

    if "error" in result:
        print("Gagal membaca:", result["error"])
    else:
        for item in result.get("results", []):
            print("\nGHOST WEB READER")
            print("URL:", item.get("url"))
            print("\nKANDUNGAN:")
            print(item.get("raw_content", "")[:5000])
