import pytest
import copy
from app.migration.wrapper import CryptoWrapper
from app.ev_simulator.message_generator import generate_simulated_ev_message
from app.ev_simulator.ocpp_parser import OCPPParser


class TestMigrationWrapper:
    """Tests the backward-compatible cryptographic migration wrapper."""

    def test_legacy_md5_wrap_and_verify(self):
        msg = generate_simulated_ev_message("CS-NORDIC-001", "Heartbeat")
        wrapped = CryptoWrapper.wrap(msg, mode="legacy_md5")

        assert wrapped["wrapper_status"] == "ENVELOPED"
        assert wrapped["crypto_metadata"]["mode"] == "legacy_md5"
        assert wrapped["crypto_metadata"]["algorithm"] == "MD5"
        # Original message payload remains intact
        assert wrapped["payload"] == msg

        # Verification succeeds
        res = CryptoWrapper.verify(wrapped, enforce_mode="legacy_md5")
        assert res["verified"] is True
        assert res["dispatched_to_legacy_parser"] is True

    def test_sha3_256_wrap_and_verify(self):
        msg = generate_simulated_ev_message("CS-ALPIN-002", "StatusNotification")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        assert wrapped["crypto_metadata"]["mode"] == "sha3_256"
        assert wrapped["crypto_metadata"]["algorithm"] == "SHA3-256"
        assert wrapped["crypto_metadata"]["digest_bits"] == 256

        res = CryptoWrapper.verify(wrapped, enforce_mode="sha3_256")
        assert res["verified"] is True
        assert res["dispatched_to_legacy_parser"] is True
        assert res["legacy_parser_validation"]["passed"] is True

    def test_hmac_sha3_256_wrap_and_verify(self):
        msg = generate_simulated_ev_message("CS-METRO-003", "StartTransaction")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256", key_id="key-test-unit")

        assert wrapped["crypto_metadata"]["mode"] == "hmac_sha3_256"
        assert wrapped["crypto_metadata"]["algorithm"] == "HMAC-SHA3-256"
        assert wrapped["crypto_metadata"]["is_keyed_mac"] is True
        assert wrapped["crypto_metadata"]["key_id"] == "key-test-unit"

        res = CryptoWrapper.verify(wrapped, enforce_mode="hmac_sha3_256")
        assert res["verified"] is True
        assert res["dispatched_to_legacy_parser"] is True

    def test_tampered_payload_rejection(self):
        msg = generate_simulated_ev_message("CS-HIGHWAY-004", "StopTransaction")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Adversary mutates transaction data
        tampered = copy.deepcopy(wrapped)
        tampered["payload"]["ocpp_message"][3]["meterStop"] = 999999

        res = CryptoWrapper.verify(tampered, enforce_mode="sha3_256")
        assert res["verified"] is False
        assert res["dispatched_to_legacy_parser"] is False
        assert res["error"] == "INTEGRITY_VERIFICATION_FAILED"

    def test_missing_metadata_rejection(self):
        msg = generate_simulated_ev_message("CS-PORT-005", "BootNotification")
        naked = {"payload": msg}  # No crypto_metadata envelope

        res = CryptoWrapper.verify(naked)
        assert res["verified"] is False
        assert res["error"] == "MISSING_INTEGRITY_METADATA"

    def test_downgrade_prevention(self):
        msg = generate_simulated_ev_message("CS-NORDIC-001", "Authorize")
        # Attacker wraps with legacy MD5
        downgraded = CryptoWrapper.wrap(msg, mode="legacy_md5")

        # System enforces SHA3-256 with default downgrade_allowed=False
        res = CryptoWrapper.verify(
            downgraded,
            enforce_mode="sha3_256",
            allow_downgrade=False,
        )
        assert res["verified"] is False
        assert res["error"] == "DOWNGRADE_ATTACK_PREVENTED"
        assert res["dispatched_to_legacy_parser"] is False

    def test_legacy_parser_ocpp_compatibility(self):
        # Verify that wrapped message can be unpacked and ingested by standard OCPP parser
        msg = generate_simulated_ev_message("CS-NORDIC-001", "BootNotification")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # CSMS unrolls wrapper
        payload = wrapped["payload"]
        ocpp_frame = payload["ocpp_message"]

        # Legacy parser validates OCPP frame structure
        valid, parsed, desc = OCPPParser.validate_and_parse(ocpp_frame)
        assert valid is True
        assert parsed["action"] == "BootNotification"
        assert parsed["message_type_name"] == "CALL"
        assert parsed["payload"]["chargePointVendor"] == "NordicVolt Systems"
