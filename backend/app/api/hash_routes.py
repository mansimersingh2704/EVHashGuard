from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database.db import get_db, SecurityAuditLog
from app.crypto.hash_engine import compare_hashes
from app.models.schemas import HashRequest

router = APIRouter(tags=["Cryptographic Hash Lab"])


@router.post("/hash/compare")
async def api_compare_hashes(request: HashRequest, db: AsyncSession = Depends(get_db)):
    results = compare_hashes(request.message, request.algorithms)

    # Log operation to SecurityAuditLog
    audit_entry = SecurityAuditLog(
        event_type="HASH_COMPUTATION",
        station_id=None,
        algorithm=",".join(request.algorithms),
        status="SUCCESS",
        details=f"Computed comparison across {len(request.algorithms)} algorithms for {len(request.message)} char input.",
    )
    db.add(audit_entry)
    await db.commit()

    return {
        "message": request.message,
        "results": results,
    }
