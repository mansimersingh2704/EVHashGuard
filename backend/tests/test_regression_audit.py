import pytest
import copy
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.migration.wrapper import CryptoWrapper
from app.migration.replay import PersistentReplayProtection
from app.ev_simulator.ocpp_parser import OCPPParser
from app.ev_simulator.message_generator import generate_simulated_ev_message
from app.core.config import settings, get_key
from app.database.db import Base, ConsumedNonce


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def test_db_session():
    """Provides an isolated in-memory SQLite database session for persistent replay tests."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await test_engine.dispose()


class TestCriticalSecurityRegressionAudit:
    """
    Automated Regression Test Suite verifying all 20 critical security audit items.
    """

    # ─── 1. MD5 Digest Verification ───────────────────────────────────────────
    def test_01_md5_digest_verification(self):
        msg = generate_simulated_ev_message("CS-NORDIC-001", "Heartbeat")
        wrapped = CryptoWrapper.wrap(msg, mode="legacy_md5")
        res = CryptoWrapper.verify(wrapped, enforce_mode="legacy_md5")

        assert res["verified"] is True
        assert res["crypto_verified"] is True
        assert res["algorithm"] == "MD5"
        assert res["dispatched_to_legacy_parser"] is True

    # ─── 2. SHA3-256 Verification ─────────────────────────────────────────────
    def test_02_sha3_256_verification(self):
        msg = generate_simulated_ev_message("CS-ALPIN-002", "StatusNotification")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")
        res = CryptoWrapper.verify(wrapped, enforce_mode="sha3_256")

        assert res["verified"] is True
        assert res["crypto_verified"] is True
        assert res["algorithm"] == "SHA3-256"
        assert res["dispatched_to_legacy_parser"] is True
        assert "unkeyed integrity only" in res["security_warning"]

    # ─── 3. HMAC-SHA3-256 Verification ────────────────────────────────────────
    def test_03_hmac_sha3_256_verification(self):
        msg = generate_simulated_ev_message("CS-METRO-003", "StartTransaction")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256")
        res = CryptoWrapper.verify(wrapped, enforce_mode="hmac_sha3_256")

        assert res["verified"] is True
        assert res["crypto_verified"] is True
        assert res["algorithm"] == "HMAC-SHA3-256"
        assert res["dispatched_to_legacy_parser"] is True
        assert "authenticated sender origin" in res["security_warning"]

    # ─── 4. Malformed Digest ──────────────────────────────────────────────────
    def test_04_malformed_digest(self):
        msg = generate_simulated_ev_message("CS-HIGHWAY-004", "Heartbeat")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Case A: Non-hexadecimal characters
        tampered_hex = copy.deepcopy(wrapped)
        tampered_hex["crypto_metadata"]["digest"] = "z" * 64
        res_a = CryptoWrapper.verify(tampered_hex)
        assert res_a["verified"] is False
        assert res_a["error"] == "MALFORMED_DIGEST"
        assert "non-hexadecimal" in res_a["details"]

        # Case B: Invalid length (63 characters instead of 64)
        tampered_len = copy.deepcopy(wrapped)
        tampered_len["crypto_metadata"]["digest"] = "a" * 63
        res_b = CryptoWrapper.verify(tampered_len)
        assert res_b["verified"] is False
        assert res_b["error"] == "MALFORMED_DIGEST"
        assert "length" in res_b["details"]

    # ─── 5. Metadata Modification ─────────────────────────────────────────────
    def test_05_metadata_modification(self):
        msg = generate_simulated_ev_message("CS-PORT-005", "StatusNotification")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Tampering with wrapper_version invalidates the authenticated envelope digest
        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["wrapper_version"] = "1.0.0-insecure"
        res = CryptoWrapper.verify(tampered)

        assert res["verified"] is False
        assert res["crypto_verified"] is False
        assert res["error"] == "INTEGRITY_VERIFICATION_FAILED"

    # ─── 6. Algorithm Field Substitution ──────────────────────────────────────
    def test_06_algorithm_field_substitution(self):
        msg = generate_simulated_ev_message("CS-NORDIC-001", "BootNotification")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Substitute algorithm field to "MD5" while mode is "sha3_256"
        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["algorithm"] = "MD5"
        res = CryptoWrapper.verify(tampered)

        assert res["verified"] is False
        assert res["error"] == "ALGORITHM_MODE_MISMATCH"

    # ─── 7. Key ID Substitution ───────────────────────────────────────────────
    def test_07_key_id_substitution(self):
        msg = generate_simulated_ev_message("CS-ALPIN-002", "Authorize")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256", key_id="key-active-csms-primary")

        # Adversary substitutes key_id to a different valid key
        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["key_id"] = "key-backup-csms-2026"
        res = CryptoWrapper.verify(tampered, enforce_mode="hmac_sha3_256")

        # Recomputed tag with backup key does not match tag computed with primary key
        assert res["verified"] is False
        assert res["error"] == "INTEGRITY_VERIFICATION_FAILED"

    # ─── 8. Timestamp Modification ────────────────────────────────────────────
    def test_08_timestamp_modification(self):
        msg = generate_simulated_ev_message("CS-METRO-003", "Heartbeat")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Adversary modifies timestamp
        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["timestamp"] = "2026-01-01T00:00:00+00:00"
        res = CryptoWrapper.verify(tampered, check_freshness=False)

        assert res["verified"] is False
        assert res["error"] == "INTEGRITY_VERIFICATION_FAILED"

    # ─── 9. Nonce Modification ────────────────────────────────────────────────
    def test_09_nonce_modification(self):
        msg = generate_simulated_ev_message("CS-HIGHWAY-004", "MeterValues")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256")

        # Adversary substitutes nonce
        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["nonce"] = "forged-nonce-value-99"
        res = CryptoWrapper.verify(tampered, enforce_mode="hmac_sha3_256")

        assert res["verified"] is False
        assert res["error"] == "INTEGRITY_VERIFICATION_FAILED"

    # ─── 10. SHA3-to-MD5 Downgrade ────────────────────────────────────────────
    def test_10_sha3_to_md5_downgrade(self):
        msg = generate_simulated_ev_message("CS-PORT-005", "StopTransaction")
        # Attacker crafts MD5 wrapped frame
        wrapped_md5 = CryptoWrapper.wrap(msg, mode="legacy_md5")

        # Server enforces SHA3-256
        res = CryptoWrapper.verify(wrapped_md5, enforce_mode="sha3_256", allow_downgrade=False)

        assert res["verified"] is False
        assert res["error"] == "DOWNGRADE_ATTACK_PREVENTED"
        assert res["dispatched_to_legacy_parser"] is False

    # ─── 11. HMAC-to-SHA3 Downgrade ───────────────────────────────────────────
    def test_11_hmac_to_sha3_downgrade(self):
        msg = generate_simulated_ev_message("CS-NORDIC-001", "Authorize")
        # Attacker presents unkeyed SHA3-256
        wrapped_sha3 = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Server enforces authenticated HMAC-SHA3-256
        res = CryptoWrapper.verify(wrapped_sha3, enforce_mode="hmac_sha3_256", allow_downgrade=False)

        assert res["verified"] is False
        assert res["error"] == "DOWNGRADE_ATTACK_PREVENTED"
        assert res["dispatched_to_legacy_parser"] is False

    # ─── 12. Replay of Identical Message ──────────────────────────────────────
    @pytest.mark.anyio
    async def test_12_replay_of_identical_message(self, test_db_session):
        nonce = f"nonce-replay-{uuid.uuid4()}"
        ts = datetime.now(timezone.utc).isoformat()

        # First consumption succeeds
        ok1, msg1 = await PersistentReplayProtection.check_and_consume_nonce(
            test_db_session, nonce, ts, station_id="CS-NORDIC-001"
        )
        assert ok1 is True

        # Replayed consumption fails
        ok2, msg2 = await PersistentReplayProtection.check_and_consume_nonce(
            test_db_session, nonce, ts, station_id="CS-NORDIC-001"
        )
        assert ok2 is False
        assert "REPLAY_ATTACK_DETECTED" in msg2

    # ─── 13. Replay After Backend Restart ─────────────────────────────────────
    @pytest.mark.anyio
    async def test_13_replay_after_backend_restart(self):
        """Simulates restarting the backend application with the same SQLite database."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        nonce = f"persisted-nonce-{uuid.uuid4()}"
        ts = datetime.now(timezone.utc).isoformat()

        # Session 1 consumes nonce
        async with session_maker() as session1:
            ok1, _ = await PersistentReplayProtection.check_and_consume_nonce(session1, nonce, ts)
            assert ok1 is True
            await session1.commit()

        # Session 2 (simulating fresh server restart) attempts replay
        async with session_maker() as session2:
            ok2, reason2 = await PersistentReplayProtection.check_and_consume_nonce(session2, nonce, ts)
            assert ok2 is False
            assert "REPLAY_ATTACK_DETECTED" in reason2

        await engine.dispose()

    # ─── 14. Concurrent Duplicate Nonce Requests ──────────────────────────────
    @pytest.mark.anyio
    async def test_14_concurrent_duplicate_nonce_requests(self):
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        nonce = f"concurrent-nonce-{uuid.uuid4()}"
        ts = datetime.now(timezone.utc).isoformat()

        async def worker():
            async with session_maker() as s:
                res, _ = await PersistentReplayProtection.check_and_consume_nonce(s, nonce, ts)
                await s.commit()
                return res

        # Run 2 concurrent tasks attempting identical nonce
        results = await asyncio.gather(worker(), worker())
        # Exactly one must succeed and one must be rejected
        assert results.count(True) == 1
        assert results.count(False) == 1

        await engine.dispose()

    # ─── 15. Invalid OCPP CALL ────────────────────────────────────────────────
    def test_15_invalid_ocpp_call(self):
        # Case A: Bad frame length (3 elements instead of 4)
        v1, _, m1 = OCPPParser.validate_and_parse([2, "uuid-1", "BootNotification"])
        assert v1 is False
        assert "requires exactly 4 elements" in m1

        # Case B: Non-string unique_id (integer)
        v2, _, m2 = OCPPParser.validate_and_parse([2, 9999, "BootNotification", {}])
        assert v2 is False
        assert "UniqueId must be a string" in m2

        # Case C: Non-dict payload
        v3, _, m3 = OCPPParser.validate_and_parse([2, "uuid-1", "BootNotification", "payload-string"])
        assert v3 is False
        assert "must be a JSON object" in m3

    # ─── 16. Invalid OCPP CALLRESULT ──────────────────────────────────────────
    def test_16_invalid_ocpp_callresult(self):
        # Case A: Bad length (4 elements instead of 3)
        v1, _, m1 = OCPPParser.validate_and_parse([3, "uuid-1", {}, "extra"])
        assert v1 is False
        assert "requires exactly 3 elements" in m1

        # Case B: Non-dict payload
        v2, _, m2 = OCPPParser.validate_and_parse([3, "uuid-1", "string-payload"])
        assert v2 is False
        assert "must be a JSON object" in m2

    # ─── 17. Invalid OCPP CALLERROR ───────────────────────────────────────────
    def test_17_invalid_ocpp_callerror(self):
        # Case A: Bad length (4 elements instead of 5)
        v1, _, m1 = OCPPParser.validate_and_parse([4, "uuid-1", "NotImplemented", "Desc"])
        assert v1 is False
        assert "requires exactly 5 elements" in m1

        # Case B: Non-dict details
        v2, _, m2 = OCPPParser.validate_and_parse([4, "uuid-1", "NotImplemented", "Desc", "not-a-dict"])
        assert v2 is False
        assert "ErrorDetails must be a JSON object" in m2

    # ─── 18. Parser Rejection After Successful Hash Verification ──────────────
    def test_18_parser_rejection_after_successful_hash_verification(self):
        # Craft a message with valid SHA-3 hash, but invalid OCPP frame structure
        malformed_frame = [2, 10042, "BootNotification", "not-a-dict-payload"]  # integer unique_id & str payload
        payload = {"ocpp_message": malformed_frame}

        # Wrapping succeeds (hash correctly covers the data)
        wrapped = CryptoWrapper.wrap(payload, mode="sha3_256")

        # Verification executes
        res = CryptoWrapper.verify(wrapped, enforce_mode="sha3_256")

        # Cryptographic check PASSES (no payload tampering)
        assert res["crypto_verified"] is True
        # Protocol parser check FAILS
        assert res["protocol_verified"] is False
        # Dispatch to CSMS parser MUST BE BLOCKED
        assert res["dispatched_to_legacy_parser"] is False
        assert res["verified"] is False
        assert res["error"] == "PROTOCOL_VALIDATION_FAILED"

    # ─── 19. Tampered Payload ─────────────────────────────────────────────────
    def test_19_tampered_payload(self):
        msg = generate_simulated_ev_message("CS-NORDIC-001", "StopTransaction")
        wrapped = CryptoWrapper.wrap(msg, mode="sha3_256")

        # Tamper payload
        tampered = copy.deepcopy(wrapped)
        tampered["payload"]["ocpp_message"][3]["meterStop"] = 99999999

        res = CryptoWrapper.verify(tampered, enforce_mode="sha3_256")
        assert res["verified"] is False
        assert res["crypto_verified"] is False
        assert res["dispatched_to_legacy_parser"] is False
        assert res["error"] == "INTEGRITY_VERIFICATION_FAILED"

    # ─── 20. Unknown Key Rejection ────────────────────────────────────────────
    def test_20_unknown_key_rejection(self):
        msg = generate_simulated_ev_message("CS-METRO-003", "StartTransaction")
        wrapped = CryptoWrapper.wrap(msg, mode="hmac_sha3_256", key_id="key-active-csms-primary")

        # Attacker injects unknown key_id
        tampered = copy.deepcopy(wrapped)
        tampered["crypto_metadata"]["key_id"] = "unknown-key-adversary-injected"

        res = CryptoWrapper.verify(tampered, enforce_mode="hmac_sha3_256")
        assert res["verified"] is False
        assert res["error"] == "UNKNOWN_KEY_ID"
        assert res["dispatched_to_legacy_parser"] is False
