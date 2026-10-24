"""
Bloodline 2.0 - Synthetic Banking Network Simulator (Phase 1)
Generates 3 banks, ~5,000 accounts, ~150,000 transactions, ~60 mules, 3 honeypots,
devices/IPs/phones, vendors, and planted mule chains + legitimate look-alikes.
Fixed random seed = 42.
"""

import sqlite3
import random
import datetime
import math
from pathlib import Path
from typing import Dict, List, Tuple, Any

SEED = 42
BANKS = ["BANK_ALPHA", "BANK_BETA", "BANK_GAMMA"]
KYC_TIERS = ["TIER_1_BASIC", "TIER_2_SIMPLIFIED", "TIER_3_FULL"]
CHANNELS = ["UPI", "IMPS", "NEFT", "RTGS"]

FIRST_NAMES = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Deepak", "Divya", "Gaurav", "Isha",
    "Kavita", "Manish", "Neha", "Pooja", "Rahul", "Rohan", "Sanjay", "Shreya", "Sneha",
    "Sunil", "Tanvi", "Varun", "Vikas", "Priya", "Rajesh", "Kiran", "Meera", "Vikram",
    "Nikhil", "Ritu", "Alok", "Anil", "Bhavna", "Chetan", "Kunal", "Preeti", "Suresh"
]
LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Shah", "Joshi", "Mehta",
    "Reddy", "Nair", "Bose", "Chawla", "Deshmukh", "Iyer", "Kulkarni", "Malhotra", "Pandey",
    "Rao", "Saxena", "Sen", "Trivedi", "Agrawal", "Bansal", "Chopra", "Dutta", "Kapoor"
]
SHOP_TYPES = ["Kirana", "Electronics", "Stationery", "Pharma", "Textiles", "Auto Spares", "Hardware", "Cafe"]
CORP_NAMES = ["Tata", "Reliance", "Infosys", "Wipro", "HCL", "Mahindra", "Adani", "L&T", "Godrej", "Bajaj"]

def generate_database(db_path: Path = Path("data/bloodline.db"), force: bool = True) -> Dict[str, Any]:
    if db_path.exists() and force:
        db_path.unlink()
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
    PRAGMA journal_mode = WAL;
    PRAGMA synchronous = NORMAL;

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
        sender_bank TEXT NOT NULL,
        receiver_bank TEXT NOT NULL,
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
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        account_id TEXT NOT NULL,
        bank_id TEXT NOT NULL,
        flag_bank_detail_change INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
        FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
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

    -- Multi-bank partition views/tables
    CREATE VIEW ledger_bank_alpha AS 
    SELECT * FROM transactions WHERE sender_bank = 'BANK_ALPHA' OR receiver_bank = 'BANK_ALPHA';

    CREATE VIEW ledger_bank_beta AS 
    SELECT * FROM transactions WHERE sender_bank = 'BANK_BETA' OR receiver_bank = 'BANK_BETA';

    CREATE VIEW ledger_bank_gamma AS 
    SELECT * FROM transactions WHERE sender_bank = 'BANK_GAMMA' OR receiver_bank = 'BANK_GAMMA';

    CREATE INDEX idx_txn_sender ON transactions(sender);
    CREATE INDEX idx_txn_receiver ON transactions(receiver);
    CREATE INDEX idx_txn_ts ON transactions(epoch_seconds);
    CREATE INDEX idx_txn_origin ON transactions(origin_txn_id);
    CREATE INDEX idx_dev_acc ON devices(account_id);
    CREATE INDEX idx_dev_did ON devices(device_id);
    CREATE INDEX idx_dev_ip ON devices(ip);
    CREATE INDEX idx_dev_phone ON devices(phone);
    """)

    rng = random.Random(SEED)
    now = datetime.datetime(2026, 10, 23, 18, 0, 0, tzinfo=datetime.timezone.utc)
    base_epoch = int(now.timestamp())
    sim_days = 30
    start_epoch = base_epoch - (sim_days * 86400)

    # 1. Generate Accounts (~5,000)
    accounts = []
    account_lookup = {}
    total_target_accounts = 5000
    
    # 3 Honeypots
    honeypots = [
        {
            "id": "ACC-HONEYPOT-01",
            "bank_id": "BANK_ALPHA",
            "open_date": (now - datetime.timedelta(days=400)).strftime("%Y-%m-%d"),
            "kyc_tier": "TIER_3_FULL",
            "is_mule": 1,
            "role": "HONEYPOT",
            "pseudonymous_label": "LEA Monitored Decoy Alpha",
            "initial_balance": 150000.0,
            "current_balance": 150000.0,
            "is_honeypot": 1,
            "chain_id": None,
            "layer": 0
        },
        {
            "id": "ACC-HONEYPOT-02",
            "bank_id": "BANK_BETA",
            "open_date": (now - datetime.timedelta(days=350)).strftime("%Y-%m-%d"),
            "kyc_tier": "TIER_3_FULL",
            "is_mule": 1,
            "role": "HONEYPOT",
            "pseudonymous_label": "LEA Cyber Decoy Beta",
            "initial_balance": 200000.0,
            "current_balance": 200000.0,
            "is_honeypot": 1,
            "chain_id": None,
            "layer": 0
        },
        {
            "id": "ACC-HONEYPOT-03",
            "bank_id": "BANK_GAMMA",
            "open_date": (now - datetime.timedelta(days=280)).strftime("%Y-%m-%d"),
            "kyc_tier": "TIER_3_FULL",
            "is_mule": 1,
            "role": "HONEYPOT",
            "pseudonymous_label": "Inter-Bank Decoy Gamma",
            "initial_balance": 180000.0,
            "current_balance": 180000.0,
            "is_honeypot": 1,
            "chain_id": None,
            "layer": 0
        }
    ]
    accounts.extend(honeypots)

    # Mule Chains: 8 chains (Chains 1-7 fast hops, Chain 8 slow hops holdout)
    # Each chain: 1 victim, 3-4 Layer-1 mules, 3-4 Layer-2 mules, 1-2 Cash-out accounts
    mule_accounts = []
    chains_meta = []
    
    for c_idx in range(1, 9):
        chain_id = f"CHAIN-{c_idx:02d}"
        is_holdout = (c_idx == 8) # Chain 8 is the slow hops holdout test
        
        # Victim
        vic_bank = BANKS[(c_idx - 1) % 3]
        vic_id = f"ACC-VIC-{c_idx:02d}"
        vic_acc = {
            "id": vic_id,
            "bank_id": vic_bank,
            "open_date": (now - datetime.timedelta(days=rng.randint(300, 1200))).strftime("%Y-%m-%d"),
            "kyc_tier": "TIER_3_FULL",
            "is_mule": 0,
            "role": "VICTIM",
            "pseudonymous_label": f"Victim Corp / Trust {c_idx:02d}",
            "initial_balance": rng.uniform(2500000.0, 6000000.0),
            "current_balance": rng.uniform(2500000.0, 6000000.0),
            "is_honeypot": 0,
            "chain_id": chain_id,
            "layer": 0
        }
        accounts.append(vic_acc)

        # Layer 1 mules (3-4)
        l1_mules = []
        num_l1 = 4 if c_idx % 2 == 0 else 3
        for l1_idx in range(1, num_l1 + 1):
            m_bank = BANKS[(c_idx + l1_idx) % 3]
            m_id = f"ACC-MULE-C{c_idx}-L1-{l1_idx}"
            # Some dormant accounts reactivated
            is_dormant = (c_idx in [2, 5] and l1_idx == 1)
            open_age = rng.randint(450, 900) if is_dormant else rng.randint(3, 35)
            
            m_acc = {
                "id": m_id,
                "bank_id": m_bank,
                "open_date": (now - datetime.timedelta(days=open_age)).strftime("%Y-%m-%d"),
                "kyc_tier": "TIER_1_BASIC" if not is_dormant else "TIER_2_SIMPLIFIED",
                "is_mule": 1,
                "role": "MULE_LAYER1",
                "pseudonymous_label": f"Aggr Partner {c_idx}-{l1_idx}" + (" (Reactivated)" if is_dormant else ""),
                "initial_balance": rng.uniform(500.0, 3000.0),
                "current_balance": rng.uniform(500.0, 3000.0),
                "is_honeypot": 0,
                "chain_id": chain_id,
                "layer": 1
            }
            accounts.append(m_acc)
            l1_mules.append(m_acc)
            mule_accounts.append(m_acc)

        # Layer 2 mules (3-4)
        l2_mules = []
        num_l2 = 3
        for l2_idx in range(1, num_l2 + 1):
            m_bank = BANKS[(c_idx + l2_idx + 1) % 3]
            m_id = f"ACC-MULE-C{c_idx}-L2-{l2_idx}"
            open_age = rng.randint(5, 45)
            m_acc = {
                "id": m_id,
                "bank_id": m_bank,
                "open_date": (now - datetime.timedelta(days=open_age)).strftime("%Y-%m-%d"),
                "kyc_tier": "TIER_1_BASIC",
                "is_mule": 1,
                "role": "MULE_LAYER2",
                "pseudonymous_label": f"Dispersal Layer {c_idx}-{l2_idx}",
                "initial_balance": rng.uniform(200.0, 1500.0),
                "current_balance": rng.uniform(200.0, 1500.0),
                "is_honeypot": 0,
                "chain_id": chain_id,
                "layer": 2
            }
            accounts.append(m_acc)
            l2_mules.append(m_acc)
            mule_accounts.append(m_acc)

        # Cash-out exits (1-2)
        exit_mules = []
        num_exit = 2 if c_idx in [1, 3, 7] else 1
        for ex_idx in range(1, num_exit + 1):
            m_bank = BANKS[(c_idx + ex_idx + 2) % 3]
            m_id = f"ACC-EXIT-C{c_idx}-{ex_idx}"
            m_acc = {
                "id": m_id,
                "bank_id": m_bank,
                "open_date": (now - datetime.timedelta(days=rng.randint(15, 60))).strftime("%Y-%m-%d"),
                "kyc_tier": "TIER_2_SIMPLIFIED",
                "is_mule": 1,
                "role": "MULE_CASHOUT",
                "pseudonymous_label": f"Crypto/Bullion Cashout {c_idx}-{ex_idx}",
                "initial_balance": rng.uniform(1000.0, 50000.0),
                "current_balance": rng.uniform(1000.0, 50000.0),
                "is_honeypot": 0,
                "chain_id": chain_id,
                "layer": 3
            }
            accounts.append(m_acc)
            exit_mules.append(m_acc)
            mule_accounts.append(m_acc)

        chains_meta.append({
            "chain_id": chain_id,
            "victim": vic_acc,
            "l1": l1_mules,
            "l2": l2_mules,
            "exits": exit_mules,
            "is_holdout": is_holdout
        })

    # Legitimate Look-alikes:
    # 1. Busy Shopkeepers (high fan-in: 150 accounts)
    shopkeeper_accounts = []
    for s_idx in range(1, 151):
        bank = rng.choice(BANKS)
        shop_name = f"{rng.choice(LAST_NAMES)} {rng.choice(SHOP_TYPES)}"
        s_acc = {
            "id": f"ACC-SHOP-{s_idx:04d}",
            "bank_id": bank,
            "open_date": (now - datetime.timedelta(days=rng.randint(180, 1800))).strftime("%Y-%m-%d"),
            "kyc_tier": "TIER_3_FULL",
            "is_mule": 0,
            "role": "LEGIT_SHOPKEEPER",
            "pseudonymous_label": f"{shop_name} (Merchant)",
            "initial_balance": rng.uniform(45000.0, 350000.0),
            "current_balance": rng.uniform(45000.0, 350000.0),
            "is_honeypot": 0,
            "chain_id": None,
            "layer": 0
        }
        accounts.append(s_acc)
        shopkeeper_accounts.append(s_acc)

    # 2. Corporate Payroll (high fan-out: 30 accounts)
    payroll_accounts = []
    for p_idx in range(1, 31):
        bank = rng.choice(BANKS)
        corp = f"{rng.choice(CORP_NAMES)} Enterprises"
        p_acc = {
            "id": f"ACC-PAYROLL-{p_idx:03d}",
            "bank_id": bank,
            "open_date": (now - datetime.timedelta(days=rng.randint(365, 2500))).strftime("%Y-%m-%d"),
            "kyc_tier": "TIER_3_FULL",
            "is_mule": 0,
            "role": "LEGIT_PAYROLL",
            "pseudonymous_label": f"{corp} Payroll Disbursal",
            "initial_balance": rng.uniform(5000000.0, 35000000.0),
            "current_balance": rng.uniform(5000000.0, 35000000.0),
            "is_honeypot": 0,
            "chain_id": None,
            "layer": 0
        }
        accounts.append(p_acc)
        payroll_accounts.append(p_acc)

    # 3. Genuine New Accounts (recent open date, normal behavior: 300 accounts)
    new_legit_accounts = []
    for n_idx in range(1, 301):
        bank = rng.choice(BANKS)
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        n_acc = {
            "id": f"ACC-NEW-{n_idx:04d}",
            "bank_id": bank,
            "open_date": (now - datetime.timedelta(days=rng.randint(2, 30))).strftime("%Y-%m-%d"),
            "kyc_tier": rng.choice(["TIER_2_SIMPLIFIED", "TIER_3_FULL"]),
            "is_mule": 0,
            "role": "LEGIT_NEW_RETAIL",
            "pseudonymous_label": f"{name} (New User)",
            "initial_balance": rng.uniform(2000.0, 45000.0),
            "current_balance": rng.uniform(2000.0, 45000.0),
            "is_honeypot": 0,
            "chain_id": None,
            "layer": 0
        }
        accounts.append(n_acc)
        new_legit_accounts.append(n_acc)

    # Remainder: Regular Retail & Commercial Accounts to reach 5,000
    current_acc_count = len(accounts)
    remaining_count = total_target_accounts - current_acc_count
    regular_accounts = []
    for r_idx in range(1, remaining_count + 1):
        bank = rng.choice(BANKS)
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        r_acc = {
            "id": f"ACC-REG-{r_idx:05d}",
            "bank_id": bank,
            "open_date": (now - datetime.timedelta(days=rng.randint(35, 2000))).strftime("%Y-%m-%d"),
            "kyc_tier": rng.choice(["TIER_2_SIMPLIFIED", "TIER_3_FULL", "TIER_3_FULL"]),
            "is_mule": 0,
            "role": "LEGIT_RETAIL",
            "pseudonymous_label": name,
            "initial_balance": rng.uniform(5000.0, 250000.0),
            "current_balance": rng.uniform(5000.0, 250000.0),
            "is_honeypot": 0,
            "chain_id": None,
            "layer": 0
        }
        accounts.append(r_acc)
        regular_accounts.append(r_acc)

    for a in accounts:
        account_lookup[a["id"]] = a

    # 2. Devices, IPs, and Phones
    # Mules share device clusters, IPs, and phones!
    devices = []
    # Mule shared cluster 1: Chains 1, 2, 3 share devices/IPs
    # Mule shared cluster 2: Chains 4, 5, 6 share devices/IPs
    shared_device_pool = [f"DEV-MULE-CLUSTER-{i:02d}" for i in range(1, 7)]
    shared_ip_pool = [f"198.51.100.{10 + i}" for i in range(1, 10)]
    shared_phone_pool = [f"+91 98200 {11000 + i}" for i in range(1, 8)]

    for a in accounts:
        a_id = a["id"]
        is_mule = a["is_mule"] == 1 and a["role"].startswith("MULE")
        
        if is_mule:
            # High probability of shared device/ip/phone
            c_num = int(a["chain_id"].split("-")[1]) if a.get("chain_id") else 1
            cluster_id = 0 if c_num <= 3 else (1 if c_num <= 6 else 2)
            d_id = shared_device_pool[cluster_id]
            ip_val = shared_ip_pool[cluster_id * 2 + (c_num % 2)]
            phone_val = shared_phone_pool[cluster_id * 2]
            devices.append((a_id, d_id, ip_val, phone_val))
            # 30% have a second device in the cluster
            if rng.random() < 0.35:
                devices.append((a_id, f"{d_id}-ALT", ip_val, phone_val))
        else:
            # Clean unique or occasionally shared devices (family/store tablet sharing)
            if rng.random() < 0.08:
                # 8% of legit accounts share a device or IP with another legit account
                shared_idx = rng.randint(1, 20)
                d_id = f"DEV-SHARED-RETAIL-{shared_idx:02d}"
                ip_val = f"103.21.{shared_idx}.100"
                phone_val = f"+91 98111 {shared_idx:04d}"
            else:
                d_id = f"DEV-USR-{rng.randint(100000, 999999)}"
                ip_val = f"103.{rng.randint(10, 240)}.{rng.randint(1, 254)}.{rng.randint(1, 254)}"
                phone_val = f"+91 {rng.choice([98, 99, 97, 96, 91])}{rng.randint(10000000, 99999999)}"
            devices.append((a_id, d_id, ip_val, phone_val))

    # 3. Generate Transactions (~150,000)
    transactions = []
    txn_counter = 1

    # A. Mule Chain Transactions (Planted multi-hop flow)
    for c in chains_meta:
        chain_id = c["chain_id"]
        vic = c["victim"]
        l1s = c["l1"]
        l2s = c["l2"]
        exits = c["exits"]
        is_holdout = c["is_holdout"]

        # Timestamp for the incident: occurred between day 2 and day 28
        incident_day_offset = rng.randint(4, 26)
        chain_start_epoch = start_epoch + (incident_day_offset * 86400) + rng.randint(3600, 20000)
        
        # Stolen victim sum: ₹1,500,000 to ₹4,500,000
        victim_amount = float(rng.choice([1500000, 2100000, 2800000, 3600000, 4200000]))
        origin_ref = f"ORIGIN-MULE-{chain_id}"
        
        # Hop 0 -> Hop 1: Fan-out from Victim to Layer 1 Mules
        l1_chunk = victim_amount / len(l1s)
        current_epoch = chain_start_epoch
        l1_inbounds = {}

        for l1 in l1s:
            # Structuring/smurfing into multiple sub-payments or clean large tranche
            num_tranches = rng.choice([2, 3, 4])
            tranche_amt = math.floor(l1_chunk / num_tranches)
            l1_inbounds[l1["id"]] = []

            for tr in range(num_tranches):
                hop_sec = rng.randint(30, 180) if not is_holdout else rng.randint(3600, 14400)
                current_epoch += hop_sec
                txn_id = f"TXN-C{chain_id[-2:]}-HOP1-{txn_counter:06d}"
                txn_counter += 1
                
                # Surcharge / fee haircut (slight noise)
                amt = float(tranche_amt + rng.choice([-100, 0, 100, 500]))
                l1_inbounds[l1["id"]].append(amt)
                
                transactions.append((
                    txn_id,
                    datetime.datetime.fromtimestamp(current_epoch, tz=datetime.timezone.utc).isoformat(),
                    current_epoch,
                    vic["id"],
                    l1["id"],
                    amt,
                    "IMPS" if amt < 500000 else "RTGS",
                    origin_ref,
                    origin_ref,
                    vic["bank_id"],
                    l1["bank_id"],
                    1,
                    chain_id
                ))

        # Circular wash loop in Chain 2 & Chain 6 before Layer 2
        if chain_id in ["CHAIN-02", "CHAIN-06"] and len(l1s) >= 3:
            loop_amt = 95000.0
            t_loop1 = f"TXN-LOOP1-{txn_counter:06d}"
            txn_counter += 1
            current_epoch += 90
            transactions.append((
                t_loop1,
                datetime.datetime.fromtimestamp(current_epoch, tz=datetime.timezone.utc).isoformat(),
                current_epoch,
                l1s[0]["id"], l1s[1]["id"], loop_amt, "UPI", f"LOOP-A-{chain_id}", origin_ref,
                l1s[0]["bank_id"], l1s[1]["bank_id"], 1, chain_id
            ))
            t_loop2 = f"TXN-LOOP2-{txn_counter:06d}"
            txn_counter += 1
            current_epoch += 80
            transactions.append((
                t_loop2,
                datetime.datetime.fromtimestamp(current_epoch, tz=datetime.timezone.utc).isoformat(),
                current_epoch,
                l1s[1]["id"], l1s[2]["id"], loop_amt, "UPI", f"LOOP-B-{chain_id}", origin_ref,
                l1s[1]["bank_id"], l1s[2]["bank_id"], 1, chain_id
            ))
            t_loop3 = f"TXN-LOOP3-{txn_counter:06d}"
            txn_counter += 1
            current_epoch += 70
            transactions.append((
                t_loop3,
                datetime.datetime.fromtimestamp(current_epoch, tz=datetime.timezone.utc).isoformat(),
                current_epoch,
                l1s[2]["id"], l1s[0]["id"], loop_amt, "UPI", f"LOOP-C-{chain_id}", origin_ref,
                l1s[2]["bank_id"], l1s[0]["bank_id"], 1, chain_id
            ))

        # Hop 1 -> Hop 2: Rapid pass-through from L1 to L2
        # Rapid dwell time: 2 to 8 minutes (or 8-24 hours for holdout chain 8)
        # Haircut: 2% to 4% commission retained by mule
        l2_inbounds = {l2["id"]: [] for l2 in l2s}
        
        for l1 in l1s:
            l1_total = sum(l1_inbounds[l1["id"]])
            retention_rate = rng.uniform(0.02, 0.04) # Mule keeps 2-4%
            forward_amt = l1_total * (1.0 - retention_rate)
            dest_l2 = rng.choice(l2s)
            
            # Structuring into round lots just below ₹100k / ₹50k
            num_pieces = max(1, int(forward_amt // 95000))
            piece_val = forward_amt / num_pieces
            
            for p in range(num_pieces):
                dwell = rng.randint(90, 480) if not is_holdout else rng.randint(28800, 64800)
                current_epoch += dwell
                txn_id = f"TXN-C{chain_id[-2:]}-HOP2-{txn_counter:06d}"
                txn_counter += 1
                amt = round(piece_val, 2)
                l2_inbounds[dest_l2["id"]].append(amt)
                
                transactions.append((
                    txn_id,
                    datetime.datetime.fromtimestamp(current_epoch, tz=datetime.timezone.utc).isoformat(),
                    current_epoch,
                    l1["id"],
                    dest_l2["id"],
                    amt,
                    "IMPS" if amt <= 200000 else "NEFT",
                    f"REF-L2-{chain_id}-{txn_counter}",
                    origin_ref,
                    l1["bank_id"],
                    dest_l2["bank_id"],
                    1,
                    chain_id
                ))

        # Hop 2 -> Hop 3: Layer 2 into Cash-Out Exits (or Honeypot!)
        for l2 in l2s:
            inbound_sum = sum(l2_inbounds[l2["id"]])
            if inbound_sum <= 0:
                continue
            retention_rate = rng.uniform(0.01, 0.03)
            exit_amt = inbound_sum * (1.0 - retention_rate)
            
            # For Chain 3 & Chain 7, one branch feeds into Honeypot!
            if chain_id in ["CHAIN-03", "CHAIN-07"] and rng.random() < 0.5:
                dest_exit = honeypots[0] if chain_id == "CHAIN-03" else honeypots[1]
            else:
                dest_exit = rng.choice(exits)

            num_exit_txns = max(1, int(exit_amt // 190000))
            part_val = exit_amt / num_exit_txns

            for pe in range(num_exit_txns):
                dwell = rng.randint(120, 600) if not is_holdout else rng.randint(36000, 72000)
                current_epoch += dwell
                txn_id = f"TXN-C{chain_id[-2:]}-HOP3-{txn_counter:06d}"
                txn_counter += 1
                amt = round(part_val, 2)

                transactions.append((
                    txn_id,
                    datetime.datetime.fromtimestamp(current_epoch, tz=datetime.timezone.utc).isoformat(),
                    current_epoch,
                    l2["id"],
                    dest_exit["id"],
                    amt,
                    "IMPS" if amt <= 200000 else "RTGS",
                    f"REF-EXIT-{chain_id}-{txn_counter}",
                    origin_ref,
                    l2["bank_id"],
                    dest_exit["bank_id"],
                    1,
                    chain_id
                ))

    # B. Legitimate Commercial Transactions
    # 1. Shopkeepers: High Fan-In (each shopkeeper receives ~200-300 small retail payments)
    for shop in shopkeeper_accounts:
        num_sales = rng.randint(120, 220)
        for _ in range(num_sales):
            sec = rng.randint(start_epoch, base_epoch)
            sender_acc = rng.choice(regular_accounts)
            amt = round(rng.uniform(40.0, 3500.0), 2)
            txn_id = f"TXN-LEGIT-{txn_counter:07d}"
            txn_counter += 1
            transactions.append((
                txn_id,
                datetime.datetime.fromtimestamp(sec, tz=datetime.timezone.utc).isoformat(),
                sec,
                sender_acc["id"],
                shop["id"],
                amt,
                "UPI",
                f"UPI-MERCHANT-{rng.randint(10000000, 99999999)}",
                None,
                sender_acc["bank_id"],
                shop["bank_id"],
                0,
                None
            ))

    # 2. Payroll Accounts: High Fan-Out on 1st & 30th of month
    for payroll in payroll_accounts:
        # Two pay cycles
        for cycle_day in [1, 28]:
            cycle_epoch = start_epoch + (cycle_day * 86400) + rng.randint(28800, 43200)
            employees = rng.sample(regular_accounts, k=rng.randint(80, 160))
            for emp in employees:
                cycle_epoch += rng.randint(2, 20)
                amt = round(rng.uniform(32000.0, 145000.0), 2)
                txn_id = f"TXN-SAL-{txn_counter:07d}"
                txn_counter += 1
                transactions.append((
                    txn_id,
                    datetime.datetime.fromtimestamp(cycle_epoch, tz=datetime.timezone.utc).isoformat(),
                    cycle_epoch,
                    payroll["id"],
                    emp["id"],
                    amt,
                    "NEFT",
                    f"SALARY-OCT2026-{rng.randint(100000, 999999)}",
                    None,
                    payroll["bank_id"],
                    emp["bank_id"],
                    0,
                    None
                ))

    # 3. Regular Consumer & Peer-to-Peer Transactions to reach ~150,000 transactions
    needed_regular = 150000 - len(transactions)
    for _ in range(max(1000, needed_regular)):
        sec = rng.randint(start_epoch, base_epoch)
        snd = rng.choice(regular_accounts)
        rcv = rng.choice(regular_accounts)
        if snd["id"] == rcv["id"]:
            continue
        amt = round(rng.expovariate(1.0 / 1500.0) + 100.0, 2)
        if amt > 200000.0:
            amt = round(rng.uniform(5000.0, 45000.0), 2)
        txn_id = f"TXN-GEN-{txn_counter:07d}"
        txn_counter += 1
        transactions.append((
            txn_id,
            datetime.datetime.fromtimestamp(sec, tz=datetime.timezone.utc).isoformat(),
            sec,
            snd["id"],
            rcv["id"],
            amt,
            rng.choice(CHANNELS),
            f"REF-P2P-{rng.randint(10000000, 99999999)}",
            None,
            snd["bank_id"],
            rcv["bank_id"],
            0,
            None
        ))

    # 4. Planted Vendors & Invoices (Business Shield)
    # Plant 10 vendors, with 2 having active bank-detail-change attacks
    vendors = []
    invoices = []
    vendor_templates = [
        ("VEND-001", "Apex Cloud Infrastructure Pvt Ltd", "BANK_ALPHA", False, None),
        ("VEND-002", "Titanium Office Supplies Ltd", "BANK_BETA", False, None),
        ("VEND-003", "Precision Tooling & Fabrication", "BANK_GAMMA", True, "Bank account suddenly redirected to newly opened Layer-1 mule account ACC-MULE-C01-L1-1"),
        ("VEND-004", "Quantum Logistics Global", "BANK_ALPHA", False, None),
        ("VEND-005", "Nexus Corporate Catering Co", "BANK_BETA", False, None),
        ("VEND-006", "SecureShield Facilities & Guarding", "BANK_GAMMA", True, "Payout route modified 18 hours before billing cycle to ACC-MULE-C04-L1-2"),
        ("VEND-007", "Starlight Media & Ad Solutions", "BANK_ALPHA", False, None),
        ("VEND-008", "Frontier Data Analytics Corp", "BANK_BETA", False, None),
        ("VEND-009", "Horizon Fleet Telematics", "BANK_GAMMA", False, None),
        ("VEND-010", "Vertex Legal & Advisory LLP", "BANK_ALPHA", False, None)
    ]

    for v_id, v_name, v_bank, is_att, att_desc in vendor_templates:
        orig_acc = f"ACC-CORP-{v_id}"
        # If attacked, assign to a planted mule account
        assigned_acc = "ACC-MULE-C01-L1-1" if v_id == "VEND-003" else ("ACC-MULE-C04-L1-2" if v_id == "VEND-006" else orig_acc)
        vendors.append((v_id, v_name, assigned_acc, v_bank, orig_acc, 1 if is_att else 0, att_desc))

        # Invoices for this vendor
        num_inv = rng.randint(2, 4)
        for i_idx in range(1, num_inv + 1):
            inv_id = f"INV-{v_id[-3:]}-{i_idx:03d}"
            amt = round(rng.uniform(120000.0, 950000.0), 2)
            due = (now + datetime.timedelta(days=rng.randint(3, 14))).strftime("%Y-%m-%d")
            status = "HELD_ALERT" if is_att and i_idx == 1 else ("PAID" if i_idx > 1 else "PENDING_REVIEW")
            invoices.append((
                inv_id,
                v_id,
                amt,
                due,
                assigned_acc,
                v_bank,
                1 if (is_att and i_idx == 1) else 0,
                status
            ))

    # 5. Seed Cases (Case Clock workflow)
    # Plant cases in different regulatory stages: Suspected, Show-cause issued, Classified, etc.
    seed_cases = [
        (
            "CASE-2026-001",
            "ACC-MULE-C01-L1-1",
            "SHOW_CAUSE_ISSUED",
            (now - datetime.timedelta(days=7)).isoformat(),
            21, 14, 7,
            '{"inbound_24h": 950000.0, "outbound_ratio": 0.98, "dwell_mins": 3.2, "shared_device": "DEV-MULE-CLUSTER-01"}',
            "Account opened 12 days ago received rapid aggregation of stolen corporate funds from Victim Corp 01 and dispersed within 3.2 minutes to multiple secondary nodes.",
            "WHEREAS the bank's automated fraud monitoring systems have detected structured pass-through transactions aggregating INR 9,50,000 within 180 seconds across interconnected digital payment rails, notice is hereby given under Section 35A of the Banking Regulation Act to show cause within 21 days as to why legal lien and cybercrime escalation should not be confirmed.",
            0
        ),
        (
            "CASE-2026-002",
            "ACC-MULE-C02-L1-1",
            "REPRESENTATION_RECEIVED",
            (now - datetime.timedelta(days=16)).isoformat(),
            21, 14, 16,
            '{"inbound_24h": 1400000.0, "dormant_days": 185, "circular_flows": true}',
            "Reactivated dormant account with 0 balance for 6 months suddenly received ₹14,00,000 followed by circular wash transactions.",
            "Customer submitted written representation claiming account was compromised via remote screen-sharing application. Verification pending compliance review.",
            0
        ),
        (
            "CASE-2026-003",
            "ACC-MULE-C04-L1-2",
            "CLASSIFIED",
            (now - datetime.timedelta(days=24)).isoformat(),
            21, 14, 24,
            '{"inbound_24h": 780000.0, "vendor_takeover": true, "shared_ip": "198.51.100.12"}',
            "Linked to unauthorized vendor detail diversion on SecureShield Facilities. Internal Fraud Committee classified account on Day 21.",
            "Internal Fraud Monitoring Committee classification confirmed. 14-day statutory FMR-1 filing clock active with Central Fraud Registry (RBI CFR).",
            1
        )
    ]

    # Batch Insert Everything
    cursor.executemany("""
    INSERT INTO accounts (id, bank_id, open_date, kyc_tier, is_mule, role, pseudonymous_label, initial_balance, current_balance, is_honeypot, chain_id, layer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(a["id"], a["bank_id"], a["open_date"], a["kyc_tier"], a["is_mule"], a["role"], a["pseudonymous_label"], a["initial_balance"], a["current_balance"], a["is_honeypot"], a.get("chain_id"), a.get("layer", 0)) for a in accounts])

    cursor.executemany("""
    INSERT INTO devices (account_id, device_id, ip, phone)
    VALUES (?, ?, ?, ?)
    """, devices)

    cursor.executemany("""
    INSERT INTO transactions (id, ts, epoch_seconds, sender, receiver, amount, channel, ref, origin_txn_id, sender_bank, receiver_bank, is_mule_flow, chain_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    cursor.executemany("""
    INSERT INTO vendors (vendor_id, vendor_name, account_id, bank_id, original_account_id, is_attacked, attack_description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, vendors)

    cursor.executemany("""
    INSERT INTO invoices (invoice_id, vendor_id, amount, due_date, account_id, bank_id, flag_bank_detail_change, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, invoices)

    cursor.executemany("""
    INSERT INTO cases (case_id, account_id, stage, created_ts, show_cause_deadline_days, fmr_deadline_days, elapsed_days, evidence_json, llm_case_summary, show_cause_draft, human_approved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, seed_cases)

    conn.commit()
    conn.close()

    total_mules = sum(1 for a in accounts if a["is_mule"] == 1 and not a["is_honeypot"])
    return {
        "accounts_count": len(accounts),
        "transactions_count": len(transactions),
        "devices_count": len(devices),
        "mules_count": total_mules,
        "honeypots_count": len(honeypots),
        "vendors_count": len(vendors),
        "invoices_count": len(invoices),
        "chains_count": len(chains_meta)
    }

if __name__ == "__main__":
    summary = generate_database()
    print("Database generation complete!")
    print(summary)
