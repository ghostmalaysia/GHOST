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


if __name__ == "__main__":
    try:
        create_backup()
    except Exception as error:
        print(f"BACKUP FAILED: {error}")
        raise SystemExit(1)
