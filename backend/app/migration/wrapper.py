import json
import hashlib
import hmac
import uuid
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from app.core.config import settings, get_key
from app.crypto.hmac_engine import compute_hmac_sha3_256, verify_hmac_sha3_256
from app.ev_simulator.ocpp_parser import OCPPParser
from app.migration.replay import PersistentReplayProtection


class CryptoWrapper:
    """
    EVHashGuard Backward-Compatible Cryptographic Migration Wrapper (Specification v2.1.0-sha3).

    Architectural position: Operates transparently between transport ingress
    and legacy OCPP parsers.

    Integrity & Authentication pipeline:
    1. Envelope Validation (Type, structure, mode, and digest formatting)
    2. Downgrade Prevention Policy Enforcement
    3. Timestamp Freshness & Replay Verification
    4. Deterministic Canonicalization (RFC 8785 restricted profile)
    5. Constant-Time Cryptographic Verification
    6. Protocol Structural Validation via OCPPParser
    7. Conditional Dispatch: Only dispatch if BOTH cryptographic & protocol checks pass.
    """

    SUPPORTED_MODES = {"legacy_md5", "sha3_256", "hmac_sha3_256"}
    VALID_ALGORITHMS = {
        "legacy_md5": "MD5",
        "sha3_256": "SHA3-256",
        "hmac_sha3_256": "HMAC-SHA3-256",
    }
    WRAPPER_SPEC_VERSION = "2.1.0-sha3"
    SUPPORTED_SPEC_VERSIONS = {"2.1.0-sha3", "2.0.0-sha3", "2.1.0"}

    @classmethod
    def canonicalize(cls, data: Any) -> bytes:
        """
        Produces deterministic RFC 8785 JSON Canonicalization Scheme (JCS) byte sequence.
        - Alphabetically sorted keys at all dictionary levels
        - No whitespace between tokens (separators: ',' and ':')
        - UTF-8 encoded output without byte-order mark
        - Strict JSON data validation (rejects NaN, Infinity)
        """
        def _validate_jcs_value(val: Any) -> None:
            if isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    raise ValueError("RFC 8785 disallows NaN and Infinity in canonical JSON")
            elif isinstance(val, dict):
                for k, v in val.items():
                    if not isinstance(k, str):
                        raise TypeError(f"RFC 8785 requires string dictionary keys, got {type(k).__name__}")
                    _validate_jcs_value(v)
            elif isinstance(val, list):
                for elem in val:
                    _validate_jcs_value(elem)

        _validate_jcs_value(data)

        canonical_str = json.dumps(
            data,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False,
            allow_nan=False,
        )
        return canonical_str.encode('utf-8')

    @classmethod
    def wrap(
        cls,
        message: Dict[str, Any],
        mode: str = "sha3_256",
        key_id: Optional[str] = None,
        nonce: Optional[str] = None,
        timestamp: Optional[str] = None,
        custom_key: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Envelopes the message payload with authenticated cryptographic metadata without
        modifying the original message payload or OCPP frame structure.
        """
        if mode not in cls.SUPPORTED_MODES:
            raise ValueError(f"Unsupported migration mode: '{mode}'. Must be one of {cls.SUPPORTED_MODES}")

        now_utc = timestamp or datetime.now(timezone.utc).isoformat()
        msg_nonce = nonce or str(uuid.uuid4())
        algo_name = cls.VALID_ALGORITHMS[mode]

        if mode == "legacy_md5":
            # Legacy MD5 historically only authenticated the payload
            auth_bytes = cls.canonicalize(message)
            digest = hashlib.md5(auth_bytes).hexdigest()
            is_keyed = False
            kid = None
        elif mode == "sha3_256":
            # Authenticates all security-critical envelope fields to prevent metadata substitution
            auth_context = {
                "algorithm": algo_name,
                "mode": mode,
                "nonce": msg_nonce,
                "payload": message,
                "timestamp": now_utc,
                "wrapper_version": cls.WRAPPER_SPEC_VERSION,
            }
            auth_bytes = cls.canonicalize(auth_context)
            digest = hashlib.sha3_256(auth_bytes).hexdigest()
            is_keyed = False
            kid = None
        elif mode == "hmac_sha3_256":
            kid = key_id or settings.DEFAULT_KEY_ID
            key = custom_key if custom_key is not None else get_key(kid)
            if key is None:
                raise ValueError(f"Unknown key identifier: '{kid}'")

            auth_context = {
                "algorithm": algo_name,
                "key_id": kid,
                "mode": mode,
                "nonce": msg_nonce,
                "payload": message,
                "timestamp": now_utc,
                "wrapper_version": cls.WRAPPER_SPEC_VERSION,
            }
            auth_bytes = cls.canonicalize(auth_context)
            digest = compute_hmac_sha3_256(auth_bytes, key)
            is_keyed = True
        else:
            raise ValueError(f"Invalid mode: {mode}")

        crypto_envelope = {
            "wrapper_version": cls.WRAPPER_SPEC_VERSION,
            "mode": mode,
            "algorithm": algo_name,
            "digest": digest,
            "digest_bits": len(digest) * 4,
            "is_keyed_mac": is_keyed,
            "key_id": kid,
            "nonce": msg_nonce,
            "canonical_bytes_len": len(auth_bytes),
            "timestamp": now_utc,
            "downgrade_protection": True,
        }

        return {
            "payload": message,
            "crypto_metadata": crypto_envelope,
            "wrapper_status": "ENVELOPED",
        }

    @classmethod
    def verify(
        cls,
        wrapped_message: Dict[str, Any],
        enforce_mode: Optional[str] = None,
        allow_downgrade: Optional[bool] = None,
        custom_key: Optional[bytes] = None,
        check_freshness: bool = True,
    ) -> Dict[str, Any]:
        """
        Synchronous / In-Memory Verification Routine.
        Strictly verifies:
        1. Envelope format and types
        2. Exact algorithm and mode matching
        3. Downgrade prevention
        4. Hexadecimal encoding & digest length
        5. Timestamp freshness (window check)
        6. Constant-time digest verification over authenticated envelope fields
        7. OCPP protocol validation
        Only dispatches to legacy parser if both cryptographic and protocol checks pass.
        """
        # 1. Structural Validation
        if not isinstance(wrapped_message, dict):
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "MALFORMED_WRAPPER",
                "details": "Wrapped message must be a JSON object",
                "dispatched_to_legacy_parser": False,
            }

        payload = wrapped_message.get("payload")
        crypto_meta = wrapped_message.get("crypto_metadata")

        if payload is None:
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "MISSING_PAYLOAD",
                "details": "Wrapper envelope has no payload field",
                "dispatched_to_legacy_parser": False,
            }

        if crypto_meta is None or not isinstance(crypto_meta, dict):
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "MISSING_INTEGRITY_METADATA",
                "details": "Integrity metadata envelope is missing or invalid. Unverified message rejected.",
                "dispatched_to_legacy_parser": False,
            }

        mode = crypto_meta.get("mode")
        algo = crypto_meta.get("algorithm")
        digest = crypto_meta.get("digest")
        version = crypto_meta.get("wrapper_version")
        timestamp_str = crypto_meta.get("timestamp")
        nonce = crypto_meta.get("nonce")
        key_id = crypto_meta.get("key_id")

        # 2. Type and Metadata Attribute Validation
        if not mode or not isinstance(mode, str) or mode not in cls.SUPPORTED_MODES:
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "UNRECOGNIZED_MODE",
                "details": f"Unknown or invalid crypto mode: '{mode}'. Must be one of {cls.SUPPORTED_MODES}",
                "dispatched_to_legacy_parser": False,
            }

        if not algo or not isinstance(algo, str):
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "MISSING_ALGORITHM",
                "details": "Metadata missing algorithm identifier",
                "dispatched_to_legacy_parser": False,
            }

        expected_algo = cls.VALID_ALGORITHMS[mode]
        if algo != expected_algo:
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "ALGORITHM_MODE_MISMATCH",
                "details": f"Algorithm '{algo}' does not match mode '{mode}' (expected '{expected_algo}')",
                "dispatched_to_legacy_parser": False,
            }

        # 3. Digest Validation (Safe Hex & Length Check)
        if not digest or not isinstance(digest, str):
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "MISSING_DIGEST",
                "details": "Digest must be a valid hexadecimal string",
                "dispatched_to_legacy_parser": False,
            }

        expected_lengths = {"legacy_md5": 32, "sha3_256": 64, "hmac_sha3_256": 64}
        expected_len = expected_lengths[mode]
        clean_digest = digest.strip().lower()

        if len(clean_digest) != expected_len:
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "MALFORMED_DIGEST",
                "details": f"Invalid digest length for {algo}: got {len(clean_digest)} hex chars, expected {expected_len}",
                "dispatched_to_legacy_parser": False,
            }

        try:
            bytes.fromhex(clean_digest)
        except ValueError:
            return {
                "verified": False,
                "crypto_verified": False,
                "protocol_verified": False,
                "error": "MALFORMED_DIGEST",
                "details": "Digest contains non-hexadecimal characters",
                "dispatched_to_legacy_parser": False,
            }

        # 4. Strict Downgrade Prevention
        effective_downgrade_policy = (
            allow_downgrade if allow_downgrade is not None else settings.DOWNGRADE_ALLOWED
        )

        # Hierarchy: hmac_sha3_256 (Tier 3) > sha3_256 (Tier 2) > legacy_md5 (Tier 1)
        tier_levels = {"legacy_md5": 1, "sha3_256": 2, "hmac_sha3_256": 3}

        if enforce_mode and enforce_mode in tier_levels:
            required_tier = tier_levels[enforce_mode]
            incoming_tier = tier_levels[mode]

            if incoming_tier < required_tier and not effective_downgrade_policy:
                return {
                    "verified": False,
                    "crypto_verified": False,
                    "protocol_verified": False,
                    "error": "DOWNGRADE_ATTACK_PREVENTED",
                    "details": (
                        f"System policy strictly forbids algorithm downgrade from required '{enforce_mode}' "
                        f"(Tier {required_tier}) to weaker '{mode}' (Tier {incoming_tier})."
                    ),
                    "dispatched_to_legacy_parser": False,
                    "algorithm": algo,
                    "mode": mode,
                }

        # 5. Timestamp Freshness Check
        if check_freshness and timestamp_str:
            fresh, _, fresh_reason = PersistentReplayProtection.validate_timestamp_freshness(timestamp_str)
            if not fresh:
                return {
                    "verified": False,
                    "crypto_verified": False,
                    "protocol_verified": False,
                    "error": "REPLAY_FRESHNESS_VIOLATION",
                    "details": fresh_reason,
                    "dispatched_to_legacy_parser": False,
                }

        # 6. Cryptographic Verification
        if mode == "legacy_md5":
            auth_bytes = cls.canonicalize(payload)
            computed = hashlib.md5(auth_bytes).hexdigest()
            # Constant-time comparison
            crypto_valid = hmac.compare_digest(computed.lower(), clean_digest)
            warning = "LEGACY NOTICE: MD5 provides zero collision resistance and no origin authentication."

        elif mode == "sha3_256":
            # Reconstruct authenticated context binding envelope fields
            auth_context = {
                "algorithm": algo,
                "mode": mode,
                "nonce": nonce,
                "payload": payload,
                "timestamp": timestamp_str,
                "wrapper_version": version or cls.WRAPPER_SPEC_VERSION,
            }
            auth_bytes = cls.canonicalize(auth_context)
            computed = hashlib.sha3_256(auth_bytes).hexdigest()
            crypto_valid = hmac.compare_digest(computed.lower(), clean_digest)
            warning = "SHA3-256 provides unkeyed integrity only; it does NOT provide sender origin authentication."

        elif mode == "hmac_sha3_256":
            if not key_id and custom_key is None:
                return {
                    "verified": False,
                    "crypto_verified": False,
                    "protocol_verified": False,
                    "error": "MISSING_KEY_IDENTIFIER",
                    "details": "HMAC-SHA3-256 mode requires a valid key_id",
                    "dispatched_to_legacy_parser": False,
                }

            key = custom_key if custom_key is not None else get_key(key_id)
            if key is None:
                return {
                    "verified": False,
                    "crypto_verified": False,
                    "protocol_verified": False,
                    "error": "UNKNOWN_KEY_ID",
                    "details": f"Cryptographic key identifier '{key_id}' is not recognized in active key store",
                    "dispatched_to_legacy_parser": False,
                }

            auth_context = {
                "algorithm": algo,
                "key_id": key_id,
                "mode": mode,
                "nonce": nonce,
                "payload": payload,
                "timestamp": timestamp_str,
                "wrapper_version": version or cls.WRAPPER_SPEC_VERSION,
            }
            auth_bytes = cls.canonicalize(auth_context)
            crypto_valid = verify_hmac_sha3_256(auth_bytes, key, clean_digest)
            computed = compute_hmac_sha3_256(auth_bytes, key)
            warning = "HMAC-SHA3-256 verified: Confirms both tamper-evident integrity and authenticated sender origin."

        # 7. Protocol Structural Parser Validation
        parser_valid = True
        parser_info = "Payload did not contain an OCPP frame array"
        if isinstance(payload, list) or (isinstance(payload, dict) and "ocpp_message" in payload):
            frame = payload if isinstance(payload, list) else payload["ocpp_message"]
            parser_valid, parsed_data, parser_info = OCPPParser.validate_and_parse(frame)

        # 8. Conditional Dispatch Determination
        dispatched = crypto_valid and parser_valid
        overall_verified = dispatched

        error_reason = None
        if not crypto_valid:
            error_reason = "INTEGRITY_VERIFICATION_FAILED"
            details = "Cryptographic tag mismatch: envelope or payload tampered/forged"
        elif not parser_valid:
            error_reason = "PROTOCOL_VALIDATION_FAILED"
            details = f"Cryptographic check passed, but protocol validation failed: {parser_info}"
        else:
            details = "Cryptographic envelope verified and OCPP frame validated successfully"

        return {
            "verified": overall_verified,
            "crypto_verified": crypto_valid,
            "protocol_verified": parser_valid,
            "mode": mode,
            "algorithm": algo,
            "computed_digest": computed,
            "provided_digest": digest,
            "payload_canonical_len": len(auth_bytes),
            "dispatched_to_legacy_parser": dispatched,
            "legacy_parser_validation": {
                "passed": parser_valid,
                "info": parser_info,
            },
            "security_warning": warning,
            "error": error_reason,
            "details": details,
        }

    @classmethod
    async def verify_async(
        cls,
        wrapped_message: Dict[str, Any],
        enforce_mode: Optional[str] = None,
        allow_downgrade: Optional[bool] = None,
        custom_key: Optional[bytes] = None,
        db_session: Optional[Any] = None,
        station_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full Asynchronous Verification Routine incorporating SQLite Persistent Replay Protection.
        """
        # Execute in-memory cryptographic verification
        res = cls.verify(
            wrapped_message,
            enforce_mode=enforce_mode,
            allow_downgrade=allow_downgrade,
            custom_key=custom_key,
            check_freshness=True,
        )

        if not res["verified"]:
            return res

        # If DB session provided, enforce persistent replay nonce check in SQLite
        if db_session is not None:
            crypto_meta = wrapped_message.get("crypto_metadata", {})
            nonce = crypto_meta.get("nonce")
            timestamp = crypto_meta.get("timestamp")

            if nonce and timestamp:
                consumed, replay_reason = await PersistentReplayProtection.check_and_consume_nonce(
                    session=db_session,
                    nonce=nonce,
                    timestamp_str=timestamp,
                    station_id=station_id,
                )
                if not consumed:
                    return {
                        "verified": False,
                        "crypto_verified": True,
                        "protocol_verified": res["protocol_verified"],
                        "mode": res["mode"],
                        "algorithm": res["algorithm"],
                        "computed_digest": res["computed_digest"],
                        "provided_digest": res["provided_digest"],
                        "dispatched_to_legacy_parser": False,
                        "legacy_parser_validation": res["legacy_parser_validation"],
                        "security_warning": res["security_warning"],
                        "error": "REPLAY_ATTACK_DETECTED",
                        "details": replay_reason,
                    }

        return res
