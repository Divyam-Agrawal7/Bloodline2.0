#!/usr/bin/env python3
"""
Bloodline 2.0 - Dataset Reset & Replacement Tool
-------------------------------------------------
Wipes existing transactions/accounts and cleanly replaces them
with a new dataset, followed by automatic ML model retraining.

Usage:
  # 1. Completely clear all transaction data (leaves clean empty database)
  python scripts/reset_dataset.py --clear-only

  # 2. Clear existing data and import a new master CSV/spreadsheet
  python scripts/reset_dataset.py --file path/to/my_new_data.csv --retrain

  # 3. Restore the built-in synthetic demo dataset
  python scripts/reset_dataset.py --restore-demo --retrain
"""

import sys
import os
import shutil
import argparse
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

DB_PATH = ROOT_DIR / "data" / "bloodline.db"
BACKUP_DIR = ROOT_DIR / "data" / "backups"

CLEAN_SCHEMA_SQL = """
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS cases;
DROP TABLE IF EXISTS event_ledger;

CREATE TABLE accounts (
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

CREATE TABLE devices (
    account_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    ip TEXT NOT NULL,
    phone TEXT NOT NULL,
    PRIMARY KEY (account_id, device_id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    epoch_seconds INTEGER NOT NULL,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    amount REAL NOT NULL,
    channel TEXT NOT NULL,
    ref TEXT NOT NULL,
    origin_txn_id TEXT,
    sender_bank TEXT,
    receiver_bank TEXT,
    is_mule_flow INTEGER NOT NULL DEFAULT 0,
    chain_id TEXT,
    FOREIGN KEY (sender) REFERENCES accounts(id),
    FOREIGN KEY (receiver) REFERENCES accounts(id)
);

CREATE TABLE vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    account_id TEXT NOT NULL,
    bank_id TEXT NOT NULL,
    original_account_id TEXT NOT NULL,
    is_attacked INTEGER NOT NULL DEFAULT 0,
    attack_description TEXT
);

CREATE TABLE invoices (
    invoice_id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    vendor_name TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL,
    account_id TEXT NOT NULL,
    bank_id TEXT NOT NULL,
    flag_bank_detail_change INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE cases (
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

CREATE TABLE event_ledger (
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

CREATE INDEX IF NOT EXISTS idx_txn_sender ON transactions(sender);
CREATE INDEX IF NOT EXISTS idx_txn_receiver ON transactions(receiver);
CREATE INDEX IF NOT EXISTS idx_txn_ts ON transactions(epoch_seconds);
CREATE INDEX IF NOT EXISTS idx_txn_origin ON transactions(origin_txn_id);
CREATE INDEX IF NOT EXISTS idx_txn_chain ON transactions(chain_id);
CREATE INDEX IF NOT EXISTS idx_acc_chain ON accounts(chain_id);
CREATE INDEX IF NOT EXISTS idx_dev_acc ON devices(account_id);
"""

def backup_existing_db():
    """Create timestamped backup before wiping."""
    if DB_PATH.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_file = BACKUP_DIR / f"bloodline_{ts}.db"
        shutil.copy2(DB_PATH, bak_file)
        print(f"📦 Backup created: {bak_file}")

def clear_database():
    """Wipe all tables and vacuum SQLite database."""
    print("🧹 Clearing all existing transactions, accounts, and traces...")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(CLEAN_SCHEMA_SQL)
    conn.execute("VACUUM;")
    conn.commit()
    conn.close()
    print("✅ Database cleanly reset with fresh empty schema.")

def import_master_file(file_path: Path):
    """Import a new CSV/spreadsheet dataset."""
    print(f"📥 Ingesting new dataset from: {file_path}")
    from data.ingest_numbers_dataset import ingest_master_dataset
    ingest_master_dataset(csv_path=str(file_path), db_path=str(DB_PATH))

def retrain_models():
    """Re-train XGBoost, Isolation Forest, and SHAP explainer on new data."""
    print("\n🧠 Retraining AI Models on the new dataset...")
    from app.ml.train import train_and_evaluate
    metrics = train_and_evaluate()
    print(f"✅ AI Training Complete!")
    print(f"   • PR-AUC: {metrics['ml_model']['pr_auc']:.4f}")
    print(f"   • Precision: {metrics['ml_model']['precision']*100:.1f}%")
    print(f"   • Recall: {metrics['ml_model']['recall']*100:.1f}%")
    print(f"   • Metrics updated in: eval/metrics.json")

def print_summary():
    """Print current counts in database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    acc_count = c.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    mule_count = c.execute("SELECT COUNT(*) FROM accounts WHERE is_mule = 1").fetchone()[0]
    txn_count = c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    chains = [r[0] for r in c.execute("SELECT DISTINCT chain_id FROM transactions WHERE chain_id IS NOT NULL").fetchall()]
    conn.close()

    print("\n📊 Current Database Status:")
    print(f"   • Total Accounts: {acc_count:,}")
    print(f"   • Flagged Mules:  {mule_count:,}")
    print(f"   • Transactions:   {txn_count:,}")
    print(f"   • Active Chains:  {len(chains)} chains ({', '.join(chains[:6])}{'...' if len(chains) > 6 else ''})")

def main():
    parser = argparse.ArgumentParser(description="Reset or replace Bloodline 2.0 dataset")
    parser.add_argument("--clear-only", action="store_true", help="Only wipe database without importing new data")
    parser.add_argument("--file", type=str, help="Path to new dataset CSV file")
    parser.add_argument("--restore-demo", action="store_true", help="Restore built-in synthetic demo data")
    parser.add_argument("--retrain", action="store_true", default=True, help="Automatically retrain AI models after ingestion")
    parser.add_argument("--no-retrain", dest="retrain", action="store_false", help="Skip AI model retraining")

    args = parser.parse_args()

    print("================================================================================")
    print("                  BLOODLINE 2.0 — DATASET RESET & REPLACEMENT                   ")
    print("================================================================================")

    backup_existing_db()

    if args.clear_only:
        clear_database()
        print_summary()
        return

    if args.file:
        new_file = Path(args.file)
        if not new_file.exists():
            print(f"❌ Error: File not found: {new_file}")
            sys.exit(1)
        clear_database()
        import_master_file(new_file)
        if args.retrain:
            retrain_models()
        print_summary()
        return

    if args.restore_demo:
        clear_database()
        demo_csv = ROOT_DIR / "data" / "custom_input" / "bloodline_master.csv"
        if demo_csv.exists():
            import_master_file(demo_csv)
            if args.retrain:
                retrain_models()
        print_summary()
        return

    # If no flags provided, show help
    parser.print_help()

if __name__ == "__main__":
    main()
