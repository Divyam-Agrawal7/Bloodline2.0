from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class ActionRecommendation(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    DELAY_REVIEW = "DELAY_REVIEW"
    HOLD_FREEZE = "HOLD_FREEZE"

class PaymentOutcome(str, Enum):
    CANCELLED = "CANCELLED"
    PROCEEDED = "PROCEEDED"
    HELD = "HELD"
    RELEASED = "RELEASED"
    BLOCKED = "BLOCKED"

class CaseState(str, Enum):
    SUSPECTED = "suspected"
    SHOW_CAUSE_PENDING = "show_cause_pending"
    REPRESENTATION_WINDOW = "representation_window"
    ORDER_PENDING = "order_pending"
    CLASSIFIED = "classified"
    REPORTED_CLOSED = "reported_closed"
    FALSE_POSITIVE_CLOSED = "false_positive_closed"

class ReasonCode(BaseModel):
    code: str
    evidence: str
    severity: Optional[str] = "MEDIUM"

# Score API
class ScoreRequest(BaseModel):
    transaction_id: str
    amount: float
    currency: str = "USD"
    sender_account_id: str
    receiver_account_id: str
    channel: str = "FAST_PAY"
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ScoreResponse(BaseModel):
    transaction_id: str
    risk_score: float
    recommended_action: ActionRecommendation
    reason_codes: List[ReasonCode]
    model_version: str
    policy_version: str
    decision_id: str
    latency_ms: float
    cooling_off_hours: Optional[int] = None
    customer_warning: Optional[str] = None

# Payee Check API
class PayeeCheckRequest(BaseModel):
    sender_account_id: str
    payee_account_id: str
    transfer_amount: float
    currency: str = "USD"
    channel: str = "MOBILE_APP"

class PayeeCheckResponse(BaseModel):
    payee_account_id: str
    account_age_days: int
    account_status: str
    mule_risk_level: str
    mule_score: float
    is_new_payee_for_sender: bool
    velocity_24h_inflow: float
    shared_device_detected: bool
    recommended_cooling_off_hours: int
    reasons: List[ReasonCode]
    allow_immediate_release: bool

# Vendor Check API
class VendorCheckRequest(BaseModel):
    vendor_id: str
    vendor_name: Optional[str] = "Registered Vendor"
    proposed_destination_account: Optional[str] = None
    destination_account: Optional[str] = None
    invoice_number: Optional[str] = "INV-001"
    amount: float = 450000.0
    currency: str = "INR"
    bank_details_updated_at: Optional[datetime] = None

class VendorCheckResponse(BaseModel):
    vendor_id: str
    risk_level: str
    is_recent_bank_detail_change: bool
    hours_since_bank_change: Optional[float]
    account_mule_score: float
    divergence_flag: bool
    recommended_action: str
    evidence: List[str]
    callback_verification_required: bool
    attack_flagged: Optional[bool] = False
    verdict: Optional[str] = "ALLOW"

# Account Risk API
class AccountRiskResponse(BaseModel):
    account_id: str
    customer_id: str
    account_type: str
    account_age_days: int
    status: str
    composite_mule_score: float
    risk_tier: str
    velocity_in_24h: float
    velocity_out_24h: float
    pass_through_ratio: float
    is_dormant_reactivated: bool
    shared_device_ids: List[str]
    shared_ip_addresses: List[str]
    shared_phone_numbers: List[str]
    linked_case_ids: List[str]
    indicators: List[str]
    provenance_disclaimer: str = "Treat shared signals as uncertain investigative context, not proof of common control."

# Network Graph Subgraph API
class GraphNode(BaseModel):
    id: str
    label: str
    type: str # account, customer, device, phone, ip, payee_vendor, case, honeypot
    risk_score: Optional[float] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str # TRANSFERRED_TO, OWNS_CONTROLS, USED_DEVICE, USED_PHONE, USED_IP, PAID_VENDOR, LINKED_TO_CASE
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    timestamp: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    is_predicted: bool = False
    probability: Optional[float] = None

class NetworkGraphResponse(BaseModel):
    center_account_id: str
    hop_depth: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    disclaimer: str = "Single-bank view. Sensitive identifiers are masked with pseudonymous IDs."

# Lineage / Money DNA API
class LineageRequest(BaseModel):
    origin_transaction_id: str
    time_window_hours: int = 72
    max_hops: int = 4
    proportional_decay: bool = True

class LineageNode(BaseModel):
    id: str
    account_id: str
    account_label: str
    hop_layer: int
    tainted_amount_received: float
    total_inflow: float
    frozen_status: bool
    mule_score: float

class LineageLink(BaseModel):
    source: str
    target: str
    tainted_flow_amount: float
    actual_transfer_amount: float
    timestamp: str
    transaction_id: str
    hop: int
    channel: str

class TimelineStep(BaseModel):
    step_index: int
    timestamp: str
    active_transaction_ids: List[str]
    cumulative_tainted_amount: float
    exited_or_frozen_amount: float
    description: str

class LineageResponse(BaseModel):
    origin_transaction_id: str
    origin_amount: float
    currency: str
    time_window_hours: int
    nodes: List[LineageNode]
    links: List[LineageLink]
    timeline_steps: List[TimelineStep]
    total_tainted_tracked: float
    total_frozen: float
    total_exited: float
    tracing_methodology: str = "Proportional allocation over time window. Estimated lineage is an attribution assumption, not a legal finding."

# Next-Hop Prediction API
class NextHopPredictionRequest(BaseModel):
    account_id: str
    transaction_id: Optional[str] = None
    top_k: int = 5

class NextHopCandidate(BaseModel):
    rank: int
    account_id: str
    pseudonymous_label: str
    predicted_probability: float
    mule_score: float
    evidence: List[str]
    predicted_amount_range: str
    action_proposal: str

class NextHopPredictionResponse(BaseModel):
    source_account_id: str
    candidates: List[NextHopCandidate]
    model_name: str
    fallback_used: bool
    calibration_method: str = "Platt-scaling on held-out synthetic topology"

# Payment Outcome API
class PaymentOutcomeRequest(BaseModel):
    payment_id: str
    outcome: PaymentOutcome
    analyst_id: Optional[str] = "analyst_agent"
    notes: Optional[str] = None

# Case Clock & Audit API
class CreateCaseRequest(BaseModel):
    account_id: str
    transaction_id: Optional[str] = None
    initial_reason: str
    priority: str = "HIGH"
    created_by: str = "analyst_primary"

class CaseTransitionRequest(BaseModel):
    to_state: CaseState
    actor_id: str
    actor_role: str # analyst, senior_investigator, compliance_officer
    reason: str
    approval_token: Optional[str] = None
    notes: Optional[str] = None

class CaseDecisionRequest(BaseModel):
    decision_type: str # CONFIRMED_FRAUD, FALSE_POSITIVE, PENDING_FURTHER_REVIEW
    analyst_id: str
    rationale: str
    evidence_ids: List[str]

class CaseResponse(BaseModel):
    case_id: str
    account_id: str
    transaction_id: Optional[str]
    current_state: CaseState
    priority: str
    created_at: str
    updated_at: str
    deadline_at: Optional[str]
    time_remaining_minutes: Optional[int]
    is_overdue: bool
    assigned_role_required: str
    audit_history: List[Dict[str, Any]]
    draft_document: Optional[Dict[str, Any]]
    evidence_summary: Optional[Dict[str, Any]]

# Impact Ledger & Baseline Comparison
class ImpactMetricsResponse(BaseModel):
    prevented_amount_usd: float
    at_risk_amount_usd: float
    lost_amount_usd: float
    false_positive_friction_usd: float
    net_prevented_savings_usd: float
    comparison_with_rule_baseline: Dict[str, Any]
    evaluation_disclaimer: str = "All metrics derived from synthetic held-out benchmark and do not predict live bank operations."

# Threshold adjustment
class ThresholdAdjustmentRequest(BaseModel):
    threshold_key: str
    new_value: float
    actor_id: str
    justification: str
