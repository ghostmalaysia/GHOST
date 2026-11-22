from pathlib import Path
from urllib.parse import urlparse
import sys

BASE_DIR = Path.home() / "GHOST"
LEARNING_DIR = BASE_DIR / "core" / "learning"

sys.path.insert(0, str(LEARNING_DIR))

from web_reader import read_web
from content_cleaner import clean_content


def validate_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    if not parsed.hostname:
        return False

    return True


def process_url(url):
    if not validate_url(url):
        return {"error": "URL tidak sah. Gunakan alamat HTTP atau HTTPS."}

    print("\nGHOST: Sedang membaca sumber...")

    result = read_web(url)

    if "error" in result:
        return {"error": result["error"]}

    processed_items = []

    for item in result.get("results", []):
        original_url = item.get("url", url)
        raw_content = item.get("raw_content", "")

        cleaned_content = clean_content(raw_content)

        if not cleaned_content:
            continue

        processed_items.append({
            "source_url": original_url,
            "content": cleaned_content,
            "status": "processed"
        })

    if not processed_items:
        return {"error": "Tiada kandungan yang boleh diproses."}

    return {
        "status": "success",
        "total_sources": len(processed_items),
        "results": processed_items
    }


if __name__ == "__main__":
    print("================================")
    print(" GHOST KNOWLEDGE PROCESSOR v1")
    print("================================")

    url = input("\nMasukkan URL: ").strip()

    output = process_url(url)

    if "error" in output:
        print("\nGAGAL:", output["error"])
    else:
        print("\nSTATUS: BERJAYA")
        print("Jumlah sumber:", output["total_sources"])

        for index, item in enumerate(output["results"], 1):
            print("\n--------------------------------")
            print("SUMBER:", index)
            print("URL:", item["source_url"])
            print("STATUS:", item["status"])
            print("\nKANDUNGAN BERSIH:")
            print(item["content"][:5000])

    print("\nGHOST KNOWLEDGE PROCESSOR SELESAI")
