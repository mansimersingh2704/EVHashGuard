import hmac
import hashlib
import secrets
from typing import Optional


def generate_key(length: int = 32) -> bytes:
    """Generates a cryptographically secure random key."""
    return secrets.token_bytes(length)


def compute_hmac_sha3_256(message: bytes, key: bytes) -> str:
    """Computes HMAC using SHA3-256 digest function."""
    return hmac.new(key, message, hashlib.sha3_256).hexdigest()


def verify_hmac_sha3_256(message: bytes, key: bytes, tag: str) -> bool:
    """
    Verifies HMAC using constant-time comparison to prevent timing side-channel attacks.
    """
    expected = compute_hmac_sha3_256(message, key)
    return hmac.compare_digest(expected, tag)
