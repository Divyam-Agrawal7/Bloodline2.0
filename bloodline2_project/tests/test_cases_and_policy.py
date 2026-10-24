import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_case_lifecycle_and_role_enforcement():
    # 1. Create a new case
    create_res = client.post("/api/v1/cases", json={
        "account_id": "ACC-MULE-HUB1",
        "transaction_id": "TXN-ORIGIN-75K",
        "initial_reason": "High-velocity smurfing trigger test",
        "priority": "HIGH",
        "created_by": "analyst_primary"
    })
    assert create_res.status_code == 200
    case_data = create_res.json()
    case_id = case_data["case_id"]
    assert case_data["current_state"] == "suspected"
    assert len(case_data["audit_history"]) >= 1

    # 2. Transition from suspected -> show_cause_pending by senior_investigator
    trans_res = client.post(f"/api/v1/cases/{case_id}/transitions", json={
        "to_state": "show_cause_pending",
        "actor_id": "investigator_dan",
        "actor_role": "senior_investigator",
        "reason": "Mule indicators verified"
    })
    assert trans_res.status_code == 200
    assert trans_res.json()["current_state"] == "show_cause_pending"

    # 3. Invalid transition test: analyst cannot approve final classification
    invalid_res = client.post(f"/api/v1/cases/{case_id}/transitions", json={
        "to_state": "classified",
        "actor_id": "analyst_junior",
        "actor_role": "analyst",
        "reason": "Attempting unauthorized classification"
    })
    assert invalid_res.status_code == 400

    # 4. Valid representation window transition
    rep_res = client.post(f"/api/v1/cases/{case_id}/transitions", json={
        "to_state": "representation_window",
        "actor_id": "investigator_dan",
        "actor_role": "senior_investigator",
        "reason": "48h statutory representation notice delivered"
    })
    assert rep_res.status_code == 200
    assert rep_res.json()["current_state"] == "representation_window"

    # 5. False positive closure path test
    fp_res = client.post(f"/api/v1/cases/{case_id}/transitions", json={
        "to_state": "false_positive_closed",
        "actor_id": "analyst_primary",
        "actor_role": "analyst",
        "reason": "Legitimate business purpose demonstrated"
    })
    assert fp_res.status_code == 200
    assert fp_res.json()["current_state"] == "false_positive_closed"

def test_bounded_threshold_adjustment():
    # Valid bounded change within [0.50, 0.95]
    res = client.post("/api/v1/thresholds", json={
        "threshold_key": "hold_freeze_min",
        "new_value": 0.85,
        "actor_id": "compliance_head",
        "justification": "Calibrated risk tightening"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "UPDATED"

    # Out of bounds change (e.g. 0.30 is below min_allowable 0.50)
    oob_res = client.post("/api/v1/thresholds", json={
        "threshold_key": "hold_freeze_min",
        "new_value": 0.30,
        "actor_id": "compliance_head",
        "justification": "Too low"
    })
    assert oob_res.status_code == 400
    assert "outside bounded threshold guardrail" in oob_res.json()["detail"]

def test_impact_ledger_and_baseline():
    res = client.get("/api/v1/impact")
    assert res.status_code == 200
    data = res.json()

    assert data["prevented_amount_usd"] >= 450000.0
    assert data["at_risk_amount_usd"] >= 90000.0
    assert data["comparison_with_rule_baseline"] is not None
    assert len(data["comparison_with_rule_baseline"]["metrics"]) >= 5
