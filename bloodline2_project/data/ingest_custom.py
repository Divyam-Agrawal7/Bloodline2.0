"""
Bloodline 2.0 - Custom Dataset Ingestion Utility

Allows users to import their own accounts, transactions, devices, vendors, and invoices
from CSV or JSON files into the SQLite database (`data/bloodline.db`).

Usage:
    python data/ingest_custom.py --dir data/custom_template/
    python data/ingest_custom.py --accounts my_accounts.csv --transactions my_txns.csv --retrain
"""

import os
import sys
import argparse
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    bank_id TEXT NOT NULL,
    open_date TEXT NOT NULL,
    kyc_tier TEXT NOT NULL,
    is_mule INTEGER NOT NULL,
    role TEXT NOT NULL,
    pseudonymous_label TEXT NOT NULL,
    initial_balance REAL NOT NULL,
    current_balance REAL NOT NULL,
    is_honeypot INTEGER NOT NULL DEFAULT 0,
    chain_id TEXT,
    layer INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS devices (
    account_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    ip TEXT NOT NULL,
    phone TEXT NOT NULL,
    PRIMARY KEY (account_id, device_id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    epoch_seconds INTEGER NOT NULL,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    amount REAL NOT NULL,
    channel TEXT NOT NULL,
    ref TEXT NOT NULL,
    origin_txn_id TEXT,
    sender_bank TEXT NOT NULL,
    receiver_bank TEXT NOT NULL,
    is_mule_flow INTEGER NOT NULL DEFAULT 0,
    chain_id TEXT,
    FOREIGN KEY (sender) REFERENCES accounts(id),
    FOREIGN KEY (receiver) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    account_id TEXT NOT NULL,
    bank_id TEXT NOT NULL,
    original_account_id TEXT NOT NULL,
    is_attacked INTEGER NOT NULL DEFAULT 0,
    attack_description TEXT
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL,
    account_id TEXT NOT NULL,
    bank_id TEXT NOT NULL,
    flag_bank_detail_change INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE IF NOT EXISTS event_ledger (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    txn_id TEXT,
    account_id TEXT,
    ts TEXT NOT NULL,
    action TEXT NOT NULL,
    verdict TEXT NOT NULL,
    mule_score REAL,
    threshold_version TEXT,
    reasons_json TEXT,
    counterfactual TEXT,
    analyst_note TEXT
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    created_ts TEXT NOT NULL,
    show_cause_deadline_days INTEGER DEFAULT 21,
    fmr_deadline_days INTEGER DEFAULT 14,
    elapsed_days INTEGER DEFAULT 0,
    evidence_json TEXT,
    llm_case_summary TEXT,
    show_cause_draft TEXT,
    human_approved INTEGER DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

DROP VIEW IF EXISTS ledger_bank_alpha;
DROP VIEW IF EXISTS ledger_bank_beta;
DROP VIEW IF EXISTS ledger_bank_gamma;

CREATE VIEW ledger_bank_alpha AS 
SELECT * FROM transactions WHERE sender_bank = 'BANK_ALPHA' OR receiver_bank = 'BANK_ALPHA';

CREATE VIEW ledger_bank_beta AS 
SELECT * FROM transactions WHERE sender_bank = 'BANK_BETA' OR receiver_bank = 'BANK_BETA';

CREATE VIEW ledger_bank_gamma AS 
SELECT * FROM transactions WHERE sender_bank = 'BANK_GAMMA' OR receiver_bank = 'BANK_GAMMA';

CREATE INDEX IF NOT EXISTS idx_txn_sender ON transactions(sender);
CREATE INDEX IF NOT EXISTS idx_txn_receiver ON transactions(receiver);
CREATE INDEX IF NOT EXISTS idx_txn_ts ON transactions(epoch_seconds);
CREATE INDEX IF NOT EXISTS idx_txn_origin ON transactions(origin_txn_id);
CREATE INDEX IF NOT EXISTS idx_dev_acc ON devices(account_id);
CREATE INDEX IF NOT EXISTS idx_dev_did ON devices(device_id);
CREATE INDEX IF NOT EXISTS idx_dev_ip ON devices(ip);
CREATE INDEX IF NOT EXISTS idx_dev_phone ON devices(phone);
"""

def load_table(path: Path) -> pd.DataFrame:
    if str(path).endswith(".csv"):
        return pd.read_csv(path)
    elif str(path).endswith(".json"):
        return pd.read_json(path)
    else:
        raise ValueError(f"Unsupported format: {path}")

def ingest_dataset(
    db_path: str = "data/bloodline.db",
    data_dir: Path = None,
    accounts_file: Path = None,
    transactions_file: Path = None,
    devices_file: Path = None,
    vendors_file: Path = None,
    invoices_file: Path = None,
    cases_file: Path = None,
    retrain: bool = False
):
    print("==========================================================")
    print("      BLOODLINE 2.0 — Custom Dataset Ingestion           ")
    print("==========================================================")

    if data_dir and data_dir.exists():
        if not accounts_file and (data_dir / "accounts.csv").exists():
            accounts_file = data_dir / "accounts.csv"
        elif not accounts_file and (data_dir / "accounts.json").exists():
            accounts_file = data_dir / "accounts.json"

        if not transactions_file and (data_dir / "transactions.csv").exists():
            transactions_file = data_dir / "transactions.csv"
        elif not transactions_file and (data_dir / "transactions.json").exists():
            transactions_file = data_dir / "transactions.json"

        if not devices_file and (data_dir / "devices.csv").exists():
            devices_file = data_dir / "devices.csv"
        if not vendors_file and (data_dir / "vendors.csv").exists():
            vendors_file = data_dir / "vendors.csv"
        if not invoices_file and (data_dir / "invoices.csv").exists():
            invoices_file = data_dir / "invoices.csv"
        if not cases_file and (data_dir / "cases.csv").exists():
            cases_file = data_dir / "cases.csv"

    # Backup existing database if present
    if os.path.exists(db_path):
        backup_path = f"{db_path}.bak"
        print(f"[Backup] Preserving existing database to {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.executescript(DB_SCHEMA)

    # 1. Accounts
    if accounts_file and accounts_file.exists():
        df_acc = load_table(accounts_file)
        # Fill defaults
        if "bank_id" not in df_acc.columns:
            df_acc["bank_id"] = "BANK_ALPHA"
        if "open_date" not in df_acc.columns:
            df_acc["open_date"] = "2025-01-01"
        if "kyc_tier" not in df_acc.columns:
            df_acc["kyc_tier"] = "TIER_2"
        if "is_mule" not in df_acc.columns:
            df_acc["is_mule"] = 0
        if "role" not in df_acc.columns:
            df_acc["role"] = "LEGIT_RETAIL"
        if "pseudonymous_label" not in df_acc.columns:
            df_acc["pseudonymous_label"] = df_acc["id"]
        if "initial_balance" not in df_acc.columns:
            df_acc["initial_balance"] = 50000.0
        if "current_balance" not in df_acc.columns:
            df_acc["current_balance"] = df_acc["initial_balance"]
        if "is_honeypot" not in df_acc.columns:
            df_acc["is_honeypot"] = 0

        df_acc.to_sql("accounts", conn, if_exists="append", index=False)
        print(f"✓ Ingested {len(df_acc)} accounts from {accounts_file.name}")
    else:
        print("⚠️ No accounts file provided.")

    # 2. Devices
    if devices_file and devices_file.exists():
        df_dev = load_table(devices_file)
        df_dev.to_sql("devices", conn, if_exists="append", index=False)
        print(f"✓ Ingested {len(df_dev)} device associations from {devices_file.name}")
    else:
        # Auto-generate synthetic 1-to-1 device mappings if none provided
        if accounts_file and accounts_file.exists():
            df_acc = load_table(accounts_file)
            dev_rows = [
                {"account_id": aid, "device_id": f"DEV-{aid}", "ip": "10.0.0.1", "phone": "+91-9876500000"}
                for aid in df_acc["id"]
            ]
            pd.DataFrame(dev_rows).to_sql("devices", conn, if_exists="append", index=False)
            print(f"✓ Auto-generated default device records for {len(dev_rows)} accounts")

    # 3. Transactions
    if transactions_file and transactions_file.exists():
        df_tx = load_table(transactions_file)
        if "epoch_seconds" not in df_tx.columns and "ts" in df_tx.columns:
            df_tx["epoch_seconds"] = pd.to_datetime(df_tx["ts"]).astype("int64") // 10**9
        elif "ts" not in df_tx.columns and "epoch_seconds" in df_tx.columns:
            df_tx["ts"] = pd.to_datetime(df_tx["epoch_seconds"], unit="s").dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        if "channel" not in df_tx.columns:
            df_tx["channel"] = "UPI"
        if "ref" not in df_tx.columns:
            df_tx["ref"] = "REF-CUSTOM-" + df_tx["id"].astype(str)
        if "sender_bank" not in df_tx.columns:
            df_tx["sender_bank"] = "BANK_ALPHA"
        if "receiver_bank" not in df_tx.columns:
            df_tx["receiver_bank"] = "BANK_ALPHA"
        if "is_mule_flow" not in df_tx.columns:
            df_tx["is_mule_flow"] = 0

        df_tx.to_sql("transactions", conn, if_exists="append", index=False)
        print(f"✓ Ingested {len(df_tx)} transactions from {transactions_file.name}")
    else:
        print("⚠️ No transactions file provided.")

    # 4. Vendors & Invoices (Optional)
    if vendors_file and vendors_file.exists():
        df_v = load_table(vendors_file)
        df_v.to_sql("vendors", conn, if_exists="append", index=False)
        print(f"✓ Ingested {len(df_v)} vendors from {vendors_file.name}")

    if invoices_file and invoices_file.exists():
        df_inv = load_table(invoices_file)
        df_inv.to_sql("invoices", conn, if_exists="append", index=False)
        print(f"✓ Ingested {len(df_inv)} invoices from {invoices_file.name}")

    # 5. Cases (Optional)
    if cases_file and cases_file.exists():
        df_cases = load_table(cases_file)
        df_cases.to_sql("cases", conn, if_exists="append", index=False)
        print(f"✓ Ingested {len(df_cases)} cases from {cases_file.name}")

    conn.commit()
    conn.close()
    print("\n✅ Ingestion complete! Database successfully refreshed at:", db_path)

    if retrain:
        print("\n[ML Retraining] Re-extracting point-in-time features & retraining XGBoost...")
        from app.ml.train import train_and_evaluate
        metrics = train_and_evaluate(db_path=db_path)
        print(f"✓ ML Retraining complete! PR-AUC: {metrics['ml_model']['pr_auc']:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest custom datasets into Bloodline 2.0")
    parser.add_argument("--dir", type=str, help="Directory containing accounts.csv, transactions.csv, etc.")
    parser.add_argument("--accounts", type=str, help="Path to accounts CSV/JSON")
    parser.add_argument("--transactions", type=str, help="Path to transactions CSV/JSON")
    parser.add_argument("--devices", type=str, help="Path to devices CSV/JSON")
    parser.add_argument("--vendors", type=str, help="Path to vendors CSV/JSON")
    parser.add_argument("--invoices", type=str, help="Path to invoices CSV/JSON")
    parser.add_argument("--cases", type=str, help="Path to cases CSV/JSON")
    parser.add_argument("--db", type=str, default="data/bloodline.db", help="Target SQLite database path")
    parser.add_argument("--retrain", action="store_true", help="Retrain ML models on the newly ingested data")

    args = parser.parse_args()

    data_dir = Path(args.dir) if args.dir else None
    acc_path = Path(args.accounts) if args.accounts else None
    tx_path = Path(args.transactions) if args.transactions else None
    dev_path = Path(args.devices) if args.devices else None
    ven_path = Path(args.vendors) if args.vendors else None
    inv_path = Path(args.invoices) if args.invoices else None
    cas_path = Path(args.cases) if args.cases else None

    ingest_dataset(
        db_path=args.db,
        data_dir=data_dir,
        accounts_file=acc_path,
        transactions_file=tx_path,
        devices_file=dev_path,
        vendors_file=ven_path,
        invoices_file=inv_path,
        cases_file=cas_path,
        retrain=args.retrain
    )
