import base64
import os
from functools import lru_cache

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.cores.config import settings


ENCRYPTED_PREFIX = "enc:v1:"


def _decode_key(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    try:
        key = base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception as exc:
        raise RuntimeError("FIELD_ENCRYPTION_KEY must be URL-safe base64.") from exc

    if len(key) not in (16, 24, 32):
        raise RuntimeError("FIELD_ENCRYPTION_KEY must decode to 16, 24, or 32 bytes.")

    return key


@lru_cache(maxsize=1)
def _aesgcm() -> AESGCM:
    if not settings.FIELD_ENCRYPTION_KEY:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is required to encrypt sensitive fields.")

    return AESGCM(_decode_key(settings.FIELD_ENCRYPTION_KEY))


def encrypt_text(value: str) -> str:
    if value.startswith(ENCRYPTED_PREFIX):
        return value

    nonce = os.urandom(12)
    ciphertext = _aesgcm().encrypt(nonce, value.encode("utf-8"), None)
    payload = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii").rstrip("=")
    return f"{ENCRYPTED_PREFIX}{payload}"


def decrypt_text(value: str) -> str:
    if not value.startswith(ENCRYPTED_PREFIX):
        # Backward compatibility for plaintext rows created before encryption.
        return value

    payload = value[len(ENCRYPTED_PREFIX):]
    padded = payload + "=" * (-len(payload) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    nonce, ciphertext = raw[:12], raw[12:]
    return _aesgcm().decrypt(nonce, ciphertext, None).decode("utf-8")


class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, length: int = 1024, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.length = length

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(String(self.length))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_text(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_text(value)
