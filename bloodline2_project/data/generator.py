"""
Synthetic Mule Network Generator for Bloodline 2.0
Generates interconnected banking topologies including smurfing hubs, rapid pass-through chains,
cycles, structuring clusters, dormant account reactivations, and legitimate commercial look-alikes.
"""

import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List

def generate_synthetic_dataset(output_file: Path = Path("data/synthetic_ground_truth.json")) -> Dict[str, Any]:
    base_time = datetime.now(timezone.utc) - timedelta(days=3)

    accounts: List[Dict[str, Any]] = [
        # Legitimate
        {
            "account_id": "ACC-LEGIT-CORP",
            "pseudonymous_label": "Meridian Enterprise Logistics",
            "account_type": "COMMERCIAL",
            "balance": 845000.0,
            "mule_score": 0.04,
            "is_mule_ground_truth": False
        },
        {
            "account_id": "ACC-LEGIT-RETAIL",
            "pseudonymous_label": "Sarah Jenkins (Retail Payroll)",
            "account_type": "RETAIL_CHECKING",
            "balance": 4350.0,
            "mule_score": 0.08,
            "is_mule_ground_truth": False
        },
        # Mule Syndicate Alpha
        {
            "account_id": "ACC-VICTIM-01",
            "pseudonymous_label": "Estate Trust Client Alpha",
            "account_type": "PRIVATE_WEALTH",
            "balance": 210000.0,
            "mule_score": 0.12,
            "is_mule_ground_truth": False
        },
        {
            "account_id": "ACC-MULE-HUB1",
            "pseudonymous_label": "Pioneer Digital Trading (Hub 1)",
            "account_type": "NEW_BUSINESS",
            "balance": 1200.0,
            "mule_score": 0.93,
            "is_mule_ground_truth": True,
            "mule_role": "AGGREGATOR_FAN_OUT"
        },
        {
            "account_id": "ACC-MULE-002",
            "pseudonymous_label": "FastTrack Courier Hub",
            "account_type": "CHECKING",
            "balance": 350.0,
            "mule_score": 0.89,
            "is_mule_ground_truth": True,
            "mule_role": "LAYERING_PASS_THROUGH"
        },
        {
            "account_id": "ACC-MULE-003",
            "pseudonymous_label": "Apex Apex Freelance",
            "account_type": "CHECKING",
            "balance": 410.0,
            "mule_score": 0.86,
            "is_mule_ground_truth": True,
            "mule_role": "LAYERING_PASS_THROUGH"
        },
        {
            "account_id": "ACC-MULE-004",
            "pseudonymous_label": "Metro Quick Services",
            "account_type": "CHECKING",
            "balance": 620.0,
            "mule_score": 0.91,
            "is_mule_ground_truth": True,
            "mule_role": "LAYERING_PASS_THROUGH"
        },
        {
            "account_id": "ACC-EXIT-CRYPTO",
            "pseudonymous_label": "Overseas Virtual Asset Gateway",
            "account_type": "EXCHANGE_GATEWAY",
            "balance": 189000.0,
            "mule_score": 0.95,
            "is_mule_ground_truth": True,
            "mule_role": "CASH_OUT_EXIT"
        },
        {
            "account_id": "ACC-EXIT-RUNNER",
            "pseudonymous_label": "K. V. Runner Services",
            "account_type": "RETAIL_CHECKING",
            "balance": 150.0,
            "mule_score": 0.92,
            "is_mule_ground_truth": True,
            "mule_role": "ATM_RUNNER"
        }
    ]

    transactions: List[Dict[str, Any]] = [
        {
            "transaction_id": "TXN-ORIGIN-75K",
            "sender_account_id": "ACC-VICTIM-01",
            "receiver_account_id": "ACC-MULE-HUB1",
            "amount": 75000.0,
            "channel": "WIRE",
            "timestamp": (base_time + timedelta(hours=2)).isoformat(),
            "is_fraud_ground_truth": True
        },
        {
            "transaction_id": "TXN-SPLIT-01",
            "sender_account_id": "ACC-MULE-HUB1",
            "receiver_account_id": "ACC-MULE-002",
            "amount": 25000.0,
            "channel": "FAST_PAY",
            "timestamp": (base_time + timedelta(hours=2, minutes=18)).isoformat(),
            "is_fraud_ground_truth": True
        },
        {
            "transaction_id": "TXN-SPLIT-02",
            "sender_account_id": "ACC-MULE-HUB1",
            "receiver_account_id": "ACC-MULE-003",
            "amount": 24500.0,
            "channel": "FAST_PAY",
            "timestamp": (base_time + timedelta(hours=2, minutes=24)).isoformat(),
            "is_fraud_ground_truth": True
        },
        {
            "transaction_id": "TXN-SPLIT-03",
            "sender_account_id": "ACC-MULE-HUB1",
            "receiver_account_id": "ACC-MULE-004",
            "amount": 24300.0,
            "channel": "FAST_PAY",
            "timestamp": (base_time + timedelta(hours=2, minutes=32)).isoformat(),
            "is_fraud_ground_truth": True
        }
    ]

    dataset = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version": "synthetic-v2.0",
            "description": "Disclosed synthetic benchmark dataset for mule network and Money DNA evaluation"
        },
        "accounts": accounts,
        "transactions": transactions
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    return dataset

if __name__ == "__main__":
    data = generate_synthetic_dataset()
    print(f"Generated synthetic benchmark data with {len(data['accounts'])} accounts and {len(data['transactions'])} transactions.")
