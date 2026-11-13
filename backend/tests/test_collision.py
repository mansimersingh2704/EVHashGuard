import pytest
import hashlib
from app.crypto.collision_vectors import get_known_collision_vectors, verify_custom_collision


class TestMD5CollisionLaboratory:
    """Rigorous mathematical tests of verified MD5 collision vectors."""

    def test_verified_known_collision_pair(self):
        vectors = get_known_collision_vectors()

        b1 = bytes.fromhex(vectors["input1_hex"])
        b2 = bytes.fromhex(vectors["input2_hex"])

        # 1. Inputs must differ
        assert b1 != b2
        assert vectors["inputs_differ"] is True
        assert len(b1) == len(b2) == 64

        # 2. Both inputs must produce the EXACT same MD5 digest
        m1 = hashlib.md5(b1).hexdigest()
        m2 = hashlib.md5(b2).hexdigest()
        assert m1 == m2 == "008ee33a9d58b51cfeb425b0959121c9"
        assert vectors["md5_collision"] is True

        # 3. Modern algorithms (SHA-256 and SHA3-256) must distinguish them completely
        s256_1 = hashlib.sha256(b1).hexdigest()
        s256_2 = hashlib.sha256(b2).hexdigest()
        assert s256_1 != s256_2

        s3_1 = hashlib.sha3_256(b1).hexdigest()
        s3_2 = hashlib.sha3_256(b2).hexdigest()
        assert s3_1 != s3_2

    def test_invalid_collision_pair_detection(self):
        # Arbitrary different strings do NOT form a collision
        input1 = b"EV_FIRMWARE_PAYLOAD_GENUINE_001"
        input2 = b"EV_FIRMWARE_PAYLOAD_GENUINE_002"

        res = verify_custom_collision(input1, input2)
        assert res["inputs_differ"] is True
        assert res["collision_detected"] is False
        assert res["md5_1"] != res["md5_2"]

    def test_identical_inputs_do_not_count_as_collision(self):
        input1 = b"IDENTICAL_INPUT_DATA"
        input2 = b"IDENTICAL_INPUT_DATA"

        res = verify_custom_collision(input1, input2)
        assert res["inputs_differ"] is False
        assert res["collision_detected"] is False
