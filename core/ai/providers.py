"""Small provider adapters using Python's standard library."""

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from core.paths import CONFIG_DIR, PROJECT_DIR


DEFAULT_CONFIG = {
    "default": "qwen",
    "providers": {
        "qwen": {
            "type": "openai_compatible",
            "base_url": "http://127.0.0.1:8080/v1",
            "model": "qwen",
            "timeout": 180,
        }
    },
}


class ProviderError(RuntimeError):
    """Raised when a provider is missing or returns an unusable response."""


def _config_path():
    override = os.environ.get("GHOST_AI_CONFIG")
    return Path(override).expanduser() if override else CONFIG_DIR / "ai_providers.json"


def _load_local_secrets():
    """Load simple KEY=VALUE secrets without printing or overwriting the env."""
    path = CONFIG_DIR / "ai_secrets.env"
    if not path.is_file():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ProviderError(f"Tidak dapat membaca fail rahsia AI: {error}") from error
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if key and key.replace("_", "").isalnum() and not os.environ.get(key):
            os.environ[key] = value.strip().strip("\"'")


def load_config():
    _load_local_secrets()
    path = _config_path()
    if not path.is_file():
        return DEFAULT_CONFIG
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProviderError(f"Tidak dapat membaca konfigurasi AI: {error}") from error
    if not isinstance(config, dict) or not isinstance(config.get("providers"), dict):
        raise ProviderError("Konfigurasi AI mesti mengandungi objek 'providers'.")
    if not config["providers"]:
        raise ProviderError("Tiada penyedia AI dikonfigurasi.")
    if not all(isinstance(settings, dict) for settings in config["providers"].values()):
        raise ProviderError("Setiap penyedia dalam konfigurasi AI mesti berupa objek.")
    default_name = config.get("default")
    if not default_name:
        default_name = next(iter(config["providers"]))
        config["default"] = default_name
    if default_name and default_name not in config["providers"]:
        raise ProviderError("Penyedia lalai tidak tersenarai dalam objek 'providers'.")
    return config


def list_providers():
    config = load_config()
    rows = []
    for name, settings in config["providers"].items():
        kind = settings.get("type")
        if kind in ("claude_cli", "opencode_cli"):
            command = settings.get("command") or (
                "claude" if kind == "claude_cli" else "opencode"
            )
            available = shutil.which(command) is not None
            detail = "tersedia" if available else f"arahan '{command}' tiada dalam PATH sesi ini"
        elif kind == "openai_compatible":
            key_env = settings.get("api_key_env")
            base_url = settings.get("base_url", "")
            model = settings.get("model", "")
            available = bool(
                base_url and model
                and "YOUR_" not in base_url
                and "YOUR_" not in model
            )
            if key_env and not os.environ.get(key_env):
                available = False
                detail = f"tetapkan {key_env} dalam config/ai_secrets.env"
            elif not available:
                detail = "isi base_url dan model sebenar dalam konfigurasi"
            else:
                detail = "konfigurasi lengkap; sambungan diuji apabila dipanggil"
        elif kind == "anthropic":
            key_env = settings.get("api_key_env", "ANTHROPIC_API_KEY")
            available = bool(
                settings.get("model")
                and not settings.get("model", "").startswith("REPLACE_")
                and os.environ.get(key_env)
            )
            detail = (
                "konfigurasi dan kunci API tersedia; sambungan diuji apabila dipanggil"
                if available else f"isi model dan tetapkan {key_env} dalam config/ai_secrets.env"
            )
        else:
            available = False
            detail = f"jenis penyedia tidak dikenali: {kind}"
        rows.append({
            "name": name,
            "type": kind,
            "available": available,
            "network_provider": kind in ("openai_compatible", "anthropic"),
            "detail": detail,
        })
    return rows


def _messages_to_prompt(messages):
    return "\n\n".join(
        f"{item.get('role', 'user').upper()}: {item.get('content', '')}"
        for item in messages
    )


def _http_json(url, payload, headers, timeout):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")[:1000]
        raise ProviderError(f"HTTP {error.code} daripada penyedia AI: {details}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderError(f"Tidak dapat menghubungi penyedia AI: {error}") from error
    except json.JSONDecodeError as error:
        raise ProviderError("Penyedia AI memulangkan JSON yang tidak sah.") from error


def _call_openai_compatible(settings, messages):
    base_url = settings.get("base_url", "").rstrip("/")
    model = settings.get("model", "")
    if not base_url or not model:
        raise ProviderError("Penyedia OpenAI-compatible memerlukan base_url dan model.")
    headers = {}
    key_env = settings.get("api_key_env")
    api_key = os.environ.get(key_env, "") if key_env else ""
    if key_env and not api_key:
        raise ProviderError(f"Tetapkan {key_env} dalam config/ai_secrets.env.")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    result = _http_json(
        f"{base_url}/chat/completions",
        {
            "model": model,
            "messages": messages,
            "temperature": float(settings.get("temperature", 0.3)),
            "max_tokens": int(settings.get("max_tokens", 1200)),
            "stream": False,
        },
        headers,
        int(settings.get("timeout", 180)),
    )
    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise ProviderError("Format jawapan OpenAI-compatible tidak dikenali.") from error


def _call_anthropic(settings, messages):
    model = settings.get("model", "")
    key_env = settings.get("api_key_env", "ANTHROPIC_API_KEY")
    api_key = os.environ.get(key_env, "")
    if not model:
        raise ProviderError("Penyedia Anthropic memerlukan nama model dalam konfigurasi.")
    if not api_key:
        raise ProviderError(f"Tetapkan kunci API dalam pemboleh ubah {key_env} pada peranti anda.")
    system_parts = [m.get("content", "") for m in messages if m.get("role") == "system"]
    conversation = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in messages if m.get("role") in ("user", "assistant")
    ]
    result = _http_json(
        settings.get("base_url", "https://api.anthropic.com/v1/messages"),
        {
            "model": model,
            "system": "\n\n".join(system_parts),
            "messages": conversation,
            "max_tokens": int(settings.get("max_tokens", 1200)),
            "temperature": float(settings.get("temperature", 0.3)),
        },
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        int(settings.get("timeout", 180)),
    )
    try:
        return "\n".join(
            block["text"] for block in result["content"]
            if block.get("type") == "text"
        ).strip()
    except (KeyError, TypeError) as error:
        raise ProviderError("Format jawapan Anthropic tidak dikenali.") from error


def _call_cli(settings, messages, kind):
    command = settings.get("command") or ("claude" if kind == "claude_cli" else "opencode")
    executable = shutil.which(command)
    if not executable:
        raise ProviderError(f"Arahan '{command}' tiada dalam PATH sesi ini.")
    prompt = (
        "Jawab berdasarkan teks yang diberi sahaja. Jangan baca atau ubah fail, "
        "jangan jalankan arahan, dan jangan gunakan alat luaran.\n\n"
        + _messages_to_prompt(messages)
    )
    args = settings.get("args")
    if args is None:
        args = (
            ["--strict-mcp-config", "-p", "--tools", ""]
            if kind == "claude_cli"
            else ["run", "--agent", "ghost-collab"]
        )
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        raise ProviderError("'args' CLI mesti berupa senarai teks dalam konfigurasi.")
    pass_env = settings.get("pass_env", [])
    if not isinstance(pass_env, list) or not all(
        isinstance(name, str) and name.replace("_", "").isalnum()
        for name in pass_env
    ):
        raise ProviderError("'pass_env' CLI mesti berupa senarai nama pemboleh ubah.")
    sensitive_markers = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH")
    child_env = {
        name: value
        for name, value in os.environ.items()
        if not any(marker in name.upper() for marker in sensitive_markers)
    }
    for name in pass_env:
        if name in os.environ:
            child_env[name] = os.environ[name]
    try:
        result = subprocess.run(
            [executable, *args, prompt],
            capture_output=True,
            text=True,
            timeout=int(settings.get("timeout", 240)),
            check=False,
            cwd=str(PROJECT_DIR),
            env=child_env,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ProviderError(f"Gagal menjalankan penyedia {command}: {error}") from error
    if result.returncode:
        details = (result.stderr or result.stdout).strip()[:1000]
        raise ProviderError(f"{command} gagal (kod {result.returncode}): {details}")
    answer = result.stdout.strip()
    if not answer:
        raise ProviderError(f"{command} tidak memulangkan jawapan.")
    return answer


def ask(provider_name, messages):
    config = load_config()
    settings = config["providers"].get(provider_name)
    if not isinstance(settings, dict):
        raise ProviderError(f"Penyedia '{provider_name}' tiada dalam konfigurasi.")
    kind = settings.get("type")
    if kind == "openai_compatible":
        return _call_openai_compatible(settings, messages)
    if kind == "anthropic":
        return _call_anthropic(settings, messages)
    if kind in ("claude_cli", "opencode_cli"):
        return _call_cli(settings, messages, kind)
    raise ProviderError(f"Jenis penyedia '{kind}' tidak disokong.")
