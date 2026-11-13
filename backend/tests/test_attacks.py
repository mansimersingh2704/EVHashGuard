import pytest
from app.attacks.simulator import AttackSimulator


class TestAttackSimulationLab:
    """Verifies all 7 attack simulation scenarios and defense detection logic."""

    def test_tampering_simulation(self):
        res = AttackSimulator.simulate_tampering()
        assert res["attack_type"] == "MESSAGE_TAMPERING"
        assert res["detected"] is True
        assert "meterStop" in res["description"] or "meter" in res["description"]

    def test_collision_bypass_simulation(self):
        res = AttackSimulator.simulate_collision_bypass()
        assert res["attack_type"] == "MD5_COLLISION_BYPASS"
        assert res["detected"] is True
        assert res["input_message"]["vector_1_hex"] != res["input_message"]["vector_2_hex"]

    def test_replay_attack_simulation(self):
        res = AttackSimulator.simulate_replay(age_seconds=500)
        assert res["attack_type"] == "REPLAY_ATTACK"
        assert res["detected"] is True
        assert "freshness" in res["detection_method"].lower()

    def test_missing_metadata_simulation(self):
        res = AttackSimulator.simulate_missing_metadata()
        assert res["attack_type"] == "STRIPPED_METADATA"
        assert res["detected"] is True

    def test_invalid_tag_simulation(self):
        res = AttackSimulator.simulate_invalid_tag()
        assert res["attack_type"] == "FORGED_AUTHENTICATION_TAG"
        assert res["detected"] is True

    def test_downgrade_simulation(self):
        res = AttackSimulator.simulate_downgrade()
        assert res["attack_type"] == "ALGORITHM_DOWNGRADE"
        assert res["detected"] is True

    def test_firmware_modification_simulation(self):
        res = AttackSimulator.simulate_firmware_modification()
        assert res["attack_type"] == "FIRMWARE_METADATA_MODIFICATION"
        assert res["detected"] is True

    def test_unkeyed_digest_recomputation_simulation(self):
        res = AttackSimulator.simulate_unkeyed_digest_recomputation()
        assert res["attack_type"] == "UNKEYED_DIGEST_RECOMPUTATION"
        # Crucial cryptographic property: Unkeyed SHA3-256 FAILS to detect recomputation (detected is False)
        assert res["detected"] is False
        assert res["defense_successful"] is False
        # But HMAC-SHA3-256 blocks it
        assert res["details"]["unkeyed_sha3_verified"] is True
        assert res["details"]["hmac_sha3_verified"] is False
