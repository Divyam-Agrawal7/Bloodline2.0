#!/usr/bin/env python3
"""
Bank Server & Bloodline Background Alert Daemon Simulator
-----------------------------------------------------------
Simulates a Core Banking System (CBS) or Payment Switch (UPI/IMPS)
intercepting transactions in real time, consulting the Bloodline 2.0
background fraud engine, and dispatching high-priority banking alerts.

Usage:
  python scripts/bank_server_simulator.py          # Run sample batch test
  python scripts/bank_server_simulator.py --stream # Run continuous transaction stream
"""

import sys
import os
import time
import json
import random
from datetime import datetime
import urllib.request
import urllib.error

# Add parent directory to path so we can import app if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BLOODLINE_API_URL = "http://127.0.0.1:8000"

# ANSI Terminal Colors for Bank Dashboard
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Internal TestClient fallback if network sockets are sandboxed
_test_client = None

def get_client():
    global _test_client
    if _test_client is None:
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            _test_client = TestClient(app)
        except Exception:
            _test_client = False
    return _test_client

# Sample transactions representing legitimate users and planted syndicate mules
SAMPLE_TRANSACTIONS = [
    {
        "txn_id": "TXN-CBS-90101",
        "sender": "ACC00053",
        "sender_name": "Divya Hegde (Private Banking Client)",
        "payee": "ACC02228",
        "payee_name": "Neha Bose (Planted Mule Hub L1)",
        "amount": 95000.0,
        "channel": "IMPS",
        "remark": "Urgent contractor advance"
    },
    {
        "txn_id": "TXN-CBS-90102",
        "sender": "ACC00053",
        "sender_name": "Divya Hegde",
        "payee": "ACC00053",
        "payee_name": "Divya Hegde (Self Transfer / Merchant)",
        "amount": 420.0,
        "channel": "UPI",
        "remark": "Daily essentials"
    },
    {
        "txn_id": "TXN-CBS-90103",
        "sender": "ACC01370",
        "sender_name": "Pooja Patel",
        "payee": "ACC02215",
        "payee_name": "Neha Rao (Syndicate CH01 Mule L1)",
        "amount": 107300.0,
        "channel": "RTGS",
        "remark": "Property deposit"
    },
    {
        "txn_id": "TXN-CBS-90104",
        "sender": "ACC00813",
        "sender_name": "Rohan Iyer",
        "payee": "ACC02264",
        "payee_name": "Rahul Kulkarni (Syndicate CH08 Mule L1)",
        "amount": 88000.0,
        "channel": "NEFT",
        "remark": "Invoice settlement"
    }
]

def check_bloodline_health():
    """Verify Bloodline decision service is active (via HTTP or in-process)."""
    try:
        req = urllib.request.Request(f"{BLOODLINE_API_URL}/health")
        with urllib.request.urlopen(req, timeout=1) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get("status") == "healthy"
    except Exception:
        client = get_client()
        if client:
            res = client.get("/health")
            return res.status_code == 200
        return False

def score_transaction_with_bloodline(txn):
    """
    Synchronous pre-release check calling Bloodline /scan endpoint.
    Returns verdict, probability, plain-English reasons, and latency.
    """
    payload = {
        "payee_account_id": txn["payee"],
        "amount": txn["amount"],
        "sender_account_id": txn["sender"],
        "remark": txn["remark"]
    }
    
    start_t = time.perf_counter()
    
    # Try direct HTTP first
    try:
        req = urllib.request.Request(
            f"{BLOODLINE_API_URL}/scan",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            latency_ms = (time.perf_counter() - start_t) * 1000
            res_data = json.loads(resp.read().decode('utf-8'))
            res_data["latency_ms"] = latency_ms
            return res_data
    except Exception:
        # Fallback to direct client call
        client = get_client()
        if client:
            res = client.post("/scan", json=payload)
            latency_ms = (time.perf_counter() - start_t) * 1000
            if res.status_code == 200:
                res_data = res.json()
                res_data["latency_ms"] = latency_ms
                return res_data

    return {
        "verdict": "ALLOW",
        "probability": 0.0,
        "fallback_fail_open": True,
        "latency_ms": (time.perf_counter() - start_t) * 1000
    }

def trigger_bank_administrative_lien(account_id, reason):
    """Notify Bloodline & CBS to place an administrative hold on tainted account."""
    payload = {"account_id": account_id}
    try:
        req = urllib.request.Request(
            f"{BLOODLINE_API_URL}/hold-request",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        client = get_client()
        if client:
            res = client.post("/hold-request", json=payload)
            if res.status_code == 200:
                return res.json()
    return {"outcome": "HELD (SIMULATED)"}

def dispatch_bank_alert(txn, decision):
    """
    Simulate Core Banking System Alert Dispatcher:
    Prints structured banking alerts for fraud operations desk.
    """
    verdict = decision.get("verdict", "ALLOW")
    prob = decision.get("probability", 0.0)
    latency = decision.get("latency_ms", 0.0)
    reasons = decision.get("plain_language_reasons", [])
    
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"[{ts}] {BOLD}CORE BANKING GATEWAY INTERCEPTION{RESET} | Txn: {txn['txn_id']} | Channel: {txn['channel']}")
    print(f"Transfer: {txn['sender']} ({txn['sender_name']}) &rarr; {txn['payee']} ({txn['payee_name']})")
    print(f"Amount: ₹{txn['amount']:,.2f} | Bloodline Latency: {latency:.2f} ms")
    
    if verdict == "ALLOW":
        print(f"Status: {GREEN}{BOLD}✓ ALLOWED & SETTLED{RESET} (Mule Risk Score: {prob*100:.1f}%)")
        print(f"Bank Action: Transfer released immediately to clearing rails.")
        
    elif verdict == "DELAY":
        print(f"Status: {YELLOW}{BOLD}⚠ INTERCEPTED: 60-SECOND COOLDOWN APPLIED{RESET} (Mule Risk Score: {prob*100:.1f}%)")
        print(f"Bank Action: Prompt customer with scam warning modal before release.")
        if reasons:
            print(f"Forensic Indicators:")
            for r in reasons:
                print(f"  • {r}")
                
    elif verdict == "HOLD":
        print(f"Status: {RED}{BOLD}🚨 CRITICAL FRAUD ALERT: ADMINISTRATIVE LIEN HOLD TRIGGERED{RESET} (Mule Risk: {prob*100:.1f}%)")
        print(f"Bank Action: Funds held before debited. Notified Bank Fraud Operations Desk.")
        if reasons:
            print(f"SHAP Forensic Evidence:")
            for r in reasons:
                print(f"  • {r}")
                
        # Trigger lien hold
        lien_res = trigger_bank_administrative_lien(txn['payee'], "High-risk syndicate aggregation hub")
        print(f"Lien Status: {CYAN}Administrative Lien Successfully Placed ({lien_res.get('outcome', 'HELD')}){RESET}")
        
    print(f"{BOLD}{'='*80}{RESET}")

def run_simulation(stream_mode=False):
    print(f"{BOLD}{CYAN}")
    print("================================================================================")
    print("       BANK CORE SWITCH & BLOODLINE BACKGROUND DECISION ENGINE SIMULATOR       ")
    print("================================================================================")
    print(f"{RESET}")
    print(f"Connecting to Bloodline Engine at {BLOODLINE_API_URL}...")
    
    if not check_bloodline_health():
        print(f"{RED}ERROR: Bloodline Decision Service is not reachable!{RESET}")
        sys.exit(1)
        
    print(f"{GREEN}✓ Connected to Bloodline Core Decision Engine.{RESET}\n")
    print("Simulating Core Banking Server transactions intercepted at payment switch...")
    
    if not stream_mode:
        for txn in SAMPLE_TRANSACTIONS:
            decision = score_transaction_with_bloodline(txn)
            dispatch_bank_alert(txn, decision)
            time.sleep(0.3)
        print(f"\n{GREEN}{BOLD}✓ Batch processing simulation complete.{RESET}")
        print("To run continuous transaction stream, execute: python scripts/bank_server_simulator.py --stream\n")
    else:
        print(f"{YELLOW}Running in continuous live stream mode. Press Ctrl+C to terminate.{RESET}\n")
        try:
            counter = 1
            while True:
                base_txn = random.choice(SAMPLE_TRANSACTIONS)
                txn = dict(base_txn)
                txn["txn_id"] = f"TXN-LIVE-{counter:06d}"
                txn["amount"] = round(random.uniform(500, 150000), 2)
                
                decision = score_transaction_with_bloodline(txn)
                dispatch_bank_alert(txn, decision)
                
                counter += 1
                time.sleep(random.uniform(1.2, 2.5))
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Simulation interrupted by user. Exiting cleanly.{RESET}")

if __name__ == "__main__":
    is_stream = "--stream" in sys.argv
    run_simulation(stream_mode=is_stream)
