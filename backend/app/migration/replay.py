from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.db import ConsumedNonce


class PersistentReplayProtection:
    """
    Persistent Replay Protection Engine backed by SQLite.
    Guarantees atomic nonce consumption, freshness window verification,
    and replay rejection across server restarts and concurrent requests.
    """

    @classmethod
    def validate_timestamp_freshness(
        cls,
        timestamp_str: str,
        window_seconds: Optional[int] = None,
        max_skew_seconds: Optional[int] = None,
    ) -> Tuple[bool, Optional[datetime], str]:
        """
        Validates ISO8601 timestamp string against configured freshness window and clock skew.
        """
        if not isinstance(timestamp_str, str) or not timestamp_str.strip():
            return False, None, "REPLAY_ERROR: Missing or empty timestamp"

        try:
            # Parse ISO 8601 (handles 'Z' and offset formats)
            clean_ts = timestamp_str.replace("Z", "+00:00")
            msg_dt = datetime.fromisoformat(clean_ts)
            if msg_dt.tzinfo is None:
                msg_dt = msg_dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            return False, None, f"REPLAY_ERROR: Malformed ISO 8601 timestamp ({e})"

        now = datetime.now(timezone.utc)
        allowed_window = window_seconds if window_seconds is not None else settings.REPLAY_WINDOW_SECONDS
        allowed_skew = max_skew_seconds if max_skew_seconds is not None else settings.MAX_CLOCK_SKEW_SECONDS

        # Check future timestamp (clock drift)
        if msg_dt > now + timedelta(seconds=allowed_skew):
            drift = (msg_dt - now).total_seconds()
            return False, msg_dt, f"REPLAY_ERROR: Timestamp is in the future by {drift:.1f}s (max skew {allowed_skew}s)"

        # Check stale timestamp (expired outside window)
        if now - msg_dt > timedelta(seconds=allowed_window):
            age = (now - msg_dt).total_seconds()
            return False, msg_dt, f"REPLAY_ERROR: Timestamp expired. Age is {age:.1f}s (freshness window {allowed_window}s)"

        return True, msg_dt, "Timestamp within valid freshness window"

    @classmethod
    async def check_and_consume_nonce(
        cls,
        session: AsyncSession,
        nonce: str,
        timestamp_str: str,
        station_id: Optional[str] = None,
        window_seconds: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Atomically checks if a nonce has been consumed and registers it in SQLite.
        Returns (is_valid, reason).
        """
        if not isinstance(nonce, str) or not nonce.strip():
            return False, "REPLAY_ERROR: Missing or invalid nonce/message_id"

        fresh, msg_dt, fresh_reason = cls.validate_timestamp_freshness(timestamp_str, window_seconds)
        if not fresh:
            return False, fresh_reason

        now = datetime.now(timezone.utc)
        allowed_window = window_seconds if window_seconds is not None else settings.REPLAY_WINDOW_SECONDS
        expires_at = now + timedelta(seconds=allowed_window)

        # 1. Query for existing consumed nonce
        existing_q = await session.execute(
            select(ConsumedNonce).where(ConsumedNonce.nonce == nonce.strip())
        )
        existing = existing_q.scalar_one_or_none()
        if existing is not None:
            return False, f"REPLAY_ATTACK_DETECTED: Nonce '{nonce}' has already been consumed at {existing.created_at.isoformat()}"

        # 2. Insert new consumed nonce record
        record = ConsumedNonce(
            nonce=nonce.strip(),
            station_id=station_id,
            message_timestamp=msg_dt,
            expires_at=expires_at,
        )
        session.add(record)

        try:
            await session.flush()
        except IntegrityError:
            # Handles atomic race conditions from concurrent duplicate requests
            await session.rollback()
            return False, f"REPLAY_ATTACK_DETECTED: Concurrent duplicate nonce '{nonce}' rejected"

        return True, "Nonce successfully consumed and registered"

    @classmethod
    async def cleanup_expired_nonces(cls, session: AsyncSession) -> int:
        """Purges nonces whose freshness window has expired to prevent unbounded table growth."""
        now = datetime.now(timezone.utc)
        res = await session.execute(
            delete(ConsumedNonce).where(ConsumedNonce.expires_at < now)
        )
        await session.commit()
        return res.rowcount or 0
