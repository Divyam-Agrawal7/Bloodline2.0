from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_ready_probes():
    h_res = client.get("/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"

    r_res = client.get("/ready")
    assert r_res.status_code == 200
    assert r_res.json()["status"] == "ready"
    assert r_res.json()["accounts_loaded"] > 0

def test_score_suspicious_mule_transaction():
    payload = {
        "transaction_id": "TXN-TEST-001",
        "amount": 75000.0,
        "currency": "USD",
        "sender_account_id": "ACC-VICTIM-01",
        "receiver_account_id": "ACC-MULE-HUB1",
        "channel": "WIRE"
    }
    res = client.post("/api/v1/score", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["transaction_id"] == "TXN-TEST-001"
    assert data["risk_score"] >= 0.70
    assert data["recommended_action"] in ["DELAY_REVIEW", "HOLD_FREEZE"]
    assert len(data["reason_codes"]) > 0
    assert any(r["code"] in ["RAPID_PASS_THROUGH", "HIGH_VELOCITY_FAN_OUT", "SHARED_HARDWARE_ASSOCIATION"] for r in data["reason_codes"])
    assert data["model_version"] == "demo-2026-01"
    assert data["policy_version"] == "synthetic-demo-v1"
    assert "decision_id" in data
    assert data["latency_ms"] >= 0

def test_score_legitimate_payroll():
    payload = {
        "transaction_id": "TXN-TEST-LEGIT",
        "amount": 3200.0,
        "currency": "USD",
        "sender_account_id": "ACC-LEGIT-CORP",
        "receiver_account_id": "ACC-LEGIT-RETAIL",
        "channel": "ACH"
    }
    res = client.post("/api/v1/score", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["risk_score"] < 0.40
    assert data["recommended_action"] == "ALLOW"
    assert data["cooling_off_hours"] is None

def test_payee_check():
    res = client.post("/api/v1/payee-check", json={
        "sender_account_id": "ACC-VICTIM-01",
        "payee_account_id": "ACC-MULE-HUB1",
        "transfer_amount": 50000.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["payee_account_id"] == "ACC-MULE-HUB1"
    assert data["mule_risk_level"] in ["ELEVATED", "CRITICAL"]
    assert data["shared_device_detected"] is True
    assert data["recommended_cooling_off_hours"] >= 2
