from pathlib import Path
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.utils.audit_signature import _encode_base64url  # noqa: E402


def main() -> None:
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )

    print(f"AUDIT_SIGNATURE_PRIVATE_KEY={_encode_base64url(private_bytes)}")
    print(f"AUDIT_SIGNATURE_PUBLIC_KEY={_encode_base64url(public_bytes)}")


if __name__ == "__main__":
    main()
