import uuid
import requests
import getpass
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path.home() / "GHOST"
ENV_FILE = BASE_DIR / "config" / "supabase.env"
TABLE_URL = "/rest/v1/ghost_memories"


class CloudMemory:

    def __init__(self):
        self.url = ""
        self.api_key = ""
        self.token = ""
        self.owner_id = ""

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

        self.url = config.get("SUPABASE_URL", "").rstrip("/")
        self.api_key = config.get("SUPABASE_KEY", "")

        if not self.url or not self.api_key:
            raise RuntimeError("Konfigurasi Supabase tidak lengkap.")

    def login(self):
        email = input("Email Supabase: ").strip()
        password = getpass.getpass("Password Supabase: ")

        response = requests.post(
            f"{self.url}/auth/v1/token?grant_type=password",
            headers={"apikey": self.api_key},
            json={"email": email, "password": password},
            timeout=30
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Log masuk Supabase gagal: HTTP {response.status_code}"
            )

        data = response.json()

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

        response = requests.post(
            self.url + TABLE_URL,
            headers={
                **self._headers(),
                "Prefer": "return=representation"
            },
            json=record,
            timeout=30
        )

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Gagal menyimpan memori: HTTP {response.status_code}"
            )

        return response.json()

    def search(self, keyword, limit=10):
        if not keyword.strip():
            return []

        response = requests.get(
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
            timeout=30
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Gagal mencari memori: HTTP {response.status_code}"
            )

        return response.json()

    def show_all(self, limit=50):
        response = requests.get(
            self.url + TABLE_URL,
            headers=self._headers(),
            params={
                "select": "id,category,content,created_at",
                "owner_id": f"eq.{self.owner_id}",
                "approved": "eq.true",
                "order": "created_at.desc",
                "limit": limit
            },
            timeout=30
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Gagal membaca memori: HTTP {response.status_code}"
            )

        return response.json()

    def forget(self, memory_id):
        response = requests.delete(
            self.url + TABLE_URL,
            headers=self._headers(),
            params={
                "id": f"eq.{memory_id}",
                "owner_id": f"eq.{self.owner_id}"
            },
            timeout=30
        )

        if response.status_code not in (200, 204):
            raise RuntimeError(
                f"Gagal memadam memori: HTTP {response.status_code}"
            )

        return True
