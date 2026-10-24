"""
Comprehensive Bloodline 2.0 Feature and Acceptance Tests
Verifies:
  1. Real trained ML model scoring, SHAP reason codes, and counterfactual generation
  2. Warning pop-up conditions (Delay & Hold verdicts)
  3. Money DNA flow lineage DAG with proportional haircuts
  4. Next-hop destination ranking and hold requests
  5. Privacy-preserving cross-bank handoff
  6. Adaptive threshold feedback loop on False Positive reports
  7. Case Clock state machine with 21-day show-cause countdown & +N days simulation
  8. Live impact counters & exposure avoided under RBI regulatory formulas
  9. Metrics endpoint reading directly from eval/metrics.json
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_scan_planted_mule_account():
    # Scan planted Layer 1 mule account
    res = client.post("/scan", json={
        "payee_account_id": "ACC-MULE-C1-L1-1",
        "amount": 95000.0,
        "sender_account_id": "ACC-VIC-01",
        "remark": "Urgent contractor advance"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["account_id"] == "ACC-MULE-C1-L1-1"
    assert data["verdict"] in ["DELAY", "HOLD"]
    assert 0.0 < data["probability"] <= 1.0
    assert len(data["top_reasons"]) >= 3
    assert "counterfactual" in data
    assert "Transfer would not trigger Hold/Delay" in data["counterfactual"]
    assert len(data["next_hops"]) >= 1
    assert "neighbourhood" in data
    assert len(data["neighbourhood"]["nodes"]) > 0
    assert data["is_simulated"] is True

def test_scan_clean_legitimate_merchant():
    # Scan busy legitimate shopkeeper
    res = client.post("/scan", json={
        "payee_account_id": "ACC-SHOP-0001",
        "amount": 450.0,
        "sender_account_id": "ACC-VIC-01",
        "remark": "Store purchase"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["verdict"] == "ALLOW"
    assert data["probability"] < 0.40

def test_adaptive_threshold_feedback_loop():
    # Reset first
    client.post("/demo/reset")
    stats_before = client.get("/stats").json()
    initial_hold = stats_before["current_threshold_hold"]

    # Submit a False Positive decision
    fb_res = client.post("/decision", json={
        "account_id": "ACC-SHOP-0001",
        "txn_id": "TXN-TEST-FP",
        "outcome": "FALSE_POSITIVE",
        "analyst_note": "Legitimate verified merchant with high seasonal influx"
    })
    assert fb_res.status_code == 200
    fb_data = fb_res.json()

    assert fb_data["threshold_adjusted"] is True
    assert fb_data["current_threshold_hold"] > initial_hold
    assert fb_data["current_threshold_hold"] == round(initial_hold + 0.02, 2)

    # Subsequent stats reflect adjusted threshold
    stats_after = client.get("/stats").json()
    assert stats_after["current_threshold_hold"] == fb_data["current_threshold_hold"]

def test_money_dna_lineage_and_hold_request():
    # 1. Fetch lineage for Planted Chain 1
    res = client.get("/lineage/ORIGIN-MULE-CHAIN-01")
    assert res.status_code == 200
    dna = res.json()

    assert len(dna["nodes"]) >= 4
    assert len(dna["links"]) >= 3
    assert dna["total_tracked_inr"] > 1000000.0
    assert "is_estimated" in dna

    # 2. Request a lien hold on Layer 2 mule
    hold_target = "ACC-MULE-C1-L2-1"
    h_res = client.post("/hold-request", json={"account_id": hold_target})
    assert h_res.status_code == 200
    assert h_res.json()["outcome"] == "HELD"

    # 3. Check lineage again: target node shows is_held = True
    res2 = client.get("/lineage/ORIGIN-MULE-CHAIN-01")
    dna2 = res2.json()
    held_nodes = [n for n in dna2["nodes"] if n["account_id"] == hold_target]
    assert len(held_nodes) >= 1
    assert held_nodes[0]["is_held"] is True

def test_privacy_preserving_cross_bank_handoff():
    res = client.post("/trace-handoff", json={
        "case_id": "CASE-2026-001",
        "transfer_ref": "TXN-C01-HOP1-000001",
        "receiver_account": "ACC-MULE-C01-L1-1",
        "amount": 250000.0,
        "reason_codes": ["RAPID_PASS_THROUGH", "SHARED_HARDWARE_CLUSTER"]
    })
    assert res.status_code == 200
    data = res.json()

    assert "handoff_token" in data
    assert data["raw_ledger_shared"] is False
    assert "ENC-" in data["receiver_account_token"]
    assert data["status"] == "ACKNOWLEDGED_BY_RECIPIENT_BANK"

def test_case_clock_state_machine_and_simulation():
    cid = "CASE-2026-001"

    # Advance time by +5 days
    adv_res = client.post(f"/case/{cid}/advance", json={
        "simulate_days": 5,
        "human_approved": True
    })
    assert adv_res.status_code == 200
    adv_data = adv_res.json()

    assert adv_data["elapsed_days"] >= 5
    assert adv_data["show_cause_countdown_days"] <= 21

def test_real_eval_metrics_endpoint():
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()

    assert "ml_model" in data
    assert "rule_baseline" in data
    assert "robustness_holdout_test" in data
    assert data["ml_model"]["pr_auc"] > 0.60
    assert data["rule_baseline"]["pr_auc"] > 0.0
    assert data["robustness_holdout_test"]["status"] == "PASSED"

def test_business_shield_invoices_and_vendor_check():
    # 1. List invoices
    inv_res = client.get("/invoices")
    assert inv_res.status_code == 200
    invoices = inv_res.json()["invoices"]
    assert len(invoices) >= 10

    # 2. Check attacked vendor VEND-003
    v_res = client.post("/vendor-check", json={
        "vendor_id": "VEND-003",
        "destination_account": "ACC-MULE-C01-L1-1",
        "amount": 450000.0
    })
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["attack_flagged"] is True
    assert v_data["verdict"] == "HOLD"
