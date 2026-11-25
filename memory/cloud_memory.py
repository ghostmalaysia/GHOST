import os
import uuid
import sys
import getpass
import json
import urllib.error
import urllib.request
from urllib.parse import urlencode
from pathlib import Path
from datetime import datetime, timezone

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from core.paths import CONFIG_DIR


ENV_FILE = CONFIG_DIR / "supabase.env"
TABLE_URL = "/rest/v1/ghost_memories"


class CloudMemory:

    def __init__(self):
        self.url = ""
        self.api_key = ""
        self.token = ""
        self.owner_id = ""
        self.email = ""
        self.password = ""

        self._load_config()

    def _load_config(self):
        if not ENV_FILE.exists():
            raise RuntimeError("Fail konfigurasi Supabase tidak dijumpai.")

        config = {}

        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            value = value.strip().strip('"').strip("'")
            config[key] = value

        creds_file = CONFIG_DIR / "supabase_credentials"
        if creds_file.exists():
            for line in creds_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip('"').strip("'")

        self.url = config.get("SUPABASE_URL", "").rstrip("/")
        self.api_key = config.get("SUPABASE_KEY", "")
        self.email = config.get("SUPABASE_EMAIL", "").strip()
        self.password = config.get("SUPABASE_PASSWORD", "")

        if not self.url or not self.api_key:
            raise RuntimeError("Konfigurasi Supabase tidak lengkap.")

    def login(self):
        email = os.getenv("SUPABASE_EMAIL", "").strip() or self.email
        password = os.getenv("SUPABASE_PASSWORD", "") or self.password

        if not email:
            email = input("Email Supabase: ").strip()
        if not password:
            password = getpass.getpass("Password Supabase: ")

        data = self._request(
            "POST",
            f"{self.url}/auth/v1/token?grant_type=password",
            headers={"apikey": self.api_key},
            payload={"email": email, "password": password},
        )

        self.token = data.get("access_token", "")
        self.owner_id = data.get("user", {}).get("id", "")

        if not self.token or not self.owner_id:
            raise RuntimeError("Identiti pemilik tidak dapat disahkan.")

        print("GHOST CLOUD MEMORY: LOGIN BERJAYA")

    def _headers(self):
        if not self.token:
            raise RuntimeError("GHOST belum log masuk ke Supabase.")

        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _request(method, url, headers=None, payload=None, params=None):
        if params:
            url += ("&" if "?" in url else "?") + urlencode(params)
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request_headers = dict(headers or {})
        if body is not None:
            request_headers.setdefault("Content-Type", "application/json")
        request = urllib.request.Request(
            url,
            data=body,
            headers=request_headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(
                f"Supabase HTTP {error.code}: {details}"
            ) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise RuntimeError(f"Tidak dapat menghubungi Supabase: {error}") from error
        if not raw:
            return []
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise RuntimeError("Supabase memulangkan JSON yang tidak sah.") from error

    def remember(self, content, category="general", source_url=None):
        content = content.strip()
        category = category.strip() or "general"

        if not content:
            raise ValueError("Kandungan memori kosong.")

        record = {
            "id": str(uuid.uuid4()),
            "owner_id": self.owner_id,
            "category": category,
            "content": content,
            "source_url": source_url,
            "confidence": 1.0,
            "approved": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        return self._request(
            "POST",
            self.url + TABLE_URL,
            headers={
                **self._headers(),
                "Prefer": "return=representation"
            },
            payload=record,
        )

    def search(self, keyword, limit=10):
        if not keyword.strip():
            return []

        return self._request(
            "GET",
            self.url + TABLE_URL,
            headers=self._headers(),
            params={
                "select": "id,category,content,source_url,confidence,created_at",
                "owner_id": f"eq.{self.owner_id}",
                "approved": "eq.true",
                "content": f"ilike.*{keyword.strip()}*",
                "order": "created_at.desc",
                "limit": limit
            },
        )

    def show_all(self, limit=50):
        return self._request(
            "GET",
            self.url + TABLE_URL,
            headers=self._headers(),
            params={
                "select": "id,category,content,created_at",
                "owner_id": f"eq.{self.owner_id}",
                "approved": "eq.true",
                "order": "created_at.desc",
                "limit": limit
            },
        )

    def forget(self, memory_id):
        self._request(
            "DELETE",
            self.url + TABLE_URL,
            headers=self._headers(),
            params={
                "id": f"eq.{memory_id}",
                "owner_id": f"eq.{self.owner_id}"
            },
        )
        return True
