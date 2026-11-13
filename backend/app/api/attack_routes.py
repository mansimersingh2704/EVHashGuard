from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from app.database.db import get_db, AttackSimulation, SecurityAuditLog
from app.attacks.simulator import AttackSimulator

router = APIRouter(tags=["Attack Simulation Lab"])


async def record_attack_audit(attack_res: Dict[str, Any], db: AsyncSession):
    sim = AttackSimulation(
        attack_type=attack_res["attack_type"],
        detected=attack_res["detected"],
        input_summary=str(attack_res.get("attack_name")),
        result_summary=attack_res["actual_result"][:255],
    )
    db.add(sim)

    audit = SecurityAuditLog(
        event_type="ATTACK_SIMULATION",
        station_id=None,
        algorithm="SHA3-256 / HMAC-SHA3-256",
        status="DETECTED" if attack_res["detected"] else "UNDETECTED",
        details=f"Attack: {attack_res['attack_name']} | Result: {attack_res['actual_result'][:100]}",
    )
    db.add(audit)
    await db.commit()


@router.post("/attacks/tampering")
async def api_attack_tampering(
    message: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    res = AttackSimulator.simulate_tampering(message)
    await record_attack_audit(res, db)
    return res


@router.post("/attacks/replay")
async def api_attack_replay(
    message: Optional[Dict[str, Any]] = None,
    delay_seconds: int = 400,
    db: AsyncSession = Depends(get_db),
):
    res = AttackSimulator.simulate_replay(message, age_seconds=delay_seconds)
    await record_attack_audit(res, db)
    return res


@router.post("/attacks/downgrade")
async def api_attack_downgrade(
    message: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    res = AttackSimulator.simulate_downgrade(message)
    await record_attack_audit(res, db)
    return res


@router.post("/attacks/collision")
async def api_attack_collision(db: AsyncSession = Depends(get_db)):
    res = AttackSimulator.simulate_collision_bypass()
    await record_attack_audit(res, db)
    return res


@router.post("/attacks/missing-metadata")
async def api_attack_missing_metadata(
    message: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    res = AttackSimulator.simulate_missing_metadata(message)
    await record_attack_audit(res, db)
    return res


@router.post("/attacks/invalid-tag")
async def api_attack_invalid_tag(
    message: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    res = AttackSimulator.simulate_invalid_tag(message)
    await record_attack_audit(res, db)
    return res


@router.post("/attacks/firmware-mod")
async def api_attack_firmware_mod(
    message: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    res = AttackSimulator.simulate_firmware_modification(message)
    await record_attack_audit(res, db)
    return res
