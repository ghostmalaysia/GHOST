import os
import json
import hmac
import hashlib
import secrets
import getpass
import argparse
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"
AUTH_FILE = CONFIG_DIR / "owner_auth.json"

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
HASH_LENGTH = 32


def derive_hash(passphrase, salt):
    return hashlib.scrypt(
        passphrase.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=HASH_LENGTH
    )


def setup_owner_auth():
    if AUTH_FILE.exists() or AUTH_FILE.is_symlink():
        raise FileExistsError(
            "Owner authentication already exists. Refusing overwrite."
        )

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, 0o700)

    first = getpass.getpass("Create owner passphrase: ")
    second = getpass.getpass("Confirm owner passphrase: ")

    if len(first) < 14:
        raise ValueError("Passphrase must contain at least 14 characters.")

    if first != second:
        raise ValueError("Passphrases do not match.")

    salt = secrets.token_bytes(16)
    digest = derive_hash(first, salt)

    record = {
        "version": 1,
        "algorithm": "scrypt",
        "n": SCRYPT_N,
        "r": SCRYPT_R,
        "p": SCRYPT_P,
        "salt": salt.hex(),
        "hash": digest.hex()
    }

    fd, temp_path = tempfile.mkstemp(
        prefix=".owner_auth_",
        dir=str(CONFIG_DIR)
    )

    try:
        os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(record, file, indent=2)
            file.flush()
            os.fsync(file.fileno())

        if AUTH_FILE.exists() or AUTH_FILE.is_symlink():
            raise FileExistsError("Authentication file already exists.")

        os.replace(temp_path, AUTH_FILE)
        os.chmod(AUTH_FILE, 0o600)

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    print("Owner authentication enrolled.")
    print("Passphrase stored as a scrypt hash.")
    print("Authentication file permission: 600")


def verify_owner_auth():
    if not AUTH_FILE.is_file() or AUTH_FILE.is_symlink():
        print("Owner authentication is not configured.")
        return False

    try:
        record = json.loads(AUTH_FILE.read_text(encoding="utf-8"))

        if (
            record.get("version") != 1
            or record.get("algorithm") != "scrypt"
            or record.get("n") != SCRYPT_N
            or record.get("r") != SCRYPT_R
            or record.get("p") != SCRYPT_P
        ):
            print("Invalid authentication configuration.")
            return False

        salt = bytes.fromhex(record["salt"])
        expected = bytes.fromhex(record["hash"])

        if len(salt) != 16 or len(expected) != HASH_LENGTH:
            print("Invalid authentication data.")
            return False

        entered = getpass.getpass("Owner passphrase: ")
        actual = derive_hash(entered, salt)

        if hmac.compare_digest(actual, expected):
            print("OWNER AUTHENTICATION: VERIFIED")
            return True

        print("OWNER AUTHENTICATION: DENIED")
        return False

    except (OSError, ValueError, KeyError, TypeError):
        print("Authentication data invalid or unreadable.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="GHOST Owner Authentication"
    )
    parser.add_argument(
        "action",
        choices=["setup", "verify", "status"]
    )
    args = parser.parse_args()

    if args.action == "setup":
        setup_owner_auth()

    elif args.action == "verify":
        if not verify_owner_auth():
            raise SystemExit(1)

    elif args.action == "status":
        if AUTH_FILE.is_file() and not AUTH_FILE.is_symlink():
            print("Owner authentication: CONFIGURED")
            print("Stored format: scrypt hash")
        else:
            print("Owner authentication: NOT CONFIGURED")


if __name__ == "__main__":
    main()
