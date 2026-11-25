"""Shared filesystem locations for GHOST.

By default, data lives beside this source checkout. Set GHOST_HOME to keep
using a different installation directory or to place data elsewhere.
"""

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
_configured_home = os.environ.get("GHOST_HOME")
_legacy_home = Path.home() / "GHOST"
if _configured_home:
    BASE_DIR = Path(_configured_home).expanduser()
elif _legacy_home.is_dir() and _legacy_home.resolve() != PROJECT_DIR:
    BASE_DIR = _legacy_home
else:
    BASE_DIR = PROJECT_DIR
CONFIG_DIR = BASE_DIR / "config"
MEMORY_DIR = BASE_DIR / "memory"
IDENTITY_FILE = PROJECT_DIR / "core" / "identity" / "ghost_identity.txt"
