#!/usr/bin/env python3

import json
import subprocess
from datetime import datetime
from pathlib import Path


GHOST_DIR = Path.home() / "GHOST"
BACKUP_DIR = GHOST_DIR / "backups" / "automatic"


def run_git(*args):
    return subprocess.run(
        ["git", "-C", str(GHOST_DIR), *args],
        capture_output=True,
        text=True
    )


def create_backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Confirm this is a Git repository
    check = run_git("rev-parse", "--is-inside-work-tree")
    if check.returncode != 0:
        raise RuntimeError("GHOST Git repository not found.")

    # Do not back up while tracked files have uncommitted changes
    status = run_git("status", "--porcelain", "--untracked-files=no")
    if status.returncode != 0:
        raise RuntimeError(status.stderr.strip())

    if status.stdout.strip():
        raise RuntimeError(
            "Tracked files have uncommitted changes. "
            "Commit or review them before backup."
        )

    # Warn about untracked files; they are not included in Git Bundle
    untracked = run_git("ls-files", "--others", "--exclude-standard")
    if untracked.stdout.strip():
        print("WARNING: Untracked files are not included in this backup.")

    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    filename = f"GHOST-main-{timestamp}.bundle"
    final_path = BACKUP_DIR / filename
    temp_path = BACKUP_DIR / f".{filename}.tmp"

    try:
        # Create bundle from committed Git history
        result = run_git(
            "bundle", "create", str(temp_path), "--all"
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        # Verify bundle before keeping it
        verify = run_git("bundle", "verify", str(temp_path))
        if verify.returncode != 0:
            raise RuntimeError(verify.stderr.strip())

        temp_path.replace(final_path)

        commit = run_git("rev-parse", "HEAD").stdout.strip()

        metadata = {
            "project": "GHOST",
            "created_at": datetime.now().astimezone().isoformat(),
            "file": filename,
            "commit": commit,
            "type": "git_bundle",
            "verified": True
        }

        metadata_path = BACKUP_DIR / f"{filename}.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8"
        )

        print("BACKUP SUCCESS")
        print(f"File: {final_path}")
        print(f"Commit: {commit}")
        print("Integrity: VERIFIED")

    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise




def show_history():
    print("\n========== GHOST BACKUP HISTORY ==========\n")

    records = []

    for metadata_path in BACKUP_DIR.glob("*.bundle.json"):
        try:
            metadata = json.loads(
                metadata_path.read_text(encoding="utf-8")
            )

            backup_path = BACKUP_DIR / metadata["file"]

            records.append({
                "created_at": metadata.get("created_at", "Unknown"),
                "file": metadata["file"],
                "commit": metadata.get("commit", "Unknown"),
                "verified": metadata.get("verified", False),
                "exists": backup_path.is_file(),
                "size": backup_path.stat().st_size if backup_path.is_file() else 0
            })

        except (OSError, json.JSONDecodeError, KeyError):
            print(f"WARNING: Cannot read {metadata_path.name}")

    records.sort(
        key=lambda item: item["created_at"],
        reverse=True
    )

    if not records:
        print("No backup history found.")
        return

    for number, record in enumerate(records, start=1):
        size_kb = record["size"] / 1024

        print(f"Backup #{number}")
        print(f"Date: {record['created_at']}")
        print(f"File: {record['file']}")
        print(f"Commit: {record['commit']}")
        print(f"Integrity recorded: {'VERIFIED' if record['verified'] else 'NOT VERIFIED'}")
        print(f"File exists: {'YES' if record['exists'] else 'NO'}")
        print(f"Size: {size_kb:.2f} KB")
        print("------------------------------------------")

    print(f"Total backups recorded: {len(records)}")
    print("\n==========================================")


if __name__ == "__main__":
    import sys

    command = sys.argv[1].lower() if len(sys.argv) > 1 else "backup"

    try:
        if command == "history":
            show_history()
        elif command == "backup":
            create_backup()
        else:
            print("Usage: python backup_manager.py [backup|history]")
            raise SystemExit(2)
    except Exception as error:
        print(f"OPERATION FAILED: {error}")
        raise SystemExit(1)
