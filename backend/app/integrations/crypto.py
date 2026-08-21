import json
from functools import lru_cache

from cryptography.fernet import Fernet

from app.config import get_settings


@lru_cache
def _fernet() -> Fernet:
    settings = get_settings()
    if not settings.credential_encryption_key:
        raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY is not set; see SETUP.md")
    return Fernet(settings.credential_encryption_key.encode())


def encrypt_payload(data: dict) -> bytes:
    return _fernet().encrypt(json.dumps(data).encode())


def decrypt_payload(token: bytes) -> dict:
    return json.loads(_fernet().decrypt(token).decode())
