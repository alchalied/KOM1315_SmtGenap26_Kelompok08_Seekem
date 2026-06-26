import base64
import json
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.cores.config import settings


AUDIT_SIGNATURE_ALGORITHM = "Ed25519"


def _decode_key(value: str, key_name: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    try:
        key = base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception as exc:
        raise RuntimeError(f"{key_name} must be URL-safe base64.") from exc

    if len(key) != 32:
        raise RuntimeError(f"{key_name} must decode to 32 bytes.")

    return key


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_base64url(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


@lru_cache(maxsize=1)
def _private_key() -> Ed25519PrivateKey | None:
    if not settings.AUDIT_SIGNATURE_PRIVATE_KEY:
        return None
    return Ed25519PrivateKey.from_private_bytes(
        _decode_key(settings.AUDIT_SIGNATURE_PRIVATE_KEY, "AUDIT_SIGNATURE_PRIVATE_KEY")
    )


@lru_cache(maxsize=1)
def _public_key() -> Ed25519PublicKey | None:
    if settings.AUDIT_SIGNATURE_PUBLIC_KEY:
        return Ed25519PublicKey.from_public_bytes(
            _decode_key(settings.AUDIT_SIGNATURE_PUBLIC_KEY, "AUDIT_SIGNATURE_PUBLIC_KEY")
        )

    private_key = _private_key()
    if private_key is None:
        return None

    return private_key.public_key()


def is_audit_signature_configured() -> bool:
    return _private_key() is not None


def public_key_from_private_key(private_key_value: str) -> str:
    private_key = Ed25519PrivateKey.from_private_bytes(
        _decode_key(private_key_value, "AUDIT_SIGNATURE_PRIVATE_KEY")
    )
    public_key = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )
    return _encode_base64url(public_key)


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat(timespec="microseconds")


def _canonical_payload(log: Any) -> bytes:
    payload = {
        "actor_user_id": log.actor_user_id,
        "actor_email": log.actor_email,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "detail": log.detail,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "success": bool(log.success),
        "created_at": _format_datetime(log.created_at),
    }
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sign_audit_log(log: Any) -> str | None:
    private_key = _private_key()
    if private_key is None:
        return None

    signature = private_key.sign(_canonical_payload(log))
    return _encode_base64url(signature)


def verify_audit_log_signature(log: Any) -> bool | None:
    if not log.signature:
        return None
    if log.signature_algorithm != AUDIT_SIGNATURE_ALGORITHM:
        return False

    public_key = _public_key()
    if public_key is None:
        return None

    try:
        public_key.verify(_decode_base64url(log.signature), _canonical_payload(log))
    except (InvalidSignature, ValueError):
        return False

    return True
