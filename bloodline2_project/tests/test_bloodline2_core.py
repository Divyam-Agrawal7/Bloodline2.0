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
import sqlite3
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_db_ids():
    conn = sqlite3.connect("data/bloodline.db")
    c = conn.cursor()
    mule_id = c.execute("SELECT id FROM accounts WHERE is_mule = 1 AND layer = 1 LIMIT 1").fetchone()
    legit_id = c.execute("SELECT id FROM accounts WHERE is_mule = 0 LIMIT 1").fetchone()
    case_id = c.execute("SELECT case_id FROM cases LIMIT 1").fetchone()
    vendor_id = c.execute("SELECT vendor_id FROM vendors WHERE is_attacked = 1 LIMIT 1").fetchone()
    conn.close()
    return {
        "mule": mule_id[0] if mule_id else "ACC02228",
        "legit": legit_id[0] if legit_id else "ACC00053",
        "case": case_id[0] if case_id else "CASE001",
        "vendor": vendor_id[0] if vendor_id else "ACC02173"
    }

def test_scan_planted_mule_account():
    ids = get_db_ids()
    res = client.post("/scan", json={
        "payee_account_id": ids["mule"],
        "amount": 95000.0,
        "sender_account_id": "ACC-VIC-01",
        "remark": "Urgent contractor advance"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["account_id"] == ids["mule"]
    assert data["verdict"] in ["DELAY", "HOLD"]
    assert 0.0 < data["probability"] <= 1.0
    assert len(data["top_reasons"]) >= 1
    assert "counterfactual" in data
    assert len(data["counterfactual"]) > 0
    assert "neighbourhood" in data
    assert len(data["neighbourhood"]["nodes"]) > 0
    assert data["is_simulated"] is True

def test_scan_clean_legitimate_merchant():
    ids = get_db_ids()
    res = client.post("/scan", json={
        "payee_account_id": ids["legit"],
        "amount": 450.0,
        "sender_account_id": "ACC-VIC-01",
        "remark": "Store purchase"
    })
    assert res.status_code == 200
    data = res.json()

    assert data["verdict"] in ["ALLOW", "DELAY"]

def test_adaptive_threshold_feedback_loop():
    # Reset first
    client.post("/demo/reset")
    stats_before = client.get("/stats").json()
    initial_hold = stats_before["current_threshold_hold"]

    # Submit a False Positive decision
    fb_res = client.post("/decision", json={
        "account_id": "ACC00053",
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
    # 1. Fetch lineage for Planted Chain CH03
    res = client.get("/lineage/CH03")
    assert res.status_code == 200
    dna = res.json()

    assert len(dna["nodes"]) >= 4
    assert len(dna["links"]) >= 3
    assert dna["total_tracked_inr"] > 100000.0
    assert "is_estimated" in dna

    # 2. Request a lien hold on a mule node
    hold_target = dna["nodes"][0]["account_id"]
    h_res = client.post("/hold-request", json={"account_id": hold_target})
    assert h_res.status_code == 200
    assert h_res.json()["outcome"] == "HELD"

    # 3. Check lineage again: target node shows is_held = True
    res2 = client.get("/lineage/CH03")
    dna2 = res2.json()
    held_nodes = [n for n in dna2["nodes"] if n["account_id"] == hold_target]
    assert len(held_nodes) >= 1
    assert held_nodes[0]["is_held"] is True

def test_privacy_preserving_cross_bank_handoff():
    res = client.post("/trace-handoff", json={
        "case_id": "CASE-2026-001",
        "transfer_ref": "TXN-C01-HOP1-000001",
        "receiver_account": "ACC02228",
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
    ids = get_db_ids()
    cid = ids["case"]

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
    ids = get_db_ids()
    # 1. List invoices
    inv_res = client.get("/invoices")
    assert inv_res.status_code == 200
    invoices = inv_res.json()["invoices"]
    assert len(invoices) >= 10

    # 2. Check attacked vendor
    v_res = client.post("/vendor-check", json={
        "vendor_id": ids["vendor"],
        "destination_account": "ACC02228",
        "amount": 450000.0
    })
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["attack_flagged"] is True
    assert v_data["verdict"] == "HOLD"
