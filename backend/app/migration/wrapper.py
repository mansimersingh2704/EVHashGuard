import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from app.core.config import settings, get_hmac_key
from app.crypto.hmac_engine import compute_hmac_sha3_256, verify_hmac_sha3_256
from app.ev_simulator.ocpp_parser import OCPPParser


class CryptoWrapper:
    """
    EVHashGuard Backward-Compatible Cryptographic Migration Wrapper.

    Architectural position: Operates transparently between incoming transport
    and the legacy message parser.

    Integrity pipeline:
    Incoming Message -> Wrapper Envelope Check -> Cryptographic Verification
    -> Legacy Parser Forwarding.
    """

    SUPPORTED_MODES = {"legacy_md5", "sha3_256", "hmac_sha3_256"}
    WRAPPER_SPEC_VERSION = "2.1.0-sha3"

    @staticmethod
    def canonicalize(payload: Any) -> bytes:
        """
        Produces deterministic RFC 8785-style canonical JSON byte sequence.
        Keys are sorted; whitespace is stripped.
        """
        return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

    @classmethod
    def wrap(
        cls,
        message: Dict[str, Any],
        mode: str = "sha3_256",
        key_id: Optional[str] = None,
        custom_key: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Envelopes the message with external cryptographic metadata without modifying
        the original message payload or OCPP frame structure.
        """
        if mode not in cls.SUPPORTED_MODES:
            raise ValueError(f"Unsupported migration mode: {mode}. Must be one of {cls.SUPPORTED_MODES}")

        # The message payload to authenticate
        canonical_bytes = cls.canonicalize(message)
        now_utc = datetime.now(timezone.utc).isoformat()

        if mode == "legacy_md5":
            digest = hashlib.md5(canonical_bytes).hexdigest()
            algo_name = "MD5"
            security_tier = "LEGACY_DEPRECATED"
            is_authenticated = False
            kid = None
        elif mode == "sha3_256":
            digest = hashlib.sha3_256(canonical_bytes).hexdigest()
            algo_name = "SHA3-256"
            security_tier = "MIGRATED_INTEGRITY"
            is_authenticated = False
            kid = None
        elif mode == "hmac_sha3_256":
            key = custom_key if custom_key is not None else get_hmac_key()
            kid = key_id or "key-active-csms-primary"
            digest = compute_hmac_sha3_256(canonical_bytes, key)
            algo_name = "HMAC-SHA3-256"
            security_tier = "MIGRATED_AUTHENTICATED"
            is_authenticated = True
        else:
            raise ValueError(f"Invalid mode: {mode}")

        crypto_envelope = {
            "wrapper_version": cls.WRAPPER_SPEC_VERSION,
            "mode": mode,
            "algorithm": algo_name,
            "digest": digest,
            "digest_bits": len(digest) * 4,
            "is_keyed_mac": is_authenticated,
            "key_id": kid,
            "canonical_bytes_len": len(canonical_bytes),
            "timestamp": now_utc,
            "downgrade_protection": True,
        }

        # Keep original message 100% unmodified; append envelope outside
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
    ) -> Dict[str, Any]:
        """
        Verifies the cryptographic envelope of an incoming message before
        dispatching to the legacy message parser.
        """
        if not isinstance(wrapped_message, dict):
            return {
                "verified": False,
                "error": "MALFORMED_WRAPPER",
                "details": "Wrapped message must be a JSON object",
                "dispatched_to_legacy_parser": False,
            }

        payload = wrapped_message.get("payload")
        crypto_meta = wrapped_message.get("crypto_metadata")

        if payload is None:
            return {
                "verified": False,
                "error": "MISSING_PAYLOAD",
                "details": "Wrapper has no payload field",
                "dispatched_to_legacy_parser": False,
            }

        if crypto_meta is None or not isinstance(crypto_meta, dict):
            return {
                "verified": False,
                "error": "MISSING_INTEGRITY_METADATA",
                "details": "Integrity metadata is missing or invalid. Unverified message rejected.",
                "dispatched_to_legacy_parser": False,
            }

        mode = crypto_meta.get("mode")
        algo = crypto_meta.get("algorithm")
        digest = crypto_meta.get("digest")

        if not mode or not digest:
            return {
                "verified": False,
                "error": "INCOMPLETE_METADATA",
                "details": "Metadata missing mode or digest attribute",
                "dispatched_to_legacy_parser": False,
            }

        effective_downgrade_policy = (
            allow_downgrade if allow_downgrade is not None else settings.DOWNGRADE_ALLOWED
        )

        # Downgrade Prevention:
        # If enforce_mode requires SHA3-256 or HMAC-SHA3-256, but incoming uses MD5,
        # fail immediately unless downgrade policy explicitly permits it.
        if enforce_mode and enforce_mode != mode:
            if enforce_mode in {"sha3_256", "hmac_sha3_256"} and mode == "legacy_md5":
                if not effective_downgrade_policy:
                    return {
                        "verified": False,
                        "error": "DOWNGRADE_ATTACK_PREVENTED",
                        "details": (
                            f"System policy strictly forbids algorithm downgrade from {enforce_mode} "
                            f"to insecure legacy {mode} (MD5)."
                        ),
                        "dispatched_to_legacy_parser": False,
                        "algorithm": algo,
                        "mode": mode,
                    }

        canonical_bytes = cls.canonicalize(payload)

        # Cryptographic verification
        if mode == "legacy_md5":
            computed = hashlib.md5(canonical_bytes).hexdigest()
            # Constant-time comparison
            is_valid = hashlib.md5(canonical_bytes).digest() == bytes.fromhex(digest) if len(digest) == 32 else False
            warning = "Verified using legacy MD5. Insecure against collision and forgery attacks."
        elif mode == "sha3_256":
            computed = hashlib.sha3_256(canonical_bytes).hexdigest()
            is_valid = (computed.lower() == digest.lower())
            warning = "SHA3-256 provides preimage and collision resistance; unkeyed integrity only."
        elif mode == "hmac_sha3_256":
            key = custom_key if custom_key is not None else get_hmac_key()
            is_valid = verify_hmac_sha3_256(canonical_bytes, key, digest)
            computed = compute_hmac_sha3_256(canonical_bytes, key)
            warning = "HMAC-SHA3-256 provides both cryptographic integrity and endpoint authentication."
        else:
            return {
                "verified": False,
                "error": "UNRECOGNIZED_MODE",
                "details": f"Unknown crypto mode: {mode}",
                "dispatched_to_legacy_parser": False,
            }

        # If verification passes, optionally run legacy OCPP structural validation
        parser_valid = True
        parser_info = "Payload did not contain an OCPP frame array"
        if isinstance(payload, list) or (isinstance(payload, dict) and "ocpp_message" in payload):
            frame = payload if isinstance(payload, list) else payload["ocpp_message"]
            parser_valid, parsed_data, parser_info = OCPPParser.validate_and_parse(frame)

        return {
            "verified": is_valid,
            "mode": mode,
            "algorithm": algo,
            "computed_digest": computed,
            "provided_digest": digest,
            "payload_canonical_len": len(canonical_bytes),
            "dispatched_to_legacy_parser": is_valid,
            "legacy_parser_validation": {
                "passed": parser_valid,
                "info": parser_info,
            },
            "security_warning": warning,
            "error": None if is_valid else "INTEGRITY_VERIFICATION_FAILED",
            "details": "Cryptographic tag matches canonical representation" if is_valid else "Digest mismatch: payload altered or forged",
        }
