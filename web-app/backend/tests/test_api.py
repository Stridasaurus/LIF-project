"""API tests using FastAPI's TestClient."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_defaults_shape():
    resp = client.get("/api/defaults")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("I", "V_thr", "R", "simulation_time", "dt"):
        assert key in body


def test_run_simulation_defaults():
    resp = client.post("/api/run_simulation", json={})
    assert resp.status_code == 200
    body = resp.json()
    n = len(body["time"])
    assert n > 0
    assert len(body["voltage"]) == n
    assert len(body["current"]) == n
    assert len(body["threshold"]) == n
    assert body["meta"]["n_spikes"] == len(body["spike_times"])
    # Defaults sit exactly at rheobase -> no threshold crossing (matches notebook).
    assert body["meta"]["n_spikes"] == 0


def test_run_simulation_suprathreshold_spikes():
    resp = client.post("/api/run_simulation", json={"I": "2.0"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["n_spikes"] > 1


def test_run_simulation_custom_expression():
    resp = client.post(
        "/api/run_simulation",
        json={"I": "1.5 + math.sin(t / 10)", "simulation_time": 100},
    )
    assert resp.status_code == 200


def test_invalid_expression_returns_400():
    resp = client.post(
        "/api/run_simulation",
        json={"I": '__import__("os").system("ls")'},
    )
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_oversized_simulation_returns_422():
    resp = client.post(
        "/api/run_simulation",
        json={"simulation_time": 100000, "dt": 0.001},
    )
    assert resp.status_code == 422


def test_out_of_range_simulation_time_rejected_by_schema():
    resp = client.post(
        "/api/run_simulation",
        json={"simulation_time": 10_000_000},
    )
    # Exceeds schema's le=MAX_SIMULATION_TIME -> 422 from pydantic validation.
    assert resp.status_code == 422
