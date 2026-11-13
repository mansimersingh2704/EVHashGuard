from fastapi import APIRouter
from typing import Dict, Any

from app.risk_engine.analyzer import get_risk_analysis_report

router = APIRouter(tags=["Cryptographic Risk Analysis Engine"])


@router.get("/risk/analysis")
async def api_risk_analysis():
    """
    Returns qualitative risk matrix and comparative evaluation for MD5, SHA-1, SHA-256,
    SHA3-256, and HMAC-SHA3-256.
    """
    return get_risk_analysis_report()
