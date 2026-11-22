
import json
import urllib.request
from pathlib import Path

CONFIG = Path.home() / "GHOST/config/tavily.env"


def read_web(url):
    if not CONFIG.exists():
        return {"error": "Tavily configuration not found"}

    line = CONFIG.read_text().strip()
    api_key = line.split("=", 1)[1].strip()

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
