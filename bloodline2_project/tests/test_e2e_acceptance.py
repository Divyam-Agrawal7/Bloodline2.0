import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_frontend_spa_and_health(client):
    r_index = client.get("/")
    assert r_index.status_code == 200
    assert "Bloodline" in r_index.text or "vite" in r_index.text or "assets" in r_index.text

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    r_ready = client.get("/ready")
    assert r_ready.status_code == 200
    ready_data = r_ready.json()
    assert ready_data["status"] == "ready"
    assert ready_data["accounts_loaded"] >= 1000
    assert ready_data["transactions_loaded"] >= 5000

def test_mule_scan_with_shap_and_counterfactual(client):
    import sqlite3
    conn = sqlite3.connect("data/bloodline.db")
    mule_id = conn.execute("SELECT id FROM accounts WHERE is_mule = 1 LIMIT 1").fetchone()[0]
    conn.close()

    scan_payload = {
        "payee_account_id": mule_id,
        "amount": 95000.0,
        "sender_account_id": "ACC-VIC-01",
        "remark": "Urgent contractor transfer"
    }
    r_scan = client.post("/scan", json=scan_payload)
    assert r_scan.status_code == 200
    scan_data = r_scan.json()
    assert scan_data["verdict"] in ["HOLD", "DELAY"]
    assert scan_data["probability"] >= 0.70
    assert len(scan_data["top_reasons"]) > 0
    assert "counterfactual" in scan_data and len(scan_data["counterfactual"]) > 0
    assert len(scan_data["next_hops"]) > 0
    assert "neighbourhood" in scan_data and "nodes" in scan_data["neighbourhood"]

def test_legitimate_merchant_scan(client):
    import sqlite3
    conn = sqlite3.connect("data/bloodline.db")
    legit_id = conn.execute("SELECT id FROM accounts WHERE is_mule = 0 AND role LIKE '%shop%' OR role LIKE '%retail%' OR role LIKE '%normal%' LIMIT 1").fetchone()[0]
    conn.close()

    legit_scan = client.post("/scan", json={
        "payee_account_id": legit_id,
        "amount": 1250.0,
        "sender_account_id": "ACC-VIC-01",
        "remark": "Grocery purchase"
    })
    assert legit_scan.status_code == 200
    legit_data = legit_scan.json()
    assert legit_data["verdict"] == "ALLOW"
    assert legit_data["probability"] < 0.40

def test_money_dna_lineage_and_hold(client):
    r_lineage = client.get("/lineage/ORIGIN-MULE-CHAIN-01")
    assert r_lineage.status_code == 200
    lin_data = r_lineage.json()
    assert len(lin_data["nodes"]) > 0
    assert len(lin_data["links"]) > 0
    assert len(lin_data["timeline"]) > 0

    r_hold = client.post("/hold-request", json={"account_id": "ACC-MULE-C1-L1-1"})
    assert r_hold.status_code == 200
    hold_data = r_hold.json()
    assert hold_data["outcome"] == "HELD"

def test_case_clock_state_machine_and_simulation(client):
    r_cases = client.get("/cases")
    assert r_cases.status_code == 200
    cases_list = r_cases.json()
    assert len(cases_list) > 0
    case0 = cases_list[0]
    case_id = case0["case_id"]

    r_adv = client.post(f"/case/{case_id}/advance", json={
        "target_stage": "SHOW_CAUSE_ISSUED",
        "human_approved": True,
        "simulate_days": 5
    })
    assert r_adv.status_code == 200
    adv_data = r_adv.json()
    assert adv_data["stage"] == "SHOW_CAUSE_ISSUED"
    assert "show_cause_countdown_days" in adv_data

def test_adaptive_feedback_loop(client):
    r_stats_before = client.get("/stats")
    thresh_before = r_stats_before.json()["current_threshold_hold"]

    for i in range(5):
        client.post("/decision", json={
            "account_id": f"ACC-FP-TEST-{i}",
            "outcome": "FALSE_POSITIVE",
            "analyst_note": "Legitimate customer flagged incorrectly"
        })

    r_stats_after = client.get("/stats")
    thresh_after = r_stats_after.json()["current_threshold_hold"]
    assert thresh_after >= thresh_before

def test_real_metrics_and_rule_baseline(client):
    r_metrics = client.get("/metrics")
    assert r_metrics.status_code == 200
    m_data = r_metrics.json()
    ml_m = m_data["ml_model"]
    rb_m = m_data["rule_baseline"]
    assert ml_m["pr_auc"] > rb_m["pr_auc"]
    assert ml_m["precision"] > rb_m["precision"]
    assert ml_m["false_positive_rate"] < rb_m["false_positive_rate"]

def test_business_shield_invoice_attack_detection(client):
    r_invoices = client.get("/invoices")
    assert r_invoices.status_code == 200
    inv_data = r_invoices.json()["invoices"]
    attacked_inv = [inv for inv in inv_data if inv["is_attacked"] == 1]
    assert len(attacked_inv) > 0

    r_vcheck = client.post("/vendor-check", json={
        "vendor_id": attacked_inv[0]["vendor_id"],
        "destination_account": attacked_inv[0]["account_id"],
        "amount": attacked_inv[0]["amount"]
    })
    assert r_vcheck.status_code == 200
    vcheck_data = r_vcheck.json()
    assert vcheck_data["attack_flagged"] is True
    assert vcheck_data["verdict"] in ["HOLD", "DELAY"]

def test_cross_bank_trace_handoff(client):
    r_handoff = client.post("/trace-handoff", json={
        "case_id": "CASE-DEMO-01",
        "transfer_ref": "TXN-CROSS-001",
        "receiver_account": "ACC-MULE-C1-L2-1",
        "amount": 88000.0,
        "reason_codes": ["FAN_OUT_VELOCITY", "LAYER2_MULE_HUB"]
    })
    assert r_handoff.status_code == 200
    handoff_data = r_handoff.json()
    assert "raw_ledger" not in handoff_data
    assert handoff_data["status"] == "ACKNOWLEDGED_BY_RECIPIENT_BANK"
