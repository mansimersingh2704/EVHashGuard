import hashlib
import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database.db import get_db, IntegrityCheck, SecurityAuditLog
from app.models.schemas import LegacyVerifyRequest

router = APIRouter(tags=["Legacy MD5 Integrity"])


@router.post("/legacy/verify")
async def api_legacy_verify(
    request: LegacyVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Canonicalize if JSON object/string
        data = json.loads(request.payload_json)
        canonical_bytes = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    except Exception:
        canonical_bytes = request.payload_json.encode('utf-8')

    computed = hashlib.md5(canonical_bytes).hexdigest()
    verified = (computed.lower() == request.legacy_md5.strip().lower())

    status_str = "PASS" if verified else "FAIL"
    warning = (
        "CRITICAL SECURITY NOTICE: Ordinary MD5 verification does NOT guarantee message authenticity. "
        "MD5 is completely broken for collision resistance. An adversary can forge disparate messages "
        "that compute to this exact digest. Migrate to SHA3-256 or HMAC-SHA3-256 immediately."
    )

    # Persist integrity check
    ic = IntegrityCheck(
        message_id="legacy-direct-check",
        algorithm="MD5",
        digest=request.legacy_md5,
        verification_status=status_str,
    )
    db.add(ic)

    audit = SecurityAuditLog(
        event_type="LEGACY_MD5_VERIFICATION",
        station_id=None,
        algorithm="MD5",
        status=status_str,
        details=f"MD5 verified={verified}, computed={computed}, provided={request.legacy_md5}",
    )
    db.add(audit)
    await db.commit()

    return {
        "verified": verified,
        "algorithm": "MD5",
        "computed_digest": computed,
        "provided_digest": request.legacy_md5,
        "security_warning": warning,
        "recommendation": "Envelop this payload with EVHashGuard SHA-3 Migration Wrapper.",
    }
