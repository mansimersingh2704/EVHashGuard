from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ─── Hash ────────────────────────────────────────────────────────────────────

class HashRequest(BaseModel):
    message: str = Field(..., description="Text to hash")
    algorithms: List[str] = Field(
        default=["md5", "sha256", "sha3_256"],
        description="Algorithms to run: md5, sha1, sha256, sha3_256"
    )


class HashResult(BaseModel):
    algorithm: str
    digest: str
    digest_length: int  # bits
    execution_time_ms: float
    security_status: str
    security_description: str


class HashCompareResponse(BaseModel):
    message: str
    results: List[HashResult]


# ─── Collision ────────────────────────────────────────────────────────────────

class CollisionRequest(BaseModel):
    input1_hex: Optional[str] = Field(None, description="First input in hex (optional; uses built-in vectors if omitted)")
    input2_hex: Optional[str] = Field(None, description="Second input in hex (optional)")


class CollisionResult(BaseModel):
    input1_hex: str
    input2_hex: str
    md5_1: str
    md5_2: str
    collision_detected: bool
    sha256_1: str
    sha256_2: str
    sha3_256_1: str
    sha3_256_2: str
    explanation: str
    inputs_differ: bool


# ─── EV / OCPP ───────────────────────────────────────────────────────────────

class EVMessageRequest(BaseModel):
    station_id: str = Field(..., description="Station ID (e.g. EV-ALPHA-001)")
    message_type: str = Field(
        default="Heartbeat",
        description="OCPP action type"
    )


class EVMessageResponse(BaseModel):
    ocpp_message: List[Any]
    legacy_integrity_metadata: Dict[str, Any]
    note: str


# ─── Legacy Verify ────────────────────────────────────────────────────────────

class LegacyVerifyRequest(BaseModel):
    payload_json: str = Field(..., description="JSON payload string")
    legacy_md5: str = Field(..., description="Legacy MD5 hex digest to verify")


class LegacyVerifyResponse(BaseModel):
    verified: bool
    algorithm: str
    computed_digest: str
    provided_digest: str
    security_warning: str
    recommendation: str


# ─── Migration Wrap ───────────────────────────────────────────────────────────

class MigrationWrapRequest(BaseModel):
    payload: Dict[str, Any] = Field(..., description="Payload to wrap")
    mode: str = Field(
        default="sha3_256",
        description="Mode: legacy_md5 | sha3_256 | hmac_sha3_256"
    )


class MigrationWrapResponse(BaseModel):
    wrapped_message: Dict[str, Any]
    mode: str
    algorithm: str
    key_id: Optional[str] = None


# ─── Migration Verify ─────────────────────────────────────────────────────────

class MigrationVerifyRequest(BaseModel):
    wrapped_message: Dict[str, Any]
    mode: str


class MigrationVerifyResponse(BaseModel):
    verified: bool
    algorithm: str
    mode: str
    details: str


# ─── Attack ───────────────────────────────────────────────────────────────────

class AttackRequest(BaseModel):
    attack_type: str = Field(
        ...,
        description=(
            "One of: collision_demonstration, length_extension, "
            "birthday_paradox, replay_attack, downgrade_attack, "
            "tampering_detection, preimage_resistance_comparison"
        )
    )
    parameters: Optional[Dict[str, Any]] = Field(default=None)


class AttackResult(BaseModel):
    attack_type: str
    detected: bool
    input_summary: Optional[str]
    result_summary: str
    details: Dict[str, Any]
    recommendation: str


# ─── Risk ─────────────────────────────────────────────────────────────────────

class AlgorithmRisk(BaseModel):
    algorithm: str
    security_level: str
    collision_resistance: str
    preimage_resistance: str
    second_preimage_resistance: str
    nist_status: str
    known_attacks: List[str]
    recommendation: str
    suitable_for_ev_firmware: bool


class RiskAnalysis(BaseModel):
    algorithms: List[AlgorithmRisk]
    overall_recommendation: str
    migration_urgency: str


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_hash_operations: int
    total_collision_checks: int
    total_migrations: int
    total_attack_simulations: int
    total_audit_events: int
    algorithm_usage: Dict[str, int]
    security_posture: str


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    id: int
    event_type: str
    station_id: Optional[str]
    algorithm: Optional[str]
    status: str
    details: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}
