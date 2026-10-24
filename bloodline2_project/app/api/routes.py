from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
from pathlib import Path

from app.models.schemas import (
    ScoreRequest, ScoreResponse,
    PayeeCheckRequest, PayeeCheckResponse,
    VendorCheckRequest, VendorCheckResponse,
    AccountRiskResponse, NetworkGraphResponse,
    LineageRequest, LineageResponse,
    NextHopPredictionRequest, NextHopPredictionResponse,
    PaymentOutcomeRequest,
    CreateCaseRequest, CaseResponse, CaseTransitionRequest, CaseDecisionRequest,
    ImpactMetricsResponse, ThresholdAdjustmentRequest
)
from app.db.store import BloodlineDatastore
from app.policies.manager import PolicyManager
from app.services.graph_service import GraphService
from app.services.lineage_service import LineageService
from app.services.prediction_service import NextHopPredictionService
from app.services.scoring_service import ScoringService
from app.services.vendor_service import VendorShieldService
from app.services.case_service import CaseService
from app.services.impact_service import ImpactService
from app.services.core_engine import CoreEngine

router = APIRouter(tags=["Bloodline Core APIs"])

# Singletons / Services
store = BloodlineDatastore.get_instance()
policy_mgr = PolicyManager.get_instance()
graph_svc = GraphService(store)
lineage_svc = LineageService(store)
prediction_svc = NextHopPredictionService(store)
scoring_svc = ScoringService(store, policy_mgr, graph_svc)
vendor_svc = VendorShieldService(store)
case_svc = CaseService(store, policy_mgr)
impact_svc = ImpactService(store)
engine = CoreEngine.get_instance()

# -------------------------------------------------------------
# 1. Scoring & Payee Checks
# -------------------------------------------------------------
@router.post("/score", response_model=ScoreResponse, summary="Score a transaction before release")
def score_transaction(req: ScoreRequest):
    return scoring_svc.score_transaction(req)

@router.post("/payee-check", response_model=PayeeCheckResponse, summary="Pre-payment check for beneficiary account/payee")
def check_payee(req: PayeeCheckRequest):
    return scoring_svc.check_payee(req)

@router.post("/vendor-check", response_model=VendorCheckResponse, summary="Check vendor destination risk and bank-detail-change signals")
def check_vendor(req: VendorCheckRequest):
    return vendor_svc.check_vendor_payout(req)

# -------------------------------------------------------------
# 2. Account Risk & Network Graph
# -------------------------------------------------------------
@router.get("/accounts/{account_id}/risk", response_model=AccountRiskResponse, summary="Retrieve current account risk summary and evidence references")
def get_account_risk(account_id: str):
    acc = store.accounts.get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")

    patterns = graph_svc.detect_mule_patterns(account_id)
    mule_score = acc.get("mule_score", 0.1)

    tier = "CRITICAL" if mule_score >= 0.8 else "ELEVATED" if mule_score >= 0.4 else "LOW"

    indicators = []
    if patterns.get("is_fan_out"):
        indicators.append("Rapid fan-out smurfing dispersal")
    if patterns.get("is_fan_in"):
        indicators.append("High inbound aggregator concentration")
    if patterns.get("has_structuring"):
        indicators.append("Sub-threshold structuring transactions")
    if patterns.get("has_cycle"):
        indicators.append("Circular flow loop participation")
    if acc.get("is_dormant_reactivated"):
        indicators.append("Sudden reactivation after long dormancy")
    if patterns.get("shared_devices"):
        indicators.append(f"Shared device ID: {patterns['shared_devices'][0]}")

    linked_cases = [c["case_id"] for c in store.cases.values() if c.get("account_id") == account_id]

    return AccountRiskResponse(
        account_id=account_id,
        customer_id=acc.get("customer_id", "CUST-UNKNOWN"),
        account_type=acc.get("account_type", "CHECKING"),
        account_age_days=14 if "MULE" in account_id else 850,
        status=acc.get("status", "ACTIVE"),
        composite_mule_score=mule_score,
        risk_tier=tier,
        velocity_in_24h=acc.get("velocity_in_24h", 0.0),
        velocity_out_24h=acc.get("velocity_out_24h", 0.0),
        pass_through_ratio=patterns.get("pass_through_ratio", 0.0),
        is_dormant_reactivated=acc.get("is_dormant_reactivated", False),
        shared_device_ids=patterns.get("shared_devices", []),
        shared_ip_addresses=patterns.get("shared_ips", []),
        shared_phone_numbers=patterns.get("shared_phones", []),
        linked_case_ids=linked_cases,
        indicators=indicators
    )

@router.get("/accounts/{account_id}/network", response_model=NetworkGraphResponse, summary="Retrieve a filtered, bounded neighborhood graph")
def get_account_network(
    account_id: str,
    hop_depth: int = Query(default=2, ge=1, le=3),
    min_amount: Optional[float] = Query(default=None)
):
    return graph_svc.get_account_network(account_id=account_id, hop_depth=hop_depth, min_amount=min_amount)

# -------------------------------------------------------------
# 3. Money DNA / Lineage
# -------------------------------------------------------------
@router.post("/lineage", response_model=LineageResponse, summary="Build estimated lineage for an origin transaction and time window")
def get_lineage(req: LineageRequest):
    return lineage_svc.build_money_dna(
        origin_txn_id=req.origin_transaction_id,
        time_window_hours=req.time_window_hours,
        max_hops=req.max_hops,
        proportional_decay=req.proportional_decay
    )

@router.get("/chains", summary="List mule chains available for Money DNA lineage (Bloodline 2.0)")
def list_chains():
    conn = engine._get_conn()
    rows = conn.execute("""
        SELECT chain_id, COUNT(*) AS transfers, ROUND(SUM(amount), 2) AS volume,
               MIN(ts) AS first_ts, MAX(ts) AS last_ts
        FROM transactions WHERE chain_id IS NOT NULL
        GROUP BY chain_id ORDER BY chain_id
    """).fetchall()
    conn.close()
    return {"chains": [dict(r) for r in rows]}

@router.get("/lineage/{origin_txn}", summary="Retrieve Money DNA proportional flow lineage DAG (Bloodline 2.0)")
def get_lineage_get(origin_txn: str):
    return engine.get_money_dna_lineage(origin_ref=origin_txn)

# -------------------------------------------------------------
# 4. Next-Hop Predictions
# -------------------------------------------------------------
@router.post("/predictions/next-hop", response_model=NextHopPredictionResponse, summary="Return ranked candidate next-hop accounts with calibrated confidence")
def predict_next_hop_legacy(req: NextHopPredictionRequest):
    return prediction_svc.predict_next_hop(
        account_id=req.account_id,
        transaction_id=req.transaction_id,
        top_k=req.top_k
    )

@router.post("/predict-next-hop", summary="Predict top 3 downstream mule hop destinations (Bloodline 2.0)")
def predict_next_hop_v2(req: Dict[str, Any]):
    account_id = req.get("account_id", "ACC-MULE-C01-L1-1")
    amount = float(req.get("amount") or 50000.0)
    top_k = int(req.get("top_k", 3))
    hops = engine.predict_next_hops(account_id, amount)[:top_k]
    return {
        "account_id": account_id,
        "top_next_hops": hops,
        "is_simulated": True
    }

# -------------------------------------------------------------
# 5. Payment Outcomes & Cooling-Off
# -------------------------------------------------------------
@router.post("/payments/{payment_id}/outcomes", summary="Record cancelled, proceeded, held, released, or other bank-defined outcome")
def record_outcome(payment_id: str, req: PaymentOutcomeRequest):
    req.payment_id = payment_id
    return case_svc.record_payment_outcome(req)

# -------------------------------------------------------------
# 6. Cases & Workflow State Machine
# -------------------------------------------------------------
@router.get("/cases", summary="List all investigation cases (Bloodline 2.0)")
def list_cases():
    return engine.list_all_cases()

@router.post("/cases", response_model=CaseResponse, summary="Create an investigation case")
def create_case(req: CreateCaseRequest):
    return case_svc.create_case(req)

@router.get("/cases/{case_id}", response_model=CaseResponse, summary="Retrieve an investigation case")
def get_case(case_id: str):
    res = case_svc.get_case(case_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return res

@router.post("/cases/{case_id}/transitions", response_model=CaseResponse, summary="Request a state transition; enforce authorization and approval requirements")
def transition_case(case_id: str, req: CaseTransitionRequest):
    try:
        return case_svc.transition_state(case_id, req)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cases/{case_id}/decisions", summary="Record analyst decision, label, rationale, and evidence references")
def record_case_decision(case_id: str, req: CaseDecisionRequest):
    try:
        return case_svc.record_decision(case_id, req)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/case/{case_id}/advance", summary="Advance Case Clock stage or simulate elapsed days (Bloodline 2.0)")
def advance_case_endpoint(case_id: str, req: Dict[str, Any]):
    try:
        return engine.advance_case_stage(
            case_id=case_id,
            target_stage=req.get("target_stage"),
            human_approved=req.get("human_approved", False),
            simulate_days=req.get("simulate_days", 0)
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

# -------------------------------------------------------------
# 7. Impact Ledger & Baseline Comparison
# -------------------------------------------------------------
@router.get("/impact", response_model=ImpactMetricsResponse, summary="Return status-ledger totals and baseline comparison for a time range")
def get_impact():
    return impact_svc.get_impact_metrics()

@router.get("/stats", summary="Live impact counters and exposure avoided (Bloodline 2.0)")
def get_stats_endpoint():
    return engine.get_impact_stats()

# -------------------------------------------------------------
# 8. Bounded Threshold Management
# -------------------------------------------------------------
@router.get("/thresholds", summary="Get current policy decision thresholds and bounded guardrails")
def get_thresholds():
    return {
        "policy_version": policy_mgr.version,
        "thresholds": policy_mgr.thresholds,
        "history": policy_mgr.get_threshold_history()
    }

@router.post("/thresholds", summary="Adjust decision threshold within bounded observable guardrails")
def adjust_threshold(req: ThresholdAdjustmentRequest):
    try:
        res = policy_mgr.adjust_threshold(
            key=req.threshold_key,
            new_value=req.new_value,
            actor=req.actor_id,
            reason=req.justification
        )
        return {"status": "UPDATED", "record": res}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------
# 9. Synthetic Demo Reset Endpoint
# -------------------------------------------------------------
@router.post("/demo/reset", summary="Reset synthetic demo environment to default pristine state")
def reset_demo():
    store.reset()
    engine.reset_demo()
    return {"status": "SUCCESS", "message": "Synthetic graph and demo database reset to default state"}

# -------------------------------------------------------------
# 10. Bloodline 2.0 Core Unified APIs
# -------------------------------------------------------------
@router.post("/scan", summary="Unified real-time risk scan for payment or payee (Bloodline 2.0)")
def unified_scan(req: Dict[str, Any]):
    payee = req.get("payee_account_id") or req.get("account_id") or "ACC-MULE-C01-L1-1"
    amt = float(req.get("amount") or 95000.0)
    snd = req.get("sender_account_id", "ACC-VIC-01")
    rem = req.get("remark", "Payment")
    return engine.scan_entity(payee_account_id=payee, amount=amt, sender_account_id=snd, remark=rem)

@router.post("/trace-handoff", summary="Privacy-preserving cross-bank handoff (Bloodline 2.0)")
def trace_handoff(req: Dict[str, Any]):
    return engine.execute_cross_bank_handoff(
        case_id=req.get("case_id", "CASE-2026-001"),
        transfer_ref=req.get("transfer_ref", "REF-MULE-001"),
        receiver_account=req.get("receiver_account", "ACC-MULE-C01-L1-1"),
        amount=float(req.get("amount", 95000.0)),
        reason_codes=req.get("reason_codes", ["RAPID_PASS_THROUGH", "SHARED_HARDWARE"])
    )

@router.post("/decision", summary="Submit human outcome and tune adaptive threshold (Bloodline 2.0)")
def record_decision_v2(req: Dict[str, Any]):
    return engine.record_decision_feedback(
        account_id=req["account_id"],
        txn_id=req.get("txn_id"),
        outcome=req["outcome"],
        analyst_note=req.get("analyst_note")
    )

@router.post("/hold-request", summary="Request administrative lien/hold on an account (Bloodline 2.0)")
def request_hold(account_id: str = Body(..., embed=True)):
    engine.requested_holds.add(account_id)
    return engine.record_decision_feedback(
        account_id=account_id,
        txn_id=None,
        outcome="HELD",
        analyst_note="Analyst requested administrative lien hold from Money DNA console"
    )

@router.get("/invoices", summary="List Business Shield invoices (Bloodline 2.0)")
def list_invoices():
    conn = engine._get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, v.vendor_name, v.is_attacked, v.attack_description, v.original_account_id
        FROM invoices i
        JOIN vendors v ON i.vendor_id = v.vendor_id
        ORDER BY i.due_date ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"invoices": rows, "is_simulated": True}

@router.get("/metrics", summary="Read real evaluation metrics from eval/metrics.json (Bloodline 2.0)")
def get_metrics_endpoint():
    metrics_path = Path("eval/metrics.json")
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Metrics file eval/metrics.json not found")
    with open(metrics_path) as f:
        data = json.load(f)
    return data

@router.get("/mules", summary="List all detected mule accounts (Bloodline 2.0)")
def list_detected_mules():
    conn = engine._get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.pseudonymous_label, a.bank_id, a.role, a.chain_id, a.layer, 
               a.initial_balance, a.current_balance, a.kyc_tier,
               COUNT(d.device_id) as shared_devices
        FROM accounts a
        LEFT JOIN devices d ON a.id = d.account_id
        WHERE a.is_mule = 1
        GROUP BY a.id
        ORDER BY a.layer ASC, a.id ASC
    """)
    mules = []
    for r in cursor.fetchall():
        d = dict(r)
        d["is_held"] = d["id"] in engine.requested_holds
        d["mule_score"] = 0.99 if d["layer"] <= 1 else 0.88
        mules.append(d)
    conn.close()
    return {"mules": mules, "total_count": len(mules), "is_simulated": True}

@router.get("/transactions", summary="List live transaction ledger feed (Bloodline 2.0)")
def list_live_transactions(limit: int = 150, chain_id: Optional[str] = None):
    conn = engine._get_conn()
    cursor = conn.cursor()
    query = """
        SELECT t.id, t.ts, t.epoch_seconds, t.sender, t.receiver, t.amount, t.channel, 
               t.ref, t.is_mule_flow, t.chain_id,
               s.pseudonymous_label as sender_name, s.bank_id as sender_bank,
               r.pseudonymous_label as receiver_name, r.bank_id as receiver_bank
        FROM transactions t
        LEFT JOIN accounts s ON t.sender = s.id
        LEFT JOIN accounts r ON t.receiver = r.id
    """
    params = []
    if chain_id:
        query += " WHERE t.chain_id = ? "
        params.append(chain_id)
    query += " ORDER BY t.epoch_seconds DESC LIMIT ? "
    params.append(limit)

    cursor.execute(query, tuple(params))
    txns = []
    for r in cursor.fetchall():
        d = dict(r)
        is_held = (d["sender"] in engine.requested_holds) or (d["receiver"] in engine.requested_holds)
        d["status"] = "HELD (LIEN)" if is_held else ("MULE DISPERSAL" if d["is_mule_flow"] else "CLEARED")
        txns.append(d)
    conn.close()
    return {"transactions": txns, "total_count": len(txns), "is_simulated": True}

@router.get("/demo/story", summary="Retrieve deterministic 5-minute demo story anchors")
def get_demo_story():
    return {
        "title": "Bloodline 2.0 Five-Minute Bank Fraud & Mule Defense Walkthrough",
        "anchors": {
            "planted_victim": "ACC-VIC-01",
            "planted_mule_l1": "ACC-MULE-C1-L1-1",
            "planted_mule_l2": "ACC-MULE-C1-L2-1",
            "planted_exit": "ACC-EXIT-C1-1",
            "planted_vendor_attack": "VEND-003",
            "planted_lineage_ref": "ORIGIN-MULE-CHAIN-01"
        },
        "description": "Deterministic story covering pre-payment customer pop-up, Money DNA replay, Business Shield invoice protection, Case Clock 21-day show-cause, and real model metrics."
    }
