import pytest
import hashlib
from app.crypto.hash_engine import compute_hash, compare_hashes
from app.crypto.hmac_engine import generate_key, compute_hmac_sha3_256, verify_hmac_sha3_256


class TestCryptographicHashLaboratory:
    """Tests NIST / RFC known test vectors across all supported algorithms."""

    def test_md5_known_vectors(self):
        # RFC 1321 MD5 test vectors
        res_empty = compute_hash("", "md5")
        assert res_empty["digest"] == "d41d8cd98f00b204e9800998ecf8427e"
        assert res_empty["digest_length"] == 128
        assert res_empty["security_status"] == "BROKEN"

        res_abc = compute_hash("abc", "md5")
        assert res_abc["digest"] == "900150983cd24fb0d6963f7d28e17f72"

    def test_sha1_known_vectors(self):
        # RFC 3174 SHA-1 test vectors
        res_empty = compute_hash("", "sha1")
        assert res_empty["digest"] == "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        assert res_empty["digest_length"] == 160
        assert res_empty["security_status"] == "WEAK"

        res_abc = compute_hash("abc", "sha1")
        assert res_abc["digest"] == "a9993e364706816aba3e25717850c26c9cd0d89d"

    def test_sha256_known_vectors(self):
        # NIST FIPS 180-4 SHA-256 test vectors
        res_empty = compute_hash("", "sha256")
        assert res_empty["digest"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert res_empty["digest_length"] == 256
        assert res_empty["security_status"] == "SECURE"

        res_abc = compute_hash("abc", "sha256")
        assert res_abc["digest"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

    def test_sha3_256_known_vectors(self):
        # NIST FIPS 202 SHA3-256 test vectors
        res_empty = compute_hash("", "sha3_256")
        assert res_empty["digest"] == "a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a"
        assert res_empty["digest_length"] == 256
        assert res_empty["security_status"] == "RECOMMENDED"

        res_abc = compute_hash("abc", "sha3_256")
        assert res_abc["digest"] == "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"

    def test_compare_hashes_multiple_algorithms(self):
        res = compare_hashes("EV_CHARGING_TELEMETRY_SAMPLE", ["md5", "sha1", "sha256", "sha3_256"])
        assert len(res) == 4
        algos = [r["algorithm"] for r in res]
        assert "md5" in algos
        assert "sha3_256" in algos
        for r in res:
            assert r["execution_time_ms"] >= 0.0

    def test_hmac_sha3_256_integrity_and_authentication(self):
        key = generate_key(32)
        message = b"OCPP_1.6_METER_VALUES_PAYLOAD_CANONICAL"

        tag = compute_hmac_sha3_256(message, key)
        assert len(tag) == 64  # 256 bits = 64 hex characters

        # Verification succeeds with correct key and message
        assert verify_hmac_sha3_256(message, key, tag) is True

        # Verification fails if message is modified by even 1 byte
        tampered_msg = b"OCPP_1.6_METER_VALUES_PAYLOAD_CANONICAk"
        assert verify_hmac_sha3_256(tampered_msg, key, tag) is False

        # Verification fails if wrong key is used
        wrong_key = generate_key(32)
        assert verify_hmac_sha3_256(message, wrong_key, tag) is False
