from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema exists
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
                    details="EVHashGuard Cryptographic Migration Engine initialized with 5 baseline charging stations.",
                )
            )
            await session.commit()
    yield


app = FastAPI(
    title="EVHashGuard API",
    description="Backward-Compatible Cryptographic Integrity Framework for Legacy OCPP 1.6 EV Charging Systems",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for Vite frontend dev server and standard ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": "EVHashGuard CSMS Cryptographic Wrapper",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cryptography": {
            "sha3_supported": True,
            "hmac_sha3_supported": True,
            "legacy_md5_simulation": True,
        },
    }
