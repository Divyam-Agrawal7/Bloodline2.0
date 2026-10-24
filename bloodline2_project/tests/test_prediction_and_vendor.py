from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_next_hop_prediction():
    res = client.post("/api/v1/predictions/next-hop", json={
        "account_id": "ACC-MULE-002",
        "top_k": 3
    })
    assert res.status_code == 200
    data = res.json()

    assert data["source_account_id"] == "ACC-MULE-002"
    assert len(data["candidates"]) > 0
    top_cand = data["candidates"][0]
    assert top_cand["rank"] == 1
    assert 0.0 <= top_cand["predicted_probability"] <= 1.0
    assert len(top_cand["evidence"]) > 0
    assert top_cand["action_proposal"] in ["PREEMPTIVE_FREEZE", "DELAY_AND_VERIFY", "MONITOR_FLOW"]

def test_business_shield_vendor_check_tampering():
    # Simulates payout to vendor whose details changed 3 hours ago to a mule account
    payload = {
        "vendor_id": "VEND-CORP-404",
        "vendor_name": "Apex Facilities & Cloud Supplies Ltd",
        "proposed_destination_account": "ACC-MULE-HUB1",
        "invoice_number": "INV-2026-TEST",
        "amount": 85000.0
    }
    res = client.post("/api/v1/vendor-check", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["vendor_id"] == "VEND-CORP-404"
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert data["is_recent_bank_detail_change"] is True
    assert data["divergence_flag"] is True
    assert data["callback_verification_required"] is True
    assert any("diverges" in e for e in data["evidence"])

def test_business_shield_legitimate_vendor():
    payload = {
        "vendor_id": "VEND-CORP-404",
        "vendor_name": "Apex Facilities & Cloud Supplies Ltd",
        "proposed_destination_account": "ACC-LEGIT-CORP",
        "invoice_number": "INV-2026-LEGIT",
        "amount": 45000.0
    }
    res = client.post("/api/v1/vendor-check", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["divergence_flag"] is False
    assert data["account_mule_score"] < 0.20
