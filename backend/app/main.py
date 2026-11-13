import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select, func

from app.core.config import settings
from app.database.db import (
    create_tables,
    async_session_maker,
    ChargingStation,
    SecurityAuditLog,
)
from app.ev_simulator.message_generator import CHARGING_STATIONS
from app.api import (
    hash_routes,
    collision_routes,
    ev_routes,
    legacy_routes,
    migration_routes,
    attack_routes,
    risk_routes,
    dashboard_routes,
    audit_routes,
)

logger = logging.getLogger("evhashguard")


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Protects CSMS endpoints against Denial of Service (DoS) from oversized payload injections.
    Rejects requests exceeding MAX_REQUEST_BYTES with HTTP 413 Payload Too Large.
    """
    def __init__(self, app: FastAPI, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "PAYLOAD_TOO_LARGE",
                            "detail": f"Request size exceeds maximum allowed boundary ({self.max_bytes} bytes)",
                        },
                    )
            except ValueError:
                pass
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema and indexes exist
    await create_tables()

    # Seed baseline charging stations if database is fresh
    async with async_session_maker() as session:
        result = await session.execute(select(func.count()).select_from(ChargingStation))
        count = result.scalar() or 0
        if count == 0:
            for st in CHARGING_STATIONS:
                session.add(
                    ChargingStation(
                        station_id=st["station_id"],
                        vendor=st["vendor"],
                        model=st["model"],
                        firmware_version=st["firmware_version"],
                        location=st["location"],
                    )
                )
            # Add initial system startup audit record
            session.add(
                SecurityAuditLog(
                    event_type="SYSTEM_INITIALIZATION",
                    station_id="CS-SYSTEM-CORE",
                    algorithm="SHA3-256 / HMAC-SHA3-256",
                    status="READY",
                    details=f"EVHashGuard Core v{settings.APP_VERSION} initialized with persistent replay ledger.",
                )
            )
            await session.commit()
    yield


app = FastAPI(
    title=settings.APP_TITLE,
    description="Backward-Compatible Cryptographic Integrity Framework for Legacy OCPP 1.6 EV Charging Systems",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 1. Request Size Limitation
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.MAX_REQUEST_BYTES)

# 2. Strict CORS Configuration (No wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
)

# 3. Global Exception Handler (Safe error responses without traceback leakage)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected cryptographic or system error occurred. Details have been logged securely.",
        },
    )

# Mount all core API routers under /api
app.include_router(hash_routes.router, prefix="/api")
app.include_router(collision_routes.router, prefix="/api")
app.include_router(ev_routes.router, prefix="/api")
app.include_router(legacy_routes.router, prefix="/api")
app.include_router(migration_routes.router, prefix="/api")
app.include_router(attack_routes.router, prefix="/api")
app.include_router(risk_routes.router, prefix="/api")
app.include_router(dashboard_routes.router, prefix="/api")
app.include_router(audit_routes.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """System health check and cryptographic capabilities endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cryptography": {
            "sha3_supported": True,
            "hmac_sha3_supported": True,
            "legacy_md5_simulation": True,
            "replay_protection": "PERSISTENT_SQLITE_ATOMIC",
            "canonicalization": "RFC_8785_JCS_RESTRICTED",
        },
    }
