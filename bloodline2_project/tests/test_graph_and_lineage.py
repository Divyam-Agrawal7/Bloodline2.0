from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_account_network_graph():
    res = client.get("/api/v1/accounts/ACC-MULE-HUB1/network?hop_depth=2")
    assert res.status_code == 200
    data = res.json()

    assert data["center_account_id"] == "ACC-MULE-HUB1"
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0

    # Ensure device link exists in graph
    node_types = {n["type"] for n in data["nodes"]}
    assert "account" in node_types
    assert "device" in node_types

def test_account_risk_summary():
    res = client.get("/api/v1/accounts/ACC-MULE-HUB1/risk")
    assert res.status_code == 200
    data = res.json()

    assert data["account_id"] == "ACC-MULE-HUB1"
    assert data["composite_mule_score"] > 0.8
    assert data["risk_tier"] == "CRITICAL"
    assert len(data["shared_device_ids"]) > 0
    assert "DEV-SYN-901" in data["shared_device_ids"]
    assert data["pass_through_ratio"] > 0.8

def test_money_dna_lineage_flow():
    payload = {
        "origin_transaction_id": "TXN-ORIGIN-75K",
        "time_window_hours": 72,
        "max_hops": 4,
        "proportional_decay": True
    }
    res = client.post("/api/v1/lineage", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["origin_transaction_id"] == "TXN-ORIGIN-75K"
    assert data["origin_amount"] == 75000.0
    assert len(data["nodes"]) >= 4
    assert len(data["links"]) >= 3
    assert len(data["timeline_steps"]) >= 1

    # Check hops representation
    hop_layers = {n["hop_layer"] for n in data["nodes"]}
    assert 0 in hop_layers # Origin victim
    assert 1 in hop_layers # Mule Hub 1
    assert 2 in hop_layers # Smurfing split mules

    # Ensure frozen values tracked separately
    assert data["total_frozen"] >= 0
    assert "Proportional allocation" in data["tracing_methodology"]
