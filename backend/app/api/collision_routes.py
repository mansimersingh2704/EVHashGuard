from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database.db import get_db, SecurityAuditLog
from app.crypto.collision_vectors import get_known_collision_vectors, verify_custom_collision
from app.models.schemas import CollisionRequest

router = APIRouter(tags=["MD5 Collision Lab"])


@router.post("/collision/verify")
async def api_verify_collision(
    request: CollisionRequest = None,
    db: AsyncSession = Depends(get_db),
):
    req = request or CollisionRequest()

    if not req.input1_hex or not req.input2_hex:
        # Return verified public test vector
        result = get_known_collision_vectors()
        res_data = {
            "input1_hex": result["input1_hex"],
            "input2_hex": result["input2_hex"],
            "inputs_differ": result["inputs_differ"],
            "collision_detected": result["md5_collision"],
            "md5_1": result["md5_hash_1"],
            "md5_2": result["md5_hash_2"],
            "sha256_1": result["sha256_hash_1"],
            "sha256_2": result["sha256_hash_2"],
            "sha3_256_1": result["sha3_256_hash_1"],
            "sha3_256_2": result["sha3_256_hash_2"],
            "explanation": result["description"],
            "source": result["source"],
        }
    else:
        try:
            b1 = bytes.fromhex(req.input1_hex.strip())
            b2 = bytes.fromhex(req.input2_hex.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid hexadecimal string provided")

        analysis = verify_custom_collision(b1, b2)
        res_data = {
            "input1_hex": req.input1_hex,
            "input2_hex": req.input2_hex,
            "inputs_differ": analysis["inputs_differ"],
            "collision_detected": analysis["collision_detected"],
            "md5_1": analysis["md5_1"],
            "md5_2": analysis["md5_2"],
            "sha256_1": analysis["sha256_1"],
            "sha256_2": analysis["sha256_2"],
            "sha3_256_1": analysis["sha3_256_1"],
            "sha3_256_2": analysis["sha3_256_2"],
            "explanation": analysis["explanation"],
            "source": "Custom Input Evaluation",
        }

    # Record in audit log
    audit = SecurityAuditLog(
        event_type="COLLISION_VERIFICATION",
        station_id=None,
        algorithm="MD5 vs SHA3-256",
        status="COLLISION_DETECTED" if res_data["collision_detected"] else "NO_COLLISION",
        details=f"MD5 1={res_data['md5_1']}, MD5 2={res_data['md5_2']}, match={res_data['collision_detected']}",
    )
    db.add(audit)
    await db.commit()

    return res_data
