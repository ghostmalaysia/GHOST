import sys
from pathlib import Path

LEARNING_DIR = Path.home() / "GHOST" / "core" / "learning"
sys.path.insert(0, str(LEARNING_DIR))

from knowledge_processor import process_url
from knowledge_analyzer import analyze_content


def learn_from_url(url):
    print("\n[1/3] Membaca sumber web...")

    processed = process_url(url)

    if processed.get("status") != "success":
        return {"error": processed.get("error", "Web reading failed")}

    reports = []

    for index, item in enumerate(processed["results"], 1):
        print(f"\n[2/3] Menganalisis sumber {index}...")

        analysis = analyze_content(
            item["content"],
            item["source_url"]
        )

        if analysis.get("status") != "success":
            reports.append({
                "source_url": item["source_url"],
                "error": analysis.get("error")
            })
            continue

        reports.append({
            "source_url": item["source_url"],
            "analysis": analysis["analysis"],
            "status": "analyzed"
        })

    print("\n[3/3] Menyediakan laporan...")

    return {
        "status": "success",
        "total_sources": len(reports),
        "reports": reports
    }


if __name__ == "__main__":
    print("================================")
    print(" GHOST KNOWLEDGE PIPELINE v1")
    print("================================")

    url = input("\nMasukkan URL untuk GHOST belajar: ").strip()

    result = learn_from_url(url)

    if result.get("status") == "success":
        print("\n========== KNOWLEDGE REPORT ==========")

        for index, report in enumerate(result["reports"], 1):
            print(f"\nSUMBER {index}")
            print("URL:", report["source_url"])

            if report.get("status") == "analyzed":
                print("\nANALISIS:")
                print(report["analysis"])
            else:
                print("\nRALAT:", report.get("error"))

        print("\nJumlah sumber:", result["total_sources"])

    else:
        print("\nPIPELINE FAILED:", result.get("error"))

    print("\nGHOST KNOWLEDGE PIPELINE SELESAI")
