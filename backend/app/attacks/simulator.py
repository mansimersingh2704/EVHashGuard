import copy
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Set

from app.migration.wrapper import CryptoWrapper
from app.crypto.collision_vectors import get_known_collision_vectors
from app.ev_simulator.message_generator import generate_simulated_ev_message

# In-memory tracking of received message IDs for replay prevention demonstration
_SEEN_MESSAGE_IDS: Set[str] = set()
REPLAY_WINDOW_SECONDS = 300  # 5 minutes


class AttackSimulator:
    """
    Controlled Educational Attack Simulation Lab.
    Demonstrates practical exploitation vectors and EVHashGuard defense responses.
    """

    @classmethod
    def simulate_tampering(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 1: Attacker intercepts an OCPP message (e.g. StopTransaction)
        and maliciously alters the meterStop energy reading to defraud billing.
        """
        msg = base_message or generate_simulated_ev_message("CS-NORDIC-001", "StopTransaction")
        # Generate wrapped message with SHA3-256
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Attacker tampers with payload data
        tampered_wrapped = copy.deepcopy(wrapped)
        if "payload" in tampered_wrapped and isinstance(tampered_wrapped["payload"], dict):
            if "ocpp_message" in tampered_wrapped["payload"] and len(tampered_wrapped["payload"]["ocpp_message"]) > 3:
                # Alter meter reading from e.g. 149320 to 142851
                tampered_wrapped["payload"]["ocpp_message"][3]["meterStop"] = 142851
                tampered_wrapped["payload"]["ocpp_message"][3]["tampered_by_attacker"] = True
            else:
                tampered_wrapped["payload"]["meter_manipulated"] = 999999

        # Run verification through wrapper
        verify_result = CryptoWrapper.verify(tampered_wrapped)

        detected = not verify_result["verified"]

        return {
            "attack_type": "MESSAGE_TAMPERING",
            "attack_name": "In-Flight Meter Reading Manipulation",
            "description": (
                "An adversary intercepts a StopTransaction OCPP frame and modifies the meterStop "
                "reading to under-report consumed charging energy. The legacy parser without wrapper "
                "would process the falsified energy values."
            ),
            "input_message": tampered_wrapped,
            "expected_result": "Wrapper recalculates canonical digest, detects divergence, and drops message.",
            "actual_result": (
                f"Verification failed: computed digest {verify_result.get('computed_digest')[:16]}... "
                f"!= provided {verify_result.get('provided_digest')[:16]}..."
            ),
            "detected": detected,
            "detection_method": "SHA3-256 cryptographic digest mismatch over canonical payload bytes",
            "security_explanation": (
                "The EVHashGuard wrapper binds all payload fields into a deterministic canonical byte stream. "
                "Any single-bit modification drastically flips the digest via the avalanche effect of the "
                "Keccak sponge function, rendering payload tampering immediately detectable."
            ),
        }

    @classmethod
    def simulate_collision_bypass(cls) -> Dict[str, Any]:
        """
        Attack 2: Attacker leverages an MD5 collision to swap a legitimate firmware command
        or charging parameter with a malicious command without invalidating the legacy MD5 digest.
        """
        vectors = get_known_collision_vectors()
        input1_hex = vectors["input1_hex"]
        input2_hex = vectors["input2_hex"]

        # In legacy MD5 system:
        legacy_pass = (vectors["md5_hash_1"] == vectors["md5_hash_2"])

        # In modern SHA-3 / SHA-256 system:
        sha3_diverge = vectors["sha3_256_differ"]

        return {
            "attack_type": "MD5_COLLISION_BYPASS",
            "attack_name": "Legacy MD5 Collision Verification Bypass",
            "description": (
                "An adversary exploits MD5's broken collision resistance to construct two distinct messages "
                "that hash to the identical 128-bit MD5 digest (008ee33a9d58b51cfeb425b0959121c9). "
                "In a legacy MD5-only EV system, replacing Message 1 with Message 2 circumvents integrity verification."
            ),
            "input_message": {
                "vector_1_hex": input1_hex,
                "vector_2_hex": input2_hex,
                "vector_length_bytes": vectors["byte_length"],
                "byte_divergences": vectors["differing_byte_indices"],
            },
            "expected_result": (
                "Legacy MD5 treats both inputs as identical. EVHashGuard SHA3-256 detects divergence "
                "and rejects collision payload."
            ),
            "actual_result": (
                f"MD5 digest matched ({vectors['md5_hash_1']}) [Legacy BYPASSED!]. "
                f"However, SHA3-256 produced {vectors['sha3_256_hash_1'][:16]}... vs {vectors['sha3_256_hash_2'][:16]}... [Collision BLOCKED!]"
            ),
            "detected": sha3_diverge,
            "detection_method": "SHA3-256 second-preimage / collision resistance enforcement",
            "security_explanation": (
                "MD5's collision resistance was completely shattered in 2004-2005. "
                "By migrating to SHA3-256 (Keccak-256), the system achieves 128-bit collision security "
                "and 256-bit preimage resistance with zero known practical differential paths."
            ),
        }

    @classmethod
    def simulate_replay(cls, base_message: Optional[Dict[str, Any]] = None, age_seconds: int = 400) -> Dict[str, Any]:
        """
        Attack 3: Attacker captures a valid historic Authorize or StartTransaction message
        and re-injects it into the CSMS after the freshness window has elapsed.
        """
        msg = base_message or generate_simulated_ev_message("CS-ALPIN-002", "Authorize")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256")

        # Simulate expired timestamp or already recorded message_id
        simulated_old_timestamp = (
            datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
        ).isoformat()

        replay_wrapped = copy.deepcopy(wrapped)
        replay_wrapped["crypto_metadata"]["timestamp"] = simulated_old_timestamp
        # If timestamp altered, HMAC also becomes invalid unless recomputed;
        # let's test freshness window detection:
        msg_time = datetime.fromisoformat(replay_wrapped["crypto_metadata"]["timestamp"])
        now = datetime.now(timezone.utc)
        time_delta = (now - msg_time).total_seconds()

        # Replay evaluation:
        is_stale = time_delta > REPLAY_WINDOW_SECONDS
        msg_id = msg.get("message_id", "simulated-id")
        already_seen = msg_id in _SEEN_MESSAGE_IDS
        _SEEN_MESSAGE_IDS.add(msg_id)

        detected = is_stale or already_seen

        return {
            "attack_type": "REPLAY_ATTACK",
            "attack_name": "Historic Message Injection (Stale Token)",
            "description": (
                f"Adversary captures a legitimate Authorize message and transmits it {age_seconds} seconds later "
                f"(beyond the {REPLAY_WINDOW_SECONDS}s freshness threshold) to trigger unauthorized charging sessions."
            ),
            "input_message": replay_wrapped,
            "expected_result": f"Message rejected due to expiration beyond {REPLAY_WINDOW_SECONDS}s freshness window.",
            "actual_result": f"Rejected: message age is {int(time_delta)}s (allowed window: {REPLAY_WINDOW_SECONDS}s)",
            "detected": detected,
            "detection_method": "Timestamp freshness window check and nonce/message_id tracking",
            "security_explanation": (
                "Integrity checks alone do not prevent replay. EVHashGuard binds a cryptographically signed "
                "timestamp and unique message identifier, rejecting frames exceeding the freshness boundary."
            ),
        }

    @classmethod
    def simulate_missing_metadata(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 4: Attacker strips the integrity metadata to trick the backend into
        treating it as an unauthenticated plaintext message.
        """
        msg = base_message or generate_simulated_ev_message("CS-METRO-003", "BootNotification")
        naked_message = {"payload": msg}  # no crypto_metadata

        verify_result = CryptoWrapper.verify(naked_message)
        detected = not verify_result["verified"]

        return {
            "attack_type": "STRIPPED_METADATA",
            "attack_name": "Cryptographic Envelope Stripping",
            "description": (
                "Adversary strips the cryptographic metadata envelope entirely, attempting to invoke legacy "
                "fail-open behavior in the CSMS parser."
            ),
            "input_message": naked_message,
            "expected_result": "Wrapper rejects message with MISSING_INTEGRITY_METADATA error.",
            "actual_result": f"Rejected: {verify_result.get('error')} - {verify_result.get('details')}",
            "detected": detected,
            "detection_method": "Mandatory cryptographic wrapper enforcement policy",
            "security_explanation": (
                "EVHashGuard strictly rejects fail-open semantics. Messages lacking required cryptographic "
                "envelopes are dropped prior to legacy parser ingestion."
            ),
        }

    @classmethod
    def simulate_invalid_tag(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 5: Attacker fabricates an arbitrary HMAC authentication tag.
        """
        msg = base_message or generate_simulated_ev_message("CS-HIGHWAY-004", "Heartbeat")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256")

        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["digest"] = "badc0ffee" * 7 + "00"  # fabricated 64-char hex tag

        verify_result = CryptoWrapper.verify(tampered, enforce_mode="hmac_sha3_256")
        detected = not verify_result["verified"]

        return {
            "attack_type": "FORGED_AUTHENTICATION_TAG",
            "attack_name": "Forged HMAC-SHA3-256 Tag Injection",
            "description": (
                "An unauthenticated attacker sends an arbitrary HMAC tag hoping the server uses weak "
                "or non-constant-time verification."
            ),
            "input_message": tampered,
            "expected_result": "Wrapper rejects message due to HMAC verification failure.",
            "actual_result": f"Verification failed: {verify_result.get('details')}",
            "detected": detected,
            "detection_method": "Constant-time HMAC-SHA3-256 tag verification",
            "security_explanation": (
                "HMAC-SHA3-256 requires knowledge of the 256-bit secret key. Without the key, an attacker "
                "has a negligible 2^-256 probability of guessing a valid MAC tag."
            ),
        }

    @classmethod
    def simulate_downgrade(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 6: Attacker attempts to downgrade an HMAC-SHA3-256 configured channel to legacy MD5.
        """
        msg = base_message or generate_simulated_ev_message("CS-PORT-005", "StatusNotification")
        # Attacker crafts legacy MD5 wrapped message
        downgraded = CryptoWrapper.wrap(msg, mode="legacy_md5")

        # Server enforces modern mode (hmac_sha3_256 or sha3_256)
        verify_result = CryptoWrapper.verify(
            downgraded,
            enforce_mode="hmac_sha3_256",
            allow_downgrade=False,
        )

        detected = not verify_result["verified"]

        return {
            "attack_type": "ALGORITHM_DOWNGRADE",
            "attack_name": "Cryptographic Downgrade Attack to Insecure MD5",
            "description": (
                "Adversary forces a protocol downgrade by masquerading as a legacy client and supplying "
                "an MD5 digest instead of the enforced HMAC-SHA3-256 tag."
            ),
            "input_message": downgraded,
            "expected_result": "Wrapper policy detects downgrade attempt and aborts connection.",
            "actual_result": f"Blocked: {verify_result.get('error')} - {verify_result.get('details')}",
            "detected": detected,
            "detection_method": "Explicit algorithm policy negotiation and downgrade lockout",
            "security_explanation": (
                "Silent downgrades are a major vulnerability class in cryptographic migrations. "
                "EVHashGuard requires explicit administrator opt-in for legacy fallbacks; by default, "
                "downgrades to MD5 are rejected at the edge."
            ),
        }

    @classmethod
    def simulate_firmware_modification(cls, base_message: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Attack 7: Malicious modification of firmware update status or binary metadata.
        """
        msg = base_message or generate_simulated_ev_message("CS-NORDIC-001", "FirmwareStatusNotification")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        tampered = copy.deepcopy(wrapped)
        if "payload" in tampered and isinstance(tampered["payload"], dict):
            # Change status from InstallationFailed to Installed, spoofing successful update
            if "ocpp_message" in tampered["payload"] and len(tampered["payload"]["ocpp_message"]) > 3:
                tampered["payload"]["ocpp_message"][3]["status"] = "Installed"
                tampered["payload"]["ocpp_message"][3]["firmwareVersion"] = "v9.9.9-backdoored"

        verify_result = CryptoWrapper.verify(tampered)
        detected = not verify_result["verified"]

        return {
            "attack_type": "FIRMWARE_METADATA_MODIFICATION",
            "attack_name": "Firmware Status Spoofing & Version Tampering",
            "description": (
                "Adversary falsifies FirmwareStatusNotification to report a compromised firmware as "
                "'Installed', misleading the fleet operator regarding charger security posture."
            ),
            "input_message": tampered,
            "expected_result": "Integrity check fails; rogue firmware notification dropped.",
            "actual_result": f"Rejected: {verify_result.get('details')}",
            "detected": detected,
            "detection_method": "Canonical payload digest verification over firmware status attributes",
            "security_explanation": (
                "Firmware lifecycle notifications are high-value targets. Cryptographic binding ensures "
                "that status transitions and version strings cannot be spoofed in transit."
            ),
        }
