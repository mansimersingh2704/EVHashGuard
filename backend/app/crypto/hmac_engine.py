import hmac
import hashlib
import secrets
from typing import Optional


def generate_key(length: int = 32) -> bytes:
    """Generates a cryptographically secure random key using CSPRNG."""
    return secrets.token_bytes(length)


def compute_hmac_sha3_256(message: bytes, key: bytes) -> str:
    """Computes HMAC using SHA3-256 digest function."""
    if not isinstance(message, bytes):
        raise TypeError("Message must be bytes")
    if not isinstance(key, bytes):
        raise TypeError("Key must be bytes")
    return hmac.new(key, message, hashlib.sha3_256).hexdigest()


def verify_hmac_sha3_256(message: bytes, key: bytes, tag: str) -> bool:
    """
    Verifies HMAC using constant-time comparison to prevent timing side-channel attacks.
    Safely handles non-string or malformed tag inputs.
    """
    if not isinstance(tag, str) or not tag:
        return False
    try:
        expected = compute_hmac_sha3_256(message, key)
        return hmac.compare_digest(expected.lower(), tag.strip().lower())
    except Exception:
        return False
