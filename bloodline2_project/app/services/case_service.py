import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.db.store import BloodlineDatastore
from app.policies.manager import PolicyManager
from app.models.schemas import (
    CaseResponse, CaseState, CreateCaseRequest, CaseTransitionRequest,
    CaseDecisionRequest, PaymentOutcomeRequest
)

class CaseService:
    VALID_TRANSITIONS = {
        CaseState.SUSPECTED: [CaseState.SHOW_CAUSE_PENDING, CaseState.FALSE_POSITIVE_CLOSED],
        CaseState.SHOW_CAUSE_PENDING: [CaseState.REPRESENTATION_WINDOW, CaseState.FALSE_POSITIVE_CLOSED],
        CaseState.REPRESENTATION_WINDOW: [CaseState.ORDER_PENDING, CaseState.FALSE_POSITIVE_CLOSED],
        CaseState.ORDER_PENDING: [CaseState.CLASSIFIED, CaseState.FALSE_POSITIVE_CLOSED],
        CaseState.CLASSIFIED: [CaseState.REPORTED_CLOSED, CaseState.FALSE_POSITIVE_CLOSED],
        CaseState.REPORTED_CLOSED: [],
        CaseState.FALSE_POSITIVE_CLOSED: []
    }

    ROLE_PERMISSIONS = {
        "analyst": [CaseState.SUSPECTED, CaseState.FALSE_POSITIVE_CLOSED],
        "senior_investigator": [CaseState.SHOW_CAUSE_PENDING, CaseState.REPRESENTATION_WINDOW, CaseState.ORDER_PENDING, CaseState.FALSE_POSITIVE_CLOSED],
        "compliance_officer": [CaseState.CLASSIFIED, CaseState.REPORTED_CLOSED, CaseState.FALSE_POSITIVE_CLOSED]
    }

    def __init__(self, store: Optional[BloodlineDatastore] = None, policy_mgr: Optional[PolicyManager] = None):
        self.store = store or BloodlineDatastore.get_instance()
        self.policy_mgr = policy_mgr or PolicyManager.get_instance()

    def get_case(self, case_id: str) -> Optional[CaseResponse]:
        c = self.store.cases.get(case_id)
        if not c:
            return None
        return self._format_case_response(c)

    def list_cases(self) -> List[CaseResponse]:
        return [self._format_case_response(c) for c in self.store.cases.values()]

    def create_case(self, req: CreateCaseRequest) -> CaseResponse:
        case_id = f"CASE-{datetime.now(timezone.utc).strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=24) # 24h for initial triage

        case_obj = {
            "case_id": case_id,
            "account_id": req.account_id,
            "transaction_id": req.transaction_id,
            "current_state": CaseState.SUSPECTED.value,
            "priority": req.priority,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "deadline_at": deadline.isoformat(),
            "assigned_role_required": "analyst",
            "audit_history": [
                {
                    "timestamp": now.isoformat(),
                    "actor_id": req.created_by,
                    "actor_role": "analyst",
                    "prior_state": "None",
                    "new_state": CaseState.SUSPECTED.value,
                    "reason": req.initial_reason,
                    "notes": "Automated case initiation from risk threshold breach"
                }
            ],
            "draft_document": self._generate_draft_document(req.account_id, req.transaction_id),
            "evidence_summary": self._generate_evidence_summary(req.account_id)
        }
        self.store.cases[case_id] = case_obj
        return self._format_case_response(case_obj)

    def transition_state(self, case_id: str, req: CaseTransitionRequest) -> CaseResponse:
        c = self.store.cases.get(case_id)
        if not c:
            raise KeyError(f"Case {case_id} not found")

        curr_state = CaseState(c["current_state"])
        target_state = req.to_state

        # Check state transition rules
        allowed = self.VALID_TRANSITIONS.get(curr_state, [])
        if target_state not in allowed:
            raise ValueError(
                f"Invalid transition from '{curr_state.value}' to '{target_state.value}'. "
                f"Permitted next states: {[s.value for s in allowed]}"
            )

        # Check role-based permission
        allowed_states_for_role = self.ROLE_PERMISSIONS.get(req.actor_role, [])
        if target_state not in allowed_states_for_role:
            raise PermissionError(
                f"Role '{req.actor_role}' does not have authority to transition case to '{target_state.value}'. "
                f"Authorised roles: {[r for r, s_list in self.ROLE_PERMISSIONS.items() if target_state in s_list]}"
            )

        now = datetime.now(timezone.utc)
        
        # Calculate new deadline from policy
        deadlines_config = self.policy_mgr.case_clock_config.get("deadlines_hours", {})
        hours = deadlines_config.get(target_state.value, 24)
        new_deadline = (now + timedelta(hours=hours)).isoformat() if target_state not in [CaseState.REPORTED_CLOSED, CaseState.FALSE_POSITIVE_CLOSED] else None

        # Determine next required role
        next_role = "analyst"
        if target_state == CaseState.SHOW_CAUSE_PENDING:
            next_role = "senior_investigator"
        elif target_state == CaseState.REPRESENTATION_WINDOW:
            next_role = "senior_investigator"
        elif target_state == CaseState.ORDER_PENDING:
            next_role = "compliance_officer"
        elif target_state == CaseState.CLASSIFIED:
            next_role = "compliance_officer"

        # Append-only audit record
        audit_entry = {
            "timestamp": now.isoformat(),
            "actor_id": req.actor_id,
            "actor_role": req.actor_role,
            "prior_state": curr_state.value,
            "new_state": target_state.value,
            "reason": req.reason,
            "notes": req.notes,
            "approval_token": req.approval_token
        }

        c["current_state"] = target_state.value
        c["updated_at"] = now.isoformat()
        c["deadline_at"] = new_deadline
        c["assigned_role_required"] = next_role
        c["audit_history"].append(audit_entry)

        # If transitioning to false positive, update impact ledger
        if target_state == CaseState.FALSE_POSITIVE_CLOSED:
            self.store.impact_records.append({
                "type": "FALSE_POSITIVE_COST",
                "amount": 250.0,
                "count": 1,
                "description": f"Analyst cleared false positive case {case_id}"
            })

        return self._format_case_response(c)

    def record_decision(self, case_id: str, req: CaseDecisionRequest) -> Dict[str, Any]:
        c = self.store.cases.get(case_id)
        if not c:
            raise KeyError(f"Case {case_id} not found")

        now = datetime.now(timezone.utc)
        decision_record = {
            "case_id": case_id,
            "decision_type": req.decision_type,
            "analyst_id": req.analyst_id,
            "rationale": req.rationale,
            "evidence_ids": req.evidence_ids,
            "timestamp": now.isoformat()
        }
        self.store.decision_logs.append(decision_record)

        # Auto transition if confirmed fraud
        if req.decision_type == "CONFIRMED_FRAUD":
            c["audit_history"].append({
                "timestamp": now.isoformat(),
                "actor_id": req.analyst_id,
                "actor_role": "compliance_officer",
                "prior_state": c["current_state"],
                "new_state": "classified",
                "reason": f"Confirmed fraud label finalized: {req.rationale}"
            })
            c["current_state"] = "classified"
            # Flag account as restricted/frozen in datastore
            acc = self.store.accounts.get(c["account_id"])
            if acc:
                acc["status"] = "RESTRICTED"

        return {"status": "SUCCESS", "decision": decision_record}

    def record_payment_outcome(self, req: PaymentOutcomeRequest) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        record = {
            "payment_id": req.payment_id,
            "outcome": req.outcome.value,
            "analyst_id": req.analyst_id,
            "notes": req.notes,
            "timestamp": now.isoformat()
        }
        self.store.payment_outcomes[req.payment_id] = record

        # Update matching transaction status
        txn = self.store.transactions.get(req.payment_id)
        if txn:
            if req.outcome.value == "HELD":
                txn["status"] = "HELD"
            elif req.outcome.value == "CANCELLED":
                txn["status"] = "CANCELLED"
            elif req.outcome.value in ["RELEASED", "PROCEEDED"]:
                txn["status"] = "COMPLETED"

        return {"status": "RECORDED", "record": record}

    def _generate_draft_document(self, account_id: str, txn_id: Optional[str]) -> Dict[str, Any]:
        acc = self.store.accounts.get(account_id, {})
        return {
            "document_type": "REGULATORY_INVESTIGATION_MEMORANDUM",
            "document_id": f"DOC-{uuid.uuid4().hex[:8].upper()}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_account": account_id,
            "target_label": acc.get("pseudonymous_label", account_id),
            "allegation": "Suspicious mule account behavior with rapid aggregation and dispersal indicators.",
            "statutory_reference": "Section 102 & FinCEN Advisory FIN-2023-A001 on Mule Networks",
            "statutory_timeline": "48 hours for representation from formal show-cause notification",
            "advisory_disclaimer": "Advisory schema-checked draft. Requires review and digital authorization by Compliance Officer before formal submission."
        }

    def _generate_evidence_summary(self, account_id: str) -> Dict[str, Any]:
        acc = self.store.accounts.get(account_id, {})
        return {
            "account_mule_score": acc.get("mule_score", 0.0),
            "account_type": acc.get("account_type", "UNKNOWN"),
            "velocity_in_24h": acc.get("velocity_in_24h", 0.0),
            "velocity_out_24h": acc.get("velocity_out_24h", 0.0),
            "status": acc.get("status", "ACTIVE"),
            "data_quality_provenance": "Bank internal payment core snapshot",
            "attribution_confidence": "HIGH"
        }

    def _format_case_response(self, c: Dict[str, Any]) -> CaseResponse:
        now = datetime.now(timezone.utc)
        deadline_str = c.get("deadline_at")
        time_rem = None
        is_overdue = False

        if deadline_str:
            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            delta = deadline - now
            time_rem = int(delta.total_seconds() / 60)
            is_overdue = time_rem < 0

        return CaseResponse(
            case_id=c["case_id"],
            account_id=c["account_id"],
            transaction_id=c.get("transaction_id"),
            current_state=CaseState(c["current_state"]),
            priority=c.get("priority", "HIGH"),
            created_at=c["created_at"],
            updated_at=c["updated_at"],
            deadline_at=deadline_str,
            time_remaining_minutes=time_rem,
            is_overdue=is_overdue,
            assigned_role_required=c.get("assigned_role_required", "analyst"),
            audit_history=c.get("audit_history", []),
            draft_document=c.get("draft_document"),
            evidence_summary=c.get("evidence_summary")
        )
