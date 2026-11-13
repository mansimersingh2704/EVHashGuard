import secrets


class Settings:
    DB_URL: str = "sqlite+aiosqlite:///./evhashguard.db"
    REPLAY_WINDOW_SECONDS: int = 300
    APP_VERSION: str = "1.0.0"
    DOWNGRADE_ALLOWED: bool = False


settings = Settings()

# HMAC key generated at startup - never hardcoded in code
_HMAC_KEY: bytes = secrets.token_bytes(32)


def get_hmac_key() -> bytes:
    return _HMAC_KEY
