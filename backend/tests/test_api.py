import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestAPIEndpoints:
    """End-to-end integration tests for all EVHashGuard REST API endpoints."""

    def test_health_endpoint(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["cryptography"]["sha3_supported"] is True

    def test_hash_compare_endpoint(self, client):
        payload = {
            "message": "EV_TELEMETRY_PACKET_2026",
            "algorithms": ["md5", "sha256", "sha3_256"]
        }
        response = client.post("/api/hash/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == payload["message"]
        assert len(data["results"]) == 3
        algos = [r["algorithm"] for r in data["results"]]
        assert "sha3_256" in algos

    def test_collision_verify_endpoint_default(self, client):
        # Empty inputs triggers loading of the verified Wang/Stevens collision vector
        response = client.post("/api/collision/verify", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["collision_detected"] is True
        assert data["inputs_differ"] is True
        assert data["md5_1"] == data["md5_2"]
        assert data["sha256_1"] != data["sha256_2"]

    def test_simulator_stations_endpoint(self, client):
        response = client.get("/api/simulator/stations")
        assert response.status_code == 200
        stations = response.json()
        assert isinstance(stations, list)
        assert len(stations) >= 5
        assert any(s["station_id"] == "CS-NORDIC-001" for s in stations)

    def test_ev_messages_endpoint(self, client):
        payload = {
            "station_id": "CS-NORDIC-001",
            "message_type": "BootNotification"
        }
        response = client.post("/api/ev/messages", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["station_id"] == "CS-NORDIC-001"
        assert "ocpp_message" in data
        assert "legacy_integrity_metadata" in data
        assert data["legacy_integrity_metadata"]["algorithm"] == "MD5"

    def test_legacy_verify_endpoint(self, client):
        payload = {
            "payload_json": '{"status":"Available","connectorId":1}',
            "legacy_md5": "00000000000000000000000000000000"
        }
        response = client.post("/api/legacy/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        assert "security_warning" in data

    def test_migration_wrap_and_verify_endpoint(self, client):
        # 1. Wrap message
        msg_payload = {"chargePointVendor": "NordicVolt", "firmware": "v1.4.2"}
        wrap_req = {
            "payload": msg_payload,
            "mode": "sha3_256"
        }
        wrap_res = client.post("/api/migration/wrap", json=wrap_req)
        assert wrap_res.status_code == 200
        wrapped_data = wrap_res.json()["wrapped_message"]

        # 2. Verify wrapped message
        verify_req = {
            "wrapped_message": wrapped_data,
            "mode": "sha3_256"
        }
        verify_res = client.post("/api/migration/verify", json=verify_req)
        assert verify_res.status_code == 200
        v_data = verify_res.json()
        assert v_data["verified"] is True
        assert v_data["algorithm"] == "SHA3-256"

    def test_attack_endpoints(self, client):
        # Test tampering
        r_tamp = client.post("/api/attacks/tampering")
        assert r_tamp.status_code == 200
        assert r_tamp.json()["detected"] is True

        # Test replay
        r_rep = client.post("/api/attacks/replay")
        assert r_rep.status_code == 200
        assert r_rep.json()["detected"] is True

        # Test downgrade
        r_down = client.post("/api/attacks/downgrade")
        assert r_down.status_code == 200
        assert r_down.json()["detected"] is True

        # Test collision attack
        r_col = client.post("/api/attacks/collision")
        assert r_col.status_code == 200
        assert r_col.json()["detected"] is True

        # Test missing metadata
        r_meta = client.post("/api/attacks/missing-metadata")
        assert r_meta.status_code == 200
        assert r_meta.json()["detected"] is True

        # Test invalid tag
        r_tag = client.post("/api/attacks/invalid-tag")
        assert r_tag.status_code == 200
        assert r_tag.json()["detected"] is True

        # Test firmware mod
        r_fmod = client.post("/api/attacks/firmware-mod")
        assert r_fmod.status_code == 200
        assert r_fmod.json()["detected"] is True

    def test_collision_invalid_hex_handling(self, client):
        r = client.post("/api/collision/verify", json={"input1_hex": "not_valid_hex", "input2_hex": "1234"})
        assert r.status_code == 400
        assert "hexadecimal" in r.json()["detail"].lower()

    def test_risk_analysis_endpoint(self, client):
        response = client.get("/api/risk/analysis")
        assert response.status_code == 200
        data = response.json()
        assert "evaluations" in data
        eval_algos = [e["algorithm"] for e in data["evaluations"]]
        assert "MD5" in eval_algos
        assert "SHA3-256" in eval_algos
        assert "HMAC-SHA3-256" in eval_algos

    def test_dashboard_stats_endpoint(self, client):
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "total_messages_processed" in stats
        assert "successful_verifications" in stats
        assert "algorithm_usage" in stats
        assert "active_charging_stations" in stats

    def test_audit_logs_endpoint(self, client):
        response = client.get("/api/audit/logs?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
