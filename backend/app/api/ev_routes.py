import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.database.db import get_db, FirmwareMessage, SecurityAuditLog
from app.ev_simulator.message_generator import (
    CHARGING_STATIONS,
    generate_simulated_ev_message,
)
from app.models.schemas import EVMessageRequest

router = APIRouter(tags=["EV Firmware & OCPP Simulator"])


@router.get("/simulator/stations")
async def get_charging_stations():
    """Returns list of simulated charging stations."""
    return CHARGING_STATIONS


@router.post("/ev/messages")
async def api_generate_ev_message(
    request: EVMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a realistic OCPP 1.6 message with simulated legacy MD5 integrity extension.
    """
    station = next((s for s in CHARGING_STATIONS if s["station_id"] == request.station_id), None)
    if not station:
        raise HTTPException(
            status_code=404,
            detail=f"Charging station '{request.station_id}' not found in simulator topology",
        )

    sim_result = generate_simulated_ev_message(request.station_id, request.message_type)

    # Persist message to database
    fm = FirmwareMessage(
        message_id=sim_result["message_id"],
        station_id=request.station_id,
        message_type=request.message_type,
        payload_json=json.dumps(sim_result["ocpp_message"]),
        legacy_integrity=sim_result["legacy_integrity_metadata"]["digest"],
    )
    db.add(fm)

    audit = SecurityAuditLog(
        event_type="EV_MESSAGE_GENERATION",
        station_id=request.station_id,
        algorithm="MD5 (Legacy Extension)",
        status="GENERATED",
        details=f"Generated OCPP {request.message_type} with legacy MD5={sim_result['legacy_integrity_metadata']['digest'][:12]}...",
    )
    db.add(audit)
    await db.commit()

    return sim_result
