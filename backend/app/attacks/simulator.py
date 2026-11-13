import copy
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from app.core.config import settings
from app.migration.wrapper import CryptoWrapper
from app.migration.replay import PersistentReplayProtection
from app.crypto.collision_vectors import get_known_collision_vectors
from app.ev_simulator.message_generator import generate_simulated_ev_message


class AttackSimulator:
    """
    Controlled Red-Team Attack Simulation Laboratory.
    Executes live verification pipelines against realistic attack scenarios.
    Explicitly distinguishes:
    - attack_attempted: True
    - attack_detected: True/False
    - defense_successful: True/False
    """

    @classmethod
    def simulate_tampering(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 1: In-Flight OCPP Meter Reading Manipulation.
        Adversary tampers with meterStop in a StopTransaction frame.
        """
        msg = base_message or generate_simulated_ev_message("CS-NORDIC-001", "StopTransaction")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        tampered_wrapped = copy.deepcopy(wrapped)
        if isinstance(tampered_wrapped.get("payload"), dict):
            if "ocpp_message" in tampered_wrapped["payload"] and len(tampered_wrapped["payload"]["ocpp_message"]) > 3:
                tampered_wrapped["payload"]["ocpp_message"][3]["meterStop"] = 142851
                tampered_wrapped["payload"]["ocpp_message"][3]["tampered_by_attacker"] = True
            else:
                tampered_wrapped["payload"]["meter_manipulated"] = 999999

        # Execute actual live verification implementation
        verify_result = CryptoWrapper.verify(tampered_wrapped, enforce_mode="sha3_256")
        detected = (verify_result["crypto_verified"] is False)
        defense_successful = (verify_result["dispatched_to_legacy_parser"] is False) and detected

        return {
            "attack_type": "MESSAGE_TAMPERING",
            "attack_name": "In-Flight Meter Reading Manipulation",
            "attack_attempted": True,
            "attack_detected": detected,
            "detected": detected,
            "defense_successful": defense_successful,
            "description": (
                "An adversary intercepts a StopTransaction OCPP frame and modifies the meterStop "
                "reading to under-report consumed charging energy. The wrapper detects payload bit-flips."
            ),
            "input_message": tampered_wrapped,
            "expected_result": "Wrapper detects digest mismatch over canonical bytes, rejects frame, and drops message.",
            "actual_result": (
                f"Status: {verify_result.get('error')} | Details: {verify_result.get('details')} | "
                f"Dispatched: {verify_result.get('dispatched_to_legacy_parser')}"
            ),
            "detection_method": "SHA3-256 cryptographic digest mismatch over canonical JCS bytes",
            "security_explanation": (
                "The EVHashGuard wrapper binds all payload fields into a deterministic canonical byte stream. "
                "Any single-bit modification drastically flips the digest via the avalanche effect of the "
                "Keccak sponge function, rendering payload tampering immediately detectable."
            ),
            "details": {
                "computed_digest": verify_result.get("computed_digest"),
                "provided_digest": verify_result.get("provided_digest"),
                "crypto_verified": verify_result.get("crypto_verified"),
                "protocol_verified": verify_result.get("protocol_verified"),
            },
        }

    @classmethod
    def simulate_collision_bypass(cls) -> Dict[str, Any]:
        """
        Attack 2: Legacy MD5 Collision Verification Bypass.
        Uses mathematically verified differential collision test vectors.
        """
        vectors = get_known_collision_vectors()
        input1_hex = vectors["input1_hex"]
        input2_hex = vectors["input2_hex"]

        b1 = bytes.fromhex(input1_hex)
        b2 = bytes.fromhex(input2_hex)

        import hashlib
        m1 = hashlib.md5(b1).hexdigest()
        m2 = hashlib.md5(b2).hexdigest()
        s3_1 = hashlib.sha3_256(b1).hexdigest()
        s3_2 = hashlib.sha3_256(b2).hexdigest()

        legacy_bypassed = (m1 == m2) and (b1 != b2)
        sha3_detected = (s3_1 != s3_2)

        return {
            "attack_type": "MD5_COLLISION_BYPASS",
            "attack_name": "Legacy MD5 Collision Verification Bypass",
            "attack_attempted": True,
            "attack_detected": sha3_detected,
            "detected": sha3_detected,
            "defense_successful": sha3_detected,
            "description": (
                "An adversary exploits MD5's broken collision resistance to substitute payload 1 with payload 2 "
                "while preserving the identical 128-bit MD5 digest (008ee33a9d58b51cfeb425b0959121c9)."
            ),
            "input_message": {
                "vector_1_hex": input1_hex,
                "vector_2_hex": input2_hex,
                "vector_length_bytes": vectors["byte_length"],
                "byte_divergences": vectors["differing_byte_indices"],
                "md5_match": m1 == m2,
            },
            "expected_result": (
                "Legacy MD5 cannot distinguish inputs (hash match). Modern SHA3-256 detects bit divergence "
                "and blocks the collision payload."
            ),
            "actual_result": (
                f"MD5 identical ({m1}) [Legacy BYPASSED: {legacy_bypassed}]. "
                f"SHA3-256 diverged: {s3_1[:16]}... != {s3_2[:16]}... [Collision BLOCKED: {sha3_detected}]"
            ),
            "detection_method": "SHA3-256 128-bit collision resistance and Keccak sponge differential immunity",
            "security_explanation": (
                "MD5's collision resistance was completely shattered in 2004-2005. "
                "By migrating to SHA3-256 (Keccak-256), the system achieves full 128-bit collision security "
                "with zero known practical differential paths."
            ),
            "details": {
                "md5_digest": m1,
                "sha3_digest_1": s3_1,
                "sha3_digest_2": s3_2,
            },
        }

    @classmethod
    def simulate_replay(
        cls,
        base_message: Optional[Dict[str, Any]] = None,
        age_seconds: int = 400,
    ) -> Dict[str, Any]:
        """
        Attack 3: Replay Attack (Stale Timestamp & Duplicate Nonce).
        Executes actual PersistentReplayProtection checks.
        """
        msg = base_message or generate_simulated_ev_message("CS-ALPIN-002", "Authorize")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256")

        # Craft stale timestamp outside freshness window
        simulated_old_timestamp = (
            datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
        ).isoformat()

        replay_wrapped = copy.deepcopy(wrapped)
        replay_wrapped["crypto_metadata"]["timestamp"] = simulated_old_timestamp

        # Run actual verification
        verify_result = CryptoWrapper.verify(
            replay_wrapped,
            enforce_mode="hmac_sha3_256",
            check_freshness=True,
        )

        detected = (verify_result["verified"] is False) and (
            verify_result.get("error") in ("REPLAY_FRESHNESS_VIOLATION", "INTEGRITY_VERIFICATION_FAILED")
        )
        defense_successful = (verify_result["dispatched_to_legacy_parser"] is False)

        return {
            "attack_type": "REPLAY_ATTACK",
            "attack_name": "Historic Message Replay & Freshness Violation",
            "attack_attempted": True,
            "attack_detected": detected,
            "detected": detected,
            "defense_successful": defense_successful,
            "description": (
                f"Adversary intercepts a valid historic Authorize message and transmits it {age_seconds} seconds later "
                f"(beyond the {settings.REPLAY_WINDOW_SECONDS}s freshness threshold) to trigger unauthorized charging sessions."
            ),
            "input_message": replay_wrapped,
            "expected_result": f"Message rejected due to expiration beyond {settings.REPLAY_WINDOW_SECONDS}s freshness window.",
            "actual_result": f"Rejected: {verify_result.get('error')} - {verify_result.get('details')}",
            "detection_method": "ISO 8601 timestamp freshness window enforcement and persistent nonce deduplication",
            "security_explanation": (
                "Integrity checks alone do not prevent replay. EVHashGuard binds a cryptographically signed "
                "timestamp and unique message nonce, dropping frames outside the freshness window."
            ),
            "details": {
                "age_seconds": age_seconds,
                "freshness_window_seconds": settings.REPLAY_WINDOW_SECONDS,
                "dispatched": verify_result.get("dispatched_to_legacy_parser"),
            },
        }

    @classmethod
    def simulate_missing_metadata(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 4: Cryptographic Envelope Stripping.
        Adversary strips outer cryptographic metadata to trigger fail-open parser ingest.
        """
        msg = base_message or generate_simulated_ev_message("CS-METRO-003", "BootNotification")
        naked_message = {"payload": msg}  # missing crypto_metadata

        verify_result = CryptoWrapper.verify(naked_message)
        detected = (verify_result["verified"] is False) and (verify_result.get("error") == "MISSING_INTEGRITY_METADATA")
        defense_successful = (verify_result["dispatched_to_legacy_parser"] is False)

        return {
            "attack_type": "STRIPPED_METADATA",
            "attack_name": "Cryptographic Envelope Stripping",
            "attack_attempted": True,
            "attack_detected": detected,
            "detected": detected,
            "defense_successful": defense_successful,
            "description": (
                "Adversary strips the cryptographic metadata envelope entirely, attempting to invoke legacy "
                "fail-open behavior in the CSMS parser."
            ),
            "input_message": naked_message,
            "expected_result": "Wrapper rejects message with MISSING_INTEGRITY_METADATA error.",
            "actual_result": f"Rejected: {verify_result.get('error')} - {verify_result.get('details')}",
            "detection_method": "Mandatory cryptographic wrapper enforcement policy",
            "security_explanation": (
                "EVHashGuard strictly rejects fail-open semantics. Messages lacking required cryptographic "
                "envelopes are dropped prior to legacy parser ingestion."
            ),
            "details": {
                "error": verify_result.get("error"),
                "dispatched": verify_result.get("dispatched_to_legacy_parser"),
            },
        }

    @classmethod
    def simulate_invalid_tag(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 5: Forged HMAC-SHA3-256 Authentication Tag Injection.
        Adversary crafts a fabricated 256-bit authentication tag without secret key.
        """
        msg = base_message or generate_simulated_ev_message("CS-HIGHWAY-004", "Heartbeat")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256")

        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["digest"] = "badc0ffee" * 7 + "0"  # fabricated 64-char hex tag

        verify_result = CryptoWrapper.verify(tampered, enforce_mode="hmac_sha3_256")
        detected = (verify_result["verified"] is False) and (verify_result.get("error") == "INTEGRITY_VERIFICATION_FAILED")
        defense_successful = (verify_result["dispatched_to_legacy_parser"] is False)

        return {
            "attack_type": "FORGED_AUTHENTICATION_TAG",
            "attack_name": "Forged HMAC-SHA3-256 Tag Injection",
            "attack_attempted": True,
            "attack_detected": detected,
            "detected": detected,
            "defense_successful": defense_successful,
            "description": (
                "An unauthenticated attacker sends an arbitrary HMAC tag hoping the server uses weak "
                "or non-constant-time verification."
            ),
            "input_message": tampered,
            "expected_result": "Wrapper rejects message due to constant-time HMAC tag mismatch.",
            "actual_result": f"Rejected: {verify_result.get('error')} - {verify_result.get('details')}",
            "detection_method": "Constant-time HMAC-SHA3-256 tag verification",
            "security_explanation": (
                "HMAC-SHA3-256 requires knowledge of the 256-bit secret key. Without the key, an attacker "
                "has a negligible 2^-256 probability of guessing a valid MAC tag."
            ),
            "details": {
                "provided_tag": tampered["crypto_metadata"]["digest"],
                "computed_tag": verify_result.get("computed_digest"),
                "dispatched": verify_result.get("dispatched_to_legacy_parser"),
            },
        }

    @classmethod
    def simulate_downgrade(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 6: Algorithm Downgrade Attack.
        Tests all weaker algorithm transitions against enforced policies:
        1. Enforced HMAC-SHA3-256 -> incoming unkeyed SHA3-256
        2. Enforced HMAC-SHA3-256 -> incoming broken MD5
        3. Enforced SHA3-256 -> incoming broken MD5
        """
        msg = base_message or generate_simulated_ev_message("CS-PORT-005", "StatusNotification")

        # Transition 1: HMAC-SHA3-256 channel presented with unkeyed SHA3-256
        wrapped_sha3 = CryptoWrapper.wrap(msg, mode="sha3_256")
        res_hmac_to_sha3 = CryptoWrapper.verify(wrapped_sha3, enforce_mode="hmac_sha3_256", allow_downgrade=False)

        # Transition 2: HMAC-SHA3-256 channel presented with legacy MD5
        wrapped_md5 = CryptoWrapper.wrap(msg, mode="legacy_md5")
        res_hmac_to_md5 = CryptoWrapper.verify(wrapped_md5, enforce_mode="hmac_sha3_256", allow_downgrade=False)

        # Transition 3: SHA3-256 channel presented with legacy MD5
        res_sha3_to_md5 = CryptoWrapper.verify(wrapped_md5, enforce_mode="sha3_256", allow_downgrade=False)

        all_blocked = (
            (res_hmac_to_sha3["verified"] is False) and
            (res_hmac_to_md5["verified"] is False) and
            (res_sha3_to_md5["verified"] is False)
        )

        return {
            "attack_type": "ALGORITHM_DOWNGRADE",
            "attack_name": "Cryptographic Protocol Downgrade Attack",
            "attack_attempted": True,
            "attack_detected": all_blocked,
            "detected": all_blocked,
            "defense_successful": all_blocked,
            "description": (
                "Adversary forces a protocol downgrade by masquerading as a legacy client and supplying "
                "MD5 or unkeyed SHA3-256 on an HMAC-SHA3-256 enforced channel."
            ),
            "input_message": wrapped_md5,
            "expected_result": "Wrapper policy blocks all unapproved downgrade transitions (HMAC->SHA3, HMAC->MD5, SHA3->MD5).",
            "actual_result": (
                f"HMAC->SHA3 Blocked: {res_hmac_to_sha3.get('error') == 'DOWNGRADE_ATTACK_PREVENTED'} | "
                f"HMAC->MD5 Blocked: {res_hmac_to_md5.get('error') == 'DOWNGRADE_ATTACK_PREVENTED'} | "
                f"SHA3->MD5 Blocked: {res_sha3_to_md5.get('error') == 'DOWNGRADE_ATTACK_PREVENTED'}"
            ),
            "detection_method": "Multi-tier cryptographic policy enforcement and downgrade lockout",
            "security_explanation": (
                "Silent downgrades are a critical vulnerability class in cryptographic migrations. "
                "EVHashGuard enforces strict hierarchical mode boundaries: systems enforcing Tier 3 "
                "(HMAC-SHA3-256) reject Tier 2 (SHA3-256) and Tier 1 (MD5) unless administrative fallback is explicitly enabled."
            ),
            "details": {
                "hmac_to_sha3_error": res_hmac_to_sha3.get("error"),
                "hmac_to_md5_error": res_hmac_to_md5.get("error"),
                "sha3_to_md5_error": res_sha3_to_md5.get("error"),
            },
        }

    @classmethod
    def simulate_firmware_modification(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 7: Firmware Status Spoofing & Version Modification.
        Adversary falsifies FirmwareStatusNotification to report backdoored firmware as legitimately installed.
        """
        msg = base_message or generate_simulated_ev_message("CS-NORDIC-001", "FirmwareStatusNotification")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        tampered = copy.deepcopy(wrapped)
        if isinstance(tampered.get("payload"), dict):
            if "ocpp_message" in tampered["payload"] and len(tampered["payload"]["ocpp_message"]) > 3:
                tampered["payload"]["ocpp_message"][3]["status"] = "Installed"
                tampered["payload"]["ocpp_message"][3]["firmwareVersion"] = "v9.9.9-backdoored"

        verify_result = CryptoWrapper.verify(tampered, enforce_mode="sha3_256")
        detected = (verify_result["crypto_verified"] is False)
        defense_successful = (verify_result["dispatched_to_legacy_parser"] is False)

        return {
            "attack_type": "FIRMWARE_METADATA_MODIFICATION",
            "attack_name": "Firmware Status Spoofing & Version Tampering",
            "attack_attempted": True,
            "attack_detected": detected,
            "detected": detected,
            "defense_successful": defense_successful,
            "description": (
                "Adversary falsifies FirmwareStatusNotification to report a compromised firmware as "
                "'Installed', misleading the fleet operator regarding charger security posture."
            ),
            "input_message": tampered,
            "expected_result": "Wrapper detects digest mismatch over modified firmware status fields and drops notification.",
            "actual_result": f"Rejected: {verify_result.get('error')} - {verify_result.get('details')}",
            "detection_method": "Canonical payload digest verification over firmware status attributes",
            "security_explanation": (
                "Firmware lifecycle notifications are high-value targets. Cryptographic binding ensures "
                "that status transitions and version strings cannot be spoofed in transit."
            ),
            "details": {
                "error": verify_result.get("error"),
                "dispatched": verify_result.get("dispatched_to_legacy_parser"),
            },
        }
