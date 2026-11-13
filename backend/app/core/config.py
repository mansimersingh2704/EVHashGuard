import os
import json
import secrets
from typing import Dict, Optional, List, Tuple


class Settings:
    """
    EVHashGuard Core Configuration Settings.
    Supports environment variables with secure defaults for local development.
    """
    APP_TITLE: str = "EVHashGuard CSMS Cryptographic Wrapper"
    APP_VERSION: str = "2.1.0"
    
    # Database URL - default to persistent local file or Docker data volume
    DB_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./evhashguard.db")
    
    # Freshness window for replay protection (seconds)
    REPLAY_WINDOW_SECONDS: int = int(os.getenv("REPLAY_WINDOW_SECONDS", "300"))
    
    # Maximum clock drift permitted into future (seconds)
    MAX_CLOCK_SKEW_SECONDS: int = int(os.getenv("MAX_CLOCK_SKEW_SECONDS", "60"))
    
    # Strict downgrade policy - default is FALSE (downgrades forbidden)
    DOWNGRADE_ALLOWED: bool = os.getenv("DOWNGRADE_ALLOWED", "false").lower() in ("true", "1", "yes")
    
    # Primary Key Identifier for CSMS HMAC authentication
    DEFAULT_KEY_ID: str = os.getenv("EV_PRIMARY_KEY_ID", "key-active-csms-primary")
    
    # Explicit Allowed Origins for CORS (no wildcards when credentials enabled)
    ALLOWED_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]
    
    # Maximum HTTP request body size (1 MB limit)
    MAX_REQUEST_BYTES: int = int(os.getenv("MAX_REQUEST_BYTES", str(1024 * 1024)))


settings = Settings()


# ─── Stable Cryptographic Key Store ──────────────────────────────────────────
# Standard development/testing keys (stable across restarts).
# In production, keys are overridden via environment variable EV_KEY_<KEY_ID_HEX>
# or JSON in EV_KEY_REGISTRY.
_DEVELOPMENT_KEYS: Dict[str, bytes] = {
    "key-active-csms-primary": bytes.fromhex(
        "3a7d9f2e4c8b1a5d6e0f7c8b9a1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d"
    ),
    "key-backup-csms-2026": bytes.fromhex(
        "1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1d2c3b4a5f6e7d8c9b0a1f2e"
    ),
    "key-test-unit": bytes.fromhex(
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    ),
}


def _load_key_registry() -> Dict[str, bytes]:
    """
    Builds the active key store combining development defaults with environment secrets.
    Does NOT hardcode production secrets; environment overrides development defaults.
    """
    registry = dict(_DEVELOPMENT_KEYS)
    
    # 1. Check EV_KEY_REGISTRY_JSON env var
    env_registry_json = os.getenv("EV_KEY_REGISTRY_JSON")
    if env_registry_json:
        try:
            parsed = json.loads(env_registry_json)
            for kid, hex_val in parsed.items():
                registry[kid] = bytes.fromhex(hex_val)
        except Exception:
            pass  # Fallback to standard keys if JSON is malformed
            
    # 2. Check individual key environment variables: EV_KEY_<KEY_ID>
    for env_k, env_v in os.environ.items():
        if env_k.startswith("EV_KEY_"):
            kid = env_k[7:].lower().replace("_", "-")
            try:
                registry[kid] = bytes.fromhex(env_v)
            except ValueError:
                registry[kid] = env_v.encode("utf-8")
                
    return registry


_KEY_STORE: Dict[str, bytes] = _load_key_registry()


def get_key(key_id: str) -> Optional[bytes]:
    """
    Retrieves key material for a given key_id.
    Returns None if key_id is unrecognized (supporting strict unknown key rejection).
    """
    return _KEY_STORE.get(key_id)


def get_hmac_key(key_id: Optional[str] = None) -> bytes:
    """
    Returns key for default primary key_id or specified key_id.
    Raises ValueError if an unrecognized key_id is requested.
    """
    kid = key_id or settings.DEFAULT_KEY_ID
    key = get_key(kid)
    if key is None:
        raise ValueError(f"Unknown cryptographic key identifier: '{kid}'")
    return key


def list_registered_key_ids() -> List[str]:
    """Returns list of registered key identifiers without exposing key material."""
    return sorted(list(_KEY_STORE.keys()))


def register_ephemeral_key(key_id: str, key_bytes: bytes) -> None:
    """Registers an in-memory key (e.g. for testing dynamic key rotation)."""
    if len(key_bytes) < 16:
        raise ValueError("Key material must be at least 128 bits (16 bytes)")
    _KEY_STORE[key_id] = key_bytes
