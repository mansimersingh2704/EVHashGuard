from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database.db import get_db, MigrationEvent, IntegrityCheck, SecurityAuditLog
from app.migration.wrapper import CryptoWrapper
from app.models.schemas import (
    MigrationWrapRequest,
    MigrationWrapResponse,
    MigrationVerifyRequest,
    MigrationVerifyResponse,
)

router = APIRouter(tags=["SHA-3 Migration Wrapper"])


@router.post("/migration/wrap", response_model=MigrationWrapResponse)
async def api_migration_wrap(
    request: MigrationWrapRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        wrapped = CryptoWrapper.wrap(request.payload, mode=request.mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    meta = wrapped["crypto_metadata"]

    # Record migration event
    event = MigrationEvent(
        message_id=str(request.payload.get("message_id", "msg-wrapped")),
        from_algorithm="MD5 (Legacy)",
        to_algorithm=meta["algorithm"],
        mode=request.mode,
        success=True,
    )
    db.add(event)

    audit = SecurityAuditLog(
        event_type="MESSAGE_WRAPPED",
        station_id=request.payload.get("station_id"),
        algorithm=meta["algorithm"],
        status="ENVELOPED",
        details=f"Enveloped message with {meta['algorithm']} (mode={request.mode}, bytes={meta['canonical_bytes_len']})",
    )
    db.add(audit)
    await db.commit()

    return {
        "wrapped_message": wrapped,
        "mode": request.mode,
        "algorithm": meta["algorithm"],
        "key_id": meta.get("key_id"),
    }


@router.post("/migration/verify", response_model=MigrationVerifyResponse)
async def api_migration_verify(
    request: MigrationVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = CryptoWrapper.verify(
        request.wrapped_message,
        enforce_mode=request.mode,
    )

    status_str = "PASS" if result.get("verified") else "FAIL"

    # Log integrity check
    ic = IntegrityCheck(
        message_id="migrated-check",
        algorithm=result.get("algorithm", "UNKNOWN"),
        digest=result.get("provided_digest", "none"),
        verification_status=status_str,
    )
    db.add(ic)

    audit = SecurityAuditLog(
        event_type="MIGRATION_VERIFICATION",
        station_id=None,
        algorithm=result.get("algorithm", "UNKNOWN"),
        status=status_str,
        details=f"Mode={request.mode}, Result={status_str}: {result.get('details')}",
    )
    db.add(audit)
    await db.commit()

    return {
        "verified": result["verified"],
        "algorithm": result.get("algorithm", "UNKNOWN"),
        "mode": result.get("mode", request.mode),
        "details": result.get("details", "") + (" | " + result.get("error") if result.get("error") else ""),
    }
