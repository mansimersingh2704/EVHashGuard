from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any, List

from app.database.db import (
    get_db,
    FirmwareMessage,
    IntegrityCheck,
    MigrationEvent,
    AttackSimulation,
    SecurityAuditLog,
    ChargingStation,
)
from app.ev_simulator.message_generator import CHARGING_STATIONS

router = APIRouter(tags=["Security Audit Dashboard"])


@router.get("/dashboard/stats")
async def api_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Computes real aggregate statistics dynamically from SQLite database tables.
    """
    # Total messages
    msg_count_q = await db.execute(select(func.count()).select_from(FirmwareMessage))
    total_messages = msg_count_q.scalar() or 0

    # Successful vs Failed verifications
    pass_q = await db.execute(
        select(func.count()).select_from(IntegrityCheck).where(IntegrityCheck.verification_status == "PASS")
    )
    successful_verifications = pass_q.scalar() or 0

    fail_q = await db.execute(
        select(func.count()).select_from(IntegrityCheck).where(IntegrityCheck.verification_status == "FAIL")
    )
    failed_verifications = fail_q.scalar() or 0

    # Tampering & Attack detections
    attack_total_q = await db.execute(select(func.count()).select_from(AttackSimulation))
    total_attacks_simulated = attack_total_q.scalar() or 0

    detected_attacks_q = await db.execute(
        select(func.count()).select_from(AttackSimulation).where(AttackSimulation.detected == True)
    )
    detected_attacks = detected_attacks_q.scalar() or 0

    # Migrations count
    migration_count_q = await db.execute(select(func.count()).select_from(MigrationEvent))
    total_migrations = migration_count_q.scalar() or 0

    # Audit events count
    audit_count_q = await db.execute(select(func.count()).select_from(SecurityAuditLog))
    total_audit_events = audit_count_q.scalar() or 0

    # Algorithm usage breakdown
    algo_query = await db.execute(
        select(SecurityAuditLog.algorithm, func.count(SecurityAuditLog.id))
        .group_by(SecurityAuditLog.algorithm)
    )
    algo_rows = algo_query.all()
    algorithm_usage = {}
    for algo, count in algo_rows:
        if algo:
            algorithm_usage[algo] = count

    # Recent timeline events (last 10)
    timeline_q = await db.execute(
        select(SecurityAuditLog)
        .order_by(SecurityAuditLog.created_at.desc())
        .limit(10)
    )
    recent_events = [
        {
            "id": log.id,
            "event_type": log.event_type,
            "station_id": log.station_id,
            "algorithm": log.algorithm,
            "status": log.status,
            "details": log.details,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in timeline_q.scalars().all()
    ]

    return {
        "total_messages_processed": total_messages,
        "successful_verifications": successful_verifications,
        "failed_verifications": failed_verifications,
        "tampering_and_attacks_detected": detected_attacks,
        "total_attacks_simulated": total_attacks_simulated,
        "total_migrations": total_migrations,
        "total_audit_events": total_audit_events,
        "active_charging_stations": len(CHARGING_STATIONS),
        "algorithm_usage": algorithm_usage,
        "security_posture": "ACTIVE_WRAPPER_ENFORCED",
        "recent_security_events": recent_events,
    }
