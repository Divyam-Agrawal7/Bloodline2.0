import networkx as nx
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import threading

class BloodlineDatastore:
    _instance: Optional["BloodlineDatastore"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.entities: Dict[str, Dict[str, Any]] = {} # devices, IPs, phones
        self.cases: Dict[str, Dict[str, Any]] = {}
        self.audit_logs: List[Dict[str, Any]] = []
        self.decision_logs: List[Dict[str, Any]] = []
        self.payment_outcomes: Dict[str, Dict[str, Any]] = {}
        self.impact_records: List[Dict[str, Any]] = []
        self.vendor_registry: Dict[str, Dict[str, Any]] = {}

        # Temporal Heterogeneous Graph
        self.graph = nx.MultiDiGraph()
        self.seed_synthetic_data()

    @classmethod
    def get_instance(cls) -> "BloodlineDatastore":
        with cls._lock:
            if cls._instance is None:
                cls._instance = BloodlineDatastore()
            return cls._instance

    def reset(self):
        with self._lock:
            self.accounts.clear()
            self.transactions.clear()
            self.entities.clear()
            self.cases.clear()
            self.audit_logs.clear()
            self.decision_logs.clear()
            self.payment_outcomes.clear()
            self.impact_records.clear()
            self.vendor_registry.clear()
            self.graph.clear()
            self.seed_synthetic_data()

    def add_account(self, account_data: Dict[str, Any]):
        aid = account_data["account_id"]
        self.accounts[aid] = account_data
        self.graph.add_node(
            aid,
            label=account_data.get("pseudonymous_label", aid),
            type="account",
            risk_score=account_data.get("mule_score", 0.05),
            status=account_data.get("status", "ACTIVE"),
            metadata=account_data
        )

    def add_transaction(self, txn_data: Dict[str, Any]):
        tid = txn_data["transaction_id"]
        self.transactions[tid] = txn_data
        sender = txn_data["sender_account_id"]
        receiver = txn_data["receiver_account_id"]

        # Ensure sender and receiver exist in graph
        if sender not in self.graph:
            self.graph.add_node(sender, label=sender, type="account", risk_score=0.1, status="ACTIVE")
        if receiver not in self.graph:
            self.graph.add_node(receiver, label=receiver, type="account", risk_score=0.1, status="ACTIVE")

        self.graph.add_edge(
            sender,
            receiver,
            key=tid,
            id=tid,
            type="TRANSFERRED_TO",
            amount=txn_data["amount"],
            currency=txn_data.get("currency", "USD"),
            timestamp=txn_data["timestamp"].isoformat() if isinstance(txn_data["timestamp"], datetime) else str(txn_data["timestamp"]),
            channel=txn_data.get("channel", "FAST_PAY"),
            status=txn_data.get("status", "COMPLETED"),
            is_predicted=False
        )

    def add_shared_entity(self, entity_id: str, entity_type: str, linked_accounts: List[str]):
        self.entities[entity_id] = {
            "entity_id": entity_id,
            "type": entity_type,
            "linked_accounts": linked_accounts
        }
        self.graph.add_node(entity_id, label=entity_id, type=entity_type)
        edge_type = f"USED_{entity_type.upper()}"
        for acc in linked_accounts:
            if acc in self.graph:
                self.graph.add_edge(acc, entity_id, key=f"{acc}-{entity_id}", type=edge_type)

    def seed_synthetic_data(self):
        base_time = datetime.now(timezone.utc) - timedelta(days=2)

        # 1. Legitimate high-velocity commercial account
        self.add_account({
            "account_id": "ACC-LEGIT-CORP",
            "pseudonymous_label": "Meridian Enterprise Logistics",
            "account_type": "COMMERCIAL",
            "institution": "BankOne",
            "balance": 845000.0,
            "created_at": (base_time - timedelta(days=1200)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.04,
            "velocity_in_24h": 125000.0,
            "velocity_out_24h": 118000.0,
            "is_dormant_reactivated": False,
            "is_vendor": True,
            "customer_id": "CUST-CORP-01"
        })

        self.add_account({
            "account_id": "ACC-LEGIT-RETAIL",
            "pseudonymous_label": "Sarah Jenkins (Retail Payroll)",
            "account_type": "RETAIL_CHECKING",
            "institution": "BankOne",
            "balance": 4350.0,
            "created_at": (base_time - timedelta(days=800)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.08,
            "velocity_in_24h": 3200.0,
            "velocity_out_24h": 850.0,
            "is_dormant_reactivated": False,
            "is_vendor": False,
            "customer_id": "CUST-RETAIL-01"
        })

        # 2. Mule Syndicate Alpha (Smurfing, Rapid Pass-Through, Layering)
        # Origin victim
        self.add_account({
            "account_id": "ACC-VICTIM-01",
            "pseudonymous_label": "Estate Trust Client Alpha",
            "account_type": "PRIVATE_WEALTH",
            "institution": "BankOne",
            "balance": 210000.0,
            "created_at": (base_time - timedelta(days=950)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.12,
            "velocity_in_24h": 0.0,
            "velocity_out_24h": 75000.0,
            "is_dormant_reactivated": False,
            "customer_id": "CUST-VIC-01"
        })

        # Hop 1: Smurfing / Inbound Aggregator Mule
        self.add_account({
            "account_id": "ACC-MULE-HUB1",
            "pseudonymous_label": "Pioneer Digital Trading (Hub 1)",
            "account_type": "NEW_BUSINESS",
            "institution": "BankOne",
            "balance": 1200.0,
            "created_at": (base_time - timedelta(days=14)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.93,
            "velocity_in_24h": 75000.0,
            "velocity_out_24h": 73800.0,
            "is_dormant_reactivated": False,
            "customer_id": "CUST-MULE-HUB1"
        })

        # Hop 2: Layering Mule Accounts
        self.add_account({
            "account_id": "ACC-MULE-002",
            "pseudonymous_label": "FastTrack Courier Hub",
            "account_type": "CHECKING",
            "institution": "BankOne",
            "balance": 350.0,
            "created_at": (base_time - timedelta(days=21)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.89,
            "velocity_in_24h": 25000.0,
            "velocity_out_24h": 24800.0,
            "is_dormant_reactivated": False,
            "customer_id": "CUST-MULE-002"
        })

        self.add_account({
            "account_id": "ACC-MULE-003",
            "pseudonymous_label": "Apex Apex Freelance",
            "account_type": "CHECKING",
            "institution": "BankOne",
            "balance": 410.0,
            "created_at": (base_time - timedelta(days=18)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.86,
            "velocity_in_24h": 25000.0,
            "velocity_out_24h": 24500.0,
            "is_dormant_reactivated": False,
            "customer_id": "CUST-MULE-003"
        })

        self.add_account({
            "account_id": "ACC-MULE-004",
            "pseudonymous_label": "Metro Quick Services",
            "account_type": "CHECKING",
            "institution": "BankOne",
            "balance": 620.0,
            "created_at": (base_time - timedelta(days=35)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.91,
            "velocity_in_24h": 25000.0,
            "velocity_out_24h": 24500.0,
            "is_dormant_reactivated": False,
            "customer_id": "CUST-MULE-004"
        })

        # Hop 3: Exit Nodes (Off-ramp / ATM Runners)
        self.add_account({
            "account_id": "ACC-EXIT-CRYPTO",
            "pseudonymous_label": "Overseas Virtual Asset Gateway",
            "account_type": "EXCHANGE_GATEWAY",
            "institution": "BankOne",
            "balance": 189000.0,
            "created_at": (base_time - timedelta(days=60)).isoformat(),
            "status": "RESTRICTED",
            "mule_score": 0.95,
            "velocity_in_24h": 140000.0,
            "velocity_out_24h": 139000.0,
            "is_dormant_reactivated": False,
            "customer_id": "CUST-EXIT-CRYPTO"
        })

        self.add_account({
            "account_id": "ACC-EXIT-RUNNER",
            "pseudonymous_label": "K. V. Runner Services",
            "account_type": "RETAIL_CHECKING",
            "institution": "BankOne",
            "balance": 150.0,
            "created_at": (base_time - timedelta(days=12)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.92,
            "velocity_in_24h": 35000.0,
            "velocity_out_24h": 34900.0,
            "is_dormant_reactivated": False,
            "customer_id": "CUST-EXIT-RUNNER"
        })

        # 3. Mule Syndicate Beta (Structuring & Directed Cycles)
        self.add_account({
            "account_id": "ACC-RING-A",
            "pseudonymous_label": "Ring Node Alpha (Consulting)",
            "account_type": "BUSINESS",
            "institution": "BankOne",
            "balance": 45000.0,
            "created_at": (base_time - timedelta(days=90)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.88,
            "velocity_in_24h": 29000.0,
            "velocity_out_24h": 28500.0,
            "customer_id": "CUST-RING-A"
        })
        self.add_account({
            "account_id": "ACC-RING-B",
            "pseudonymous_label": "Ring Node Beta (Imports)",
            "account_type": "BUSINESS",
            "institution": "BankOne",
            "balance": 43000.0,
            "created_at": (base_time - timedelta(days=95)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.85,
            "velocity_in_24h": 29000.0,
            "velocity_out_24h": 28500.0,
            "customer_id": "CUST-RING-B"
        })
        self.add_account({
            "account_id": "ACC-RING-C",
            "pseudonymous_label": "Ring Node Gamma (Holding)",
            "account_type": "BUSINESS",
            "institution": "BankOne",
            "balance": 42000.0,
            "created_at": (base_time - timedelta(days=110)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.87,
            "velocity_in_24h": 29000.0,
            "velocity_out_24h": 28500.0,
            "customer_id": "CUST-RING-C"
        })

        # 4. Dormant Reactivation Account
        self.add_account({
            "account_id": "ACC-DORMANT-01",
            "pseudonymous_label": "Dormant Retail Account 91",
            "account_type": "SAVINGS",
            "institution": "BankOne",
            "balance": 45100.0,
            "created_at": (base_time - timedelta(days=730)).isoformat(),
            "status": "ACTIVE",
            "mule_score": 0.94,
            "velocity_in_24h": 45000.0,
            "velocity_out_24h": 44500.0,
            "is_dormant_reactivated": True,
            "customer_id": "CUST-DORM-01"
        })

        # Shared Entities (Device, IP, Phone)
        self.add_shared_entity("DEV-SYN-901", "device", ["ACC-MULE-HUB1", "ACC-MULE-002", "ACC-MULE-004"])
        self.add_shared_entity("IP-194.26.29.x", "ip", ["ACC-MULE-HUB1", "ACC-MULE-003", "ACC-EXIT-CRYPTO"])
        self.add_shared_entity("PHONE-+15550192", "phone", ["ACC-MULE-002", "ACC-EXIT-RUNNER"])
        self.add_shared_entity("DEV-RING-77", "device", ["ACC-RING-A", "ACC-RING-B", "ACC-RING-C"])

        # Honeypot marker node
        self.graph.add_node("HONEYPOT-TAG-01", label="High-Risk Flagged Sinkhole", type="honeypot")

        # 5. Transactions for Syndicate Alpha (Money DNA demonstration)
        # Origin Fraud Payment (Hop 0 -> Hop 1)
        t0 = base_time + timedelta(hours=2)
        self.add_transaction({
            "transaction_id": "TXN-ORIGIN-75K",
            "sender_account_id": "ACC-VICTIM-01",
            "receiver_account_id": "ACC-MULE-HUB1",
            "amount": 75000.0,
            "currency": "USD",
            "channel": "WIRE",
            "timestamp": t0,
            "status": "COMPLETED",
            "is_tainted": True
        })

        # Hop 1 -> Hop 2: Rapid Pass-Through Smurfing Splits (within 45 mins)
        t1_1 = t0 + timedelta(minutes=18)
        self.add_transaction({
            "transaction_id": "TXN-SPLIT-01",
            "sender_account_id": "ACC-MULE-HUB1",
            "receiver_account_id": "ACC-MULE-002",
            "amount": 25000.0,
            "currency": "USD",
            "channel": "FAST_PAY",
            "timestamp": t1_1,
            "status": "COMPLETED",
            "is_tainted": True
        })

        t1_2 = t0 + timedelta(minutes=24)
        self.add_transaction({
            "transaction_id": "TXN-SPLIT-02",
            "sender_account_id": "ACC-MULE-HUB1",
            "receiver_account_id": "ACC-MULE-003",
            "amount": 24500.0,
            "currency": "USD",
            "channel": "FAST_PAY",
            "timestamp": t1_2,
            "status": "COMPLETED",
            "is_tainted": True
        })

        t1_3 = t0 + timedelta(minutes=32)
        self.add_transaction({
            "transaction_id": "TXN-SPLIT-03",
            "sender_account_id": "ACC-MULE-HUB1",
            "receiver_account_id": "ACC-MULE-004",
            "amount": 24300.0,
            "currency": "USD",
            "channel": "FAST_PAY",
            "timestamp": t1_3,
            "status": "COMPLETED",
            "is_tainted": True
        })

        # Hop 2 -> Hop 3: Layering to Exit Nodes
        t2_1 = t1_1 + timedelta(minutes=40)
        self.add_transaction({
            "transaction_id": "TXN-EXIT-01",
            "sender_account_id": "ACC-MULE-002",
            "receiver_account_id": "ACC-EXIT-CRYPTO",
            "amount": 24800.0,
            "currency": "USD",
            "channel": "WIRE",
            "timestamp": t2_1,
            "status": "HELD", # Demonstrates hold action
            "is_tainted": True
        })

        t2_2 = t1_2 + timedelta(minutes=35)
        self.add_transaction({
            "transaction_id": "TXN-EXIT-02",
            "sender_account_id": "ACC-MULE-003",
            "receiver_account_id": "ACC-EXIT-RUNNER",
            "amount": 24100.0,
            "currency": "USD",
            "channel": "FAST_PAY",
            "timestamp": t2_2,
            "status": "COMPLETED",
            "is_tainted": True
        })

        # Syndicate Beta: Cycles and Structuring
        t_cycle = base_time + timedelta(hours=6)
        self.add_transaction({
            "transaction_id": "TXN-CYCLE-01",
            "sender_account_id": "ACC-RING-A",
            "receiver_account_id": "ACC-RING-B",
            "amount": 9500.0, # Structuring below $10k
            "currency": "USD",
            "channel": "WIRE",
            "timestamp": t_cycle,
            "status": "COMPLETED"
        })
        self.add_transaction({
            "transaction_id": "TXN-CYCLE-02",
            "sender_account_id": "ACC-RING-B",
            "receiver_account_id": "ACC-RING-C",
            "amount": 9450.0,
            "currency": "USD",
            "channel": "WIRE",
            "timestamp": t_cycle + timedelta(minutes=15),
            "status": "COMPLETED"
        })
        self.add_transaction({
            "transaction_id": "TXN-CYCLE-03",
            "sender_account_id": "ACC-RING-C",
            "receiver_account_id": "ACC-RING-A",
            "amount": 9400.0,
            "currency": "USD",
            "channel": "WIRE",
            "timestamp": t_cycle + timedelta(minutes=30),
            "status": "COMPLETED"
        })

        # Legitimate Payroll Transactions
        t_legit = base_time + timedelta(hours=8)
        self.add_transaction({
            "transaction_id": "TXN-PAYROLL-01",
            "sender_account_id": "ACC-LEGIT-CORP",
            "receiver_account_id": "ACC-LEGIT-RETAIL",
            "amount": 3200.0,
            "currency": "USD",
            "channel": "ACH",
            "timestamp": t_legit,
            "status": "COMPLETED"
        })

        # Vendor Registry for Business Shield Check
        self.vendor_registry["VEND-CORP-404"] = {
            "vendor_id": "VEND-CORP-404",
            "vendor_name": "Apex Facilities & Cloud Supplies Ltd",
            "verified_account_id": "ACC-LEGIT-CORP",
            "bank_details_updated_at": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(), # Updated 3 hours ago!
            "previous_account_id": "ACC-LEGIT-CORP",
            "current_account_id": "ACC-MULE-HUB1", # Swapped to mule account!
            "suspicious_divergence": True,
            "average_invoice_amount": 80000.0
        }

        # Seed Cases for the Case Clock demonstration
        self.create_seed_case()

        # Seed Baseline vs Bloodline Impact comparison data
        self.seed_impact_data()

    def create_seed_case(self):
        case_id = "CASE-2026-ALPHA-01"
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=48)
        self.cases[case_id] = {
            "case_id": case_id,
            "account_id": "ACC-MULE-HUB1",
            "transaction_id": "TXN-ORIGIN-75K",
            "current_state": "representation_window",
            "priority": "HIGH",
            "created_at": (now - timedelta(hours=14)).isoformat(),
            "updated_at": now.isoformat(),
            "deadline_at": deadline.isoformat(),
            "assigned_role_required": "senior_investigator",
            "audit_history": [
                {
                    "timestamp": (now - timedelta(hours=14)).isoformat(),
                    "actor_id": "analyst_sarah",
                    "actor_role": "analyst",
                    "prior_state": "None",
                    "new_state": "suspected",
                    "reason": "Automated high-velocity fan-out mule alert on TXN-ORIGIN-75K"
                },
                {
                    "timestamp": (now - timedelta(hours=12)).isoformat(),
                    "actor_id": "investigator_dan",
                    "actor_role": "senior_investigator",
                    "prior_state": "suspected",
                    "new_state": "show_cause_pending",
                    "reason": "Rapid pass-through confirmed with shared device DEV-SYN-901"
                },
                {
                    "timestamp": (now - timedelta(hours=6)).isoformat(),
                    "actor_id": "investigator_dan",
                    "actor_role": "senior_investigator",
                    "prior_state": "show_cause_pending",
                    "new_state": "representation_window",
                    "reason": "Show cause notice delivered to account holder. 48-hour response clock initiated."
                }
            ],
            "draft_document": {
                "document_type": "SUSPICIOUS_ACTIVITY_REPORT_DRAFT",
                "reference_no": "SAR-REF-2026-0081",
                "summary": "Account ACC-MULE-HUB1 acted as primary fan-out aggregator receiving $75,000 from compromised private wealth account ACC-VICTIM-01 and dispersing 98.4% within 32 minutes to three secondary mules sharing device DEV-SYN-901.",
                "legal_classification": "SUSPECTED_UNAUTHORIZED_MULE_AGGREGATION",
                "recommended_order": "PROVISIONAL_ASSET_FREEZE_SECTION_102"
            },
            "evidence_summary": {
                "total_inflow": 75000.0,
                "fan_out_degree": 3,
                "shared_devices": ["DEV-SYN-901"],
                "shared_ips": ["IP-194.26.29.x"],
                "pass_through_speed_mins": 18
            }
        }

    def seed_impact_data(self):
        # Comparison with documented Rule-Only Baseline
        self.impact_records = [
            {"type": "PREVENTED", "amount": 450000.0, "count": 18, "description": "Layered funds intercepted before crypto exit"},
            {"type": "AT_RISK", "amount": 98500.0, "count": 4, "description": "In cooling-off / active review status"},
            {"type": "LOST", "amount": 32000.0, "count": 2, "description": "Rapid cashout prior to behavioral trigger"},
            {"type": "FALSE_POSITIVE_COST", "amount": 2400.0, "count": 6, "description": "Friction on legitimate payroll delays"}
        ]
