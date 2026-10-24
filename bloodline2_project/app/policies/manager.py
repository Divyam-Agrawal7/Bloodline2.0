import json
from pathlib import Path
from typing import Dict, Any, Optional

POLICY_FILE = Path(__file__).parent / "policy_v1.json"

class PolicyManager:
    _instance: Optional["PolicyManager"] = None

    def __init__(self, policy_path: Path = POLICY_FILE):
        self.policy_path = policy_path
        self._policy = self._load_policy()
        self._threshold_history = []

    def _load_policy(self) -> Dict[str, Any]:
        with open(self.policy_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def get_instance(cls) -> "PolicyManager":
        if cls._instance is None:
            cls._instance = PolicyManager()
        return cls._instance

    @property
    def version(self) -> str:
        return self._policy.get("policy_version", "synthetic-demo-v1")

    @property
    def thresholds(self) -> Dict[str, Any]:
        return self._policy.get("decision_thresholds", {})

    @property
    def case_clock_config(self) -> Dict[str, Any]:
        return self._policy.get("case_clock", {})

    def evaluate_score_action(self, risk_score: float) -> str:
        t = self.thresholds
        hold_min = t.get("hold_freeze_min", 0.88)
        delay_min = t.get("delay_review_min", 0.70)
        review_min = t.get("review_min", 0.40)

        if risk_score >= hold_min:
            return "HOLD_FREEZE"
        elif risk_score >= delay_min:
            return "DELAY_REVIEW"
        elif risk_score >= review_min:
            return "REVIEW"
        else:
            return "ALLOW"

    def adjust_threshold(self, key: str, new_value: float, actor: str, reason: str) -> Dict[str, Any]:
        limits = self.thresholds.get("bounded_limits", {"min_allowable": 0.50, "max_allowable": 0.95})
        min_lim = limits.get("min_allowable", 0.50)
        max_lim = limits.get("max_allowable", 0.95)

        if not (min_lim <= new_value <= max_lim):
            raise ValueError(f"Value {new_value} is outside bounded threshold guardrail [{min_lim}, {max_lim}]")

        old_value = self.thresholds.get(key)
        self._policy["decision_thresholds"][key] = round(new_value, 3)

        change_record = {
            "key": key,
            "old_value": old_value,
            "new_value": round(new_value, 3),
            "actor": actor,
            "reason": reason,
            "version": self.version
        }
        self._threshold_history.append(change_record)
        return change_record

    def get_threshold_history(self):
        return self._threshold_history
