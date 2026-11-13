from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Index
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    pass


class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, unique=True, index=True, nullable=False)
    vendor = Column(String, nullable=False)
    model = Column(String, nullable=False)
    firmware_version = Column(String, nullable=False)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FirmwareMessage(Base):
    __tablename__ = "firmware_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True, nullable=False)
    station_id = Column(String, index=True, nullable=False)
    message_type = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    legacy_integrity = Column(String, nullable=True)  # MD5 hash (legacy/vendor-specific)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_firmware_messages_station_created", "station_id", "created_at"),
    )


class IntegrityCheck(Base):
    __tablename__ = "integrity_checks"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, index=True, nullable=False)
    algorithm = Column(String, nullable=False)
    digest = Column(String, nullable=False)
    verification_status = Column(String, nullable=False)  # PASS, FAIL, UNKNOWN
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MigrationEvent(Base):
    __tablename__ = "migration_events"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, index=True, nullable=False)
    from_algorithm = Column(String, nullable=False)
    to_algorithm = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AttackSimulation(Base):
    __tablename__ = "attack_simulations"

    id = Column(Integer, primary_key=True, index=True)
    attack_type = Column(String, nullable=False)
    detected = Column(Boolean, nullable=False)
    input_summary = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True, nullable=False)
    station_id = Column(String, index=True, nullable=True)
    algorithm = Column(String, nullable=True)
    status = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_security_audit_logs_event_created", "event_type", "created_at"),
    )


class CryptographicConfiguration(Base):
    __tablename__ = "cryptographic_configurations"

    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String, unique=True, index=True, nullable=False)
    algorithm = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    # NO plaintext keys stored - key material is never persisted in database
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ConsumedNonce(Base):
    """
    Persistent Replay Protection Ledger.
    Stores consumed nonces and message identifiers in SQLite to prevent replay attacks
    across concurrent sessions and server restarts.
    """
    __tablename__ = "consumed_nonces"

    id = Column(Integer, primary_key=True, index=True)
    nonce = Column(String(128), unique=True, index=True, nullable=False)
    station_id = Column(String(64), index=True, nullable=True)
    message_timestamp = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_consumed_nonces_nonce_unique", "nonce", unique=True),
        Index("ix_consumed_nonces_expires", "expires_at"),
    )


async_engine = create_async_engine(settings.DB_URL, echo=False)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def create_tables():
    """Initializes SQLite database schema and creates all tables and indexes."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI async dependency yielding an active SQLAlchemy session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
