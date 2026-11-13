from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, List

from app.database.db import get_db, SecurityAuditLog

router = APIRouter(tags=["Security Audit Logs"])


@router.get("/audit/logs")
async def api_get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated audit logs from SQLite database.
    """
    total_q = await db.execute(select(func.count()).select_from(SecurityAuditLog))
    total_count = total_q.scalar() or 0

    query = (
        select(SecurityAuditLog)
        .order_by(SecurityAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(query)
    logs = res.scalars().all()

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "station_id": log.station_id,
                "algorithm": log.algorithm,
                "status": log.status,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
