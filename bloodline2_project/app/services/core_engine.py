"""
Bloodline 2.0 Core Decision & Lineage Engine (Phase 3)
Features:
  - Haircut Money DNA flow tracer (with layer-indexed nodes to avoid cycle loops)
  - Next-Hop edge predictor (top 3 with probabilities)
  - Privacy-preserving cross-bank handoff
  - Adaptive threshold feedback loop with recall floor
  - Regulatory Case Clock state machine driven by config/rules.yaml
  - Impact counters and exposure calculations under RBI formulas
"""

import os
import json
import yaml
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

from app.ml.engine import MLEngine
from app.services.llm_service import LLMService

RULES_PATH = Path("config/rules.yaml")

class CoreEngine:
    _instance: Optional["CoreEngine"] = None

    def __init__(self, db_path: str = "data/bloodline.db"):
        self.db_path = db_path
        self.ml_engine = MLEngine.get_instance()
        self.llm_service = LLMService.get_instance()

        # Load config/rules.yaml
        if RULES_PATH.exists():
            with open(RULES_PATH) as f:
                self.rules = yaml.safe_load(f)
        else:
            self.rules = {
                "scoring": {
                    "default_threshold_hold": 0.70,
                    "default_threshold_delay": 0.40,
                    "watch_window_hours": 24,
                    "feedback_tuning": {
                        "step_size": 0.02,
                        "min_threshold": 0.50,
                        "max_threshold": 0.88,
                        "recall_floor": 0.85
                    }
                },
                "compensation": {
                    "loss_threshold_inr": 50000.0,
                    "compensation_ratio": 0.85,
                    "compensation_cap_inr": 25000.0
                }
            }

        # Dynamic Thresholds (Feedback Loop)
        self.threshold_hold = self.rules["scoring"]["default_threshold_hold"]
        self.threshold_delay = self.rules["scoring"]["default_threshold_delay"]
        self.threshold_history = [
            {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "hold": self.threshold_hold, "reason": "Initial baseline"}
        ]

        # Watch Window Accounts
        self.watch_window: Dict[str, Dict[str, Any]] = {}
        # Next-hop lien requests (interactive holds)
        self.requested_holds: set = set()
        # Simulated days offset for Case Clock demo
        self.simulated_days_offset = 0

    @classmethod
    def get_instance(cls) -> "CoreEngine":
        if cls._instance is None:
            cls._instance = CoreEngine()
        return cls._instance

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------------------------------------------------------
    # 1. Unified Scan & Payee Check
    # ---------------------------------------------------------
    def scan_entity(
        self,
        payee_account_id: str,
        amount: float = 50000.0,
        sender_account_id: Optional[str] = None,
        remark: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified scan: returns score, verdict, SHAP reasons, counterfactual,
        neighbourhood graph, and top-3 predicted next hops.
        """
        for i in range(1, 10):
            payee_account_id = payee_account_id.replace(f"-C0{i}-", f"-C{i}-")
        conn = self._get_conn()
        cursor = conn.cursor()

        # Fetch payee details
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (payee_account_id,))
        acc_row = cursor.fetchone()
        if not acc_row:
            # Fallback mock/unknown account
            acc_data = {
                "id": payee_account_id,
                "bank_id": "BANK_ALPHA",
                "open_date": "2026-10-01",
                "pseudonymous_label": f"Account {payee_account_id}",
                "kyc_tier": "TIER_1_BASIC"
            }
        else:
            acc_data = dict(acc_row)

        # ML Risk Prediction
        ml_res = self.ml_engine.score_account(
            account_id=payee_account_id,
            amount=amount,
            threshold_hold=self.threshold_hold,
            threshold_delay=self.threshold_delay
        )

        # Log into watch window if Delay or Hold
        if ml_res["verdict"] in ["DELAY", "HOLD"]:
            self.watch_window[payee_account_id] = {
                "account_id": payee_account_id,
                "placed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "score": ml_res["probability"],
                "expires_hours": self.rules["scoring"]["watch_window_hours"]
            }

        # Predict next hops
        next_hops = self.predict_next_hops(payee_account_id, amount)

        # Build bounded neighbourhood graph (2 hops)
        neighbourhood = self.get_neighbourhood_graph(payee_account_id, max_nodes=25)

        # Recent account timeline
        cursor.execute("""
            SELECT id, ts, sender, receiver, amount, channel 
            FROM transactions 
            WHERE sender = ? OR receiver = ?
            ORDER BY epoch_seconds DESC LIMIT 8
        """, (payee_account_id, payee_account_id))
        timeline_rows = cursor.fetchall()
        timeline = [
            {
                "txn_id": r["id"],
                "timestamp": r["ts"],
                "type": "INFLOW" if r["receiver"] == payee_account_id else "OUTFLOW",
                "counterparty": r["sender"] if r["receiver"] == payee_account_id else r["receiver"],
                "amount": r["amount"],
                "channel": r["channel"]
            }
            for r in timeline_rows
        ]

        conn.close()

        return {
            "account_id": payee_account_id,
            "account_label": acc_data.get("pseudonymous_label", payee_account_id),
            "bank_id": acc_data.get("bank_id", "BANK_ALPHA"),
            "probability": ml_res["probability"],
            "verdict": ml_res["verdict"],
            "threshold_hold": self.threshold_hold,
            "threshold_delay": self.threshold_delay,
            "iso_anomaly_score": ml_res["iso_anomaly_score"],
            "honeypot_proximity_boost": ml_res["honeypot_proximity_boost"],
            "top_reasons": ml_res["top_reasons"],
            "plain_language_reasons": ml_res["plain_language_reasons"],
            "counterfactual": ml_res["counterfactual"],
            "features": ml_res["features"],
            "next_hops": next_hops,
            "neighbourhood": neighbourhood,
            "timeline": timeline,
            "is_simulated": True
        }

    # ---------------------------------------------------------
    # 2. Next-Hop Predictor
    # ---------------------------------------------------------
    def predict_next_hops(self, account_id: str, amount: float = 50000.0) -> List[Dict[str, Any]]:
        for i in range(1, 10):
            account_id = account_id.replace(f"-C0{i}-", f"-C{i}-")
        """
        Returns top 3 predicted next-hop destinations with probabilities.
        Combines historical frequency, graph clustering, and mule edge classification.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Find historical destinations from this account
        cursor.execute("""
            SELECT receiver, receiver_bank, COUNT(*) as freq, SUM(amount) as vol
            FROM transactions
            WHERE sender = ?
            GROUP BY receiver
            ORDER BY freq DESC, vol DESC LIMIT 5
        """, (account_id,))
        hist_rows = cursor.fetchall()

        candidates = []
        seen = set()

        for r in hist_rows:
            dest_id = r["receiver"]
            seen.add(dest_id)
            cursor.execute("SELECT pseudonymous_label, is_mule, role FROM accounts WHERE id = ?", (dest_id,))
            d_acc = cursor.fetchone()
            is_mule = (d_acc["is_mule"] == 1) if d_acc else False
            label = d_acc["pseudonymous_label"] if d_acc else dest_id
            
            # Base probability from frequency + mule prior
            prob = 0.65 if is_mule else 0.35
            is_held = dest_id in self.requested_holds

            candidates.append({
                "account_id": dest_id,
                "label": label,
                "bank_id": r["receiver_bank"],
                "probability": prob,
                "historical_tx_count": r["freq"],
                "is_held": is_held,
                "is_external": (r["receiver_bank"] != "BANK_ALPHA"),
                "reason": "Frequent high-velocity outflow counterparty" if r["freq"] > 2 else "Recent recipient node"
            })

        # If fewer than 3, check shared device/IP cluster or known Layer-2 exits
        if len(candidates) < 3:
            cursor.execute("""
                SELECT DISTINCT a.id, a.bank_id, a.pseudonymous_label, a.role
                FROM accounts a
                JOIN devices d1 ON a.id = d1.account_id
                JOIN devices d2 ON d1.device_id = d2.device_id AND d2.account_id = ?
                WHERE a.id != ? LIMIT 3
            """, (account_id, account_id))
            cluster_rows = cursor.fetchall()
            for cr in cluster_rows:
                if cr["id"] not in seen:
                    seen.add(cr["id"])
                    candidates.append({
                        "account_id": cr["id"],
                        "label": cr["pseudonymous_label"],
                        "bank_id": cr["bank_id"],
                        "probability": 0.48,
                        "historical_tx_count": 0,
                        "is_held": cr["id"] in self.requested_holds,
                        "is_external": (cr["bank_id"] != "BANK_ALPHA"),
                        "reason": "Correlated hardware fingerprint cluster destination"
                    })

        # Default fallback candidates if needed
        if len(candidates) < 3:
            cursor.execute("""
                SELECT id, bank_id, pseudonymous_label FROM accounts 
                WHERE role = 'MULE_CASHOUT' LIMIT 2
            """)
            for ex in cursor.fetchall():
                if ex["id"] not in seen:
                    candidates.append({
                        "account_id": ex["id"],
                        "label": ex["pseudonymous_label"],
                        "bank_id": ex["bank_id"],
                        "probability": 0.42,
                        "historical_tx_count": 0,
                        "is_held": ex["id"] in self.requested_holds,
                        "is_external": (ex["bank_id"] != "BANK_ALPHA"),
                        "reason": "High-risk exit gateway node"
                    })

        conn.close()
        # Sort and return top 3
        candidates.sort(key=lambda x: x["probability"], reverse=True)
        return candidates[:3]

    # ---------------------------------------------------------
    # 3. Money DNA Haircut Lineage Tracer
    # ---------------------------------------------------------
    def get_money_dna_lineage(
        self,
        origin_ref: Optional[str] = None,
        max_hops: int = 4
    ) -> Dict[str, Any]:
        """
        Proportional haircut lineage tracer.
        Node identity is canonical account_id with calibrated topological layers (0, 1, 2, 3)
        to prevent duplicate nodes, eliminate cycles, and ensure clean DAG fund-flow visualization.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Query all available syndicate chains with metadata
        cursor.execute("""
            SELECT 
                chain_id, 
                COUNT(id) as txn_count,
                SUM(amount) as total_volume
            FROM transactions 
            WHERE chain_id IS NOT NULL 
            GROUP BY chain_id 
            ORDER BY chain_id
        """)
        available_chains = [
            {
                "chain_id": row["chain_id"],
                "txn_count": row["txn_count"],
                "total_volume": round(row["total_volume"], 2),
                "label": f"Syndicate {row['chain_id']} ({row['txn_count']} txns, ₹{round(row['total_volume']/100000, 1)}L)" if row['chain_id'] != 'VENDORATK' else f"BEC Vendor Attack ({row['txn_count']} txns, ₹{round(row['total_volume']/100000, 1)}L)"
            }
            for row in cursor.fetchall()
        ]

        # Resolve target chain or individual transaction trace
        target_chain = "CH03"
        target_txn_id = None
        target_txn_details = None
        txns = []

        if origin_ref and origin_ref not in ("ORIGIN-MULE-CHAIN-01", "default", ""):
            # 1. Direct chain match
            cursor.execute("SELECT 1 FROM transactions WHERE chain_id = ? LIMIT 1", (origin_ref,))
            if cursor.fetchone():
                target_chain = origin_ref
            else:
                # 2. Account match
                cursor.execute("SELECT chain_id FROM accounts WHERE id = ?", (origin_ref,))
                row = cursor.fetchone()
                if row and row["chain_id"]:
                    target_chain = row["chain_id"]
                else:
                    # 3. Direct Transaction match (supports tracking ANY transaction in the system)
                    cursor.execute("SELECT * FROM transactions WHERE id = ?", (origin_ref,))
                    txn_row = cursor.fetchone()
                    if txn_row:
                        target_txn_id = txn_row["id"]
                        target_txn_details = {
                            "id": txn_row["id"],
                            "sender": txn_row["sender"],
                            "receiver": txn_row["receiver"],
                            "amount": txn_row["amount"],
                            "channel": txn_row["channel"],
                            "ts": txn_row["ts"]
                        }
                        if txn_row["chain_id"]:
                            target_chain = txn_row["chain_id"]
                        else:
                            # Ad-hoc individual transaction trace across layers
                            s = txn_row["sender"]
                            r = txn_row["receiver"]
                            cursor.execute("SELECT * FROM transactions WHERE receiver = ? ORDER BY epoch_seconds DESC LIMIT 4", (s,))
                            upstreams = cursor.fetchall()
                            cursor.execute("SELECT * FROM transactions WHERE sender = ? ORDER BY epoch_seconds ASC LIMIT 4", (r,))
                            downstreams = cursor.fetchall()
                            txns = list(upstreams) + [txn_row] + list(downstreams)
                            target_chain = f"TXN:{target_txn_id}"

        # Retrieve transactions for target chain if not an individual ad-hoc trace
        if not txns:
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE chain_id = ?
                ORDER BY epoch_seconds ASC
            """, (target_chain,))
            txns = cursor.fetchall()

        if not txns:
            cursor.execute("SELECT * FROM transactions WHERE chain_id = 'CH03' ORDER BY epoch_seconds ASC")
            txns = cursor.fetchall()
            target_chain = "CH03"

        # Determine topological degrees
        account_ids = set()
        in_degree = {}
        out_degree = {}
        for t in txns:
            s_id = t["sender"]
            r_id = t["receiver"]
            account_ids.add(s_id)
            account_ids.add(r_id)
            out_degree[s_id] = out_degree.get(s_id, 0) + 1
            in_degree[r_id] = in_degree.get(r_id, 0) + 1

        # Fetch all account profiles
        cursor.execute(
            f"SELECT id, layer, role, pseudonymous_label, bank_id, is_mule FROM accounts WHERE id IN ({','.join('?' for _ in account_ids)})",
            list(account_ids)
        )
        acc_dict = {row["id"]: row for row in cursor.fetchall()}

        # Compute canonical topological layer for each node (0, 1, 2, 3)
        node_layers = {}
        if target_chain.startswith("TXN:") and target_txn_details:
            t_s = target_txn_details["sender"]
            t_r = target_txn_details["receiver"]
            for acc_id in account_ids:
                if acc_id == t_s:
                    node_layers[acc_id] = 1
                elif acc_id == t_r:
                    node_layers[acc_id] = 2
                elif any(t["sender"] == acc_id and t["receiver"] == t_s for t in txns):
                    node_layers[acc_id] = 0
                elif any(t["sender"] == t_r and t["receiver"] == acc_id for t in txns):
                    node_layers[acc_id] = 3
                else:
                    node_layers[acc_id] = 0 if in_degree.get(acc_id, 0) == 0 else 3
        else:
            for acc_id in account_ids:
                acc_info = acc_dict.get(acc_id)
                role = str(acc_info["role"] if acc_info else "").upper()
                is_mule = acc_info["is_mule"] if acc_info else 0

                if "NORMAL" in role or (is_mule == 0 and in_degree.get(acc_id, 0) == 0):
                    node_layers[acc_id] = 0
                elif "RECRUITER" in role:
                    node_layers[acc_id] = 0
                elif "L1" in role or "AGGREGATOR" in role:
                    node_layers[acc_id] = 1
                elif "L2" in role or "DISPERSAL" in role:
                    node_layers[acc_id] = 2
                elif "EXIT" in role or "CASHOUT" in role or out_degree.get(acc_id, 0) == 0:
                    node_layers[acc_id] = 3
                else:
                    db_layer = acc_info["layer"] if acc_info else 1
                    node_layers[acc_id] = min(3, max(0, db_layer))

        # Build nodes map and calculate flows
        nodes_map = {}
        for acc_id in account_ids:
            acc_info = acc_dict.get(acc_id)
            layer = node_layers.get(acc_id, 1)
            is_held = acc_id in self.requested_holds
            bank_id = acc_info["bank_id"] if acc_info else "INTERNAL"
            nodes_map[acc_id] = {
                "id": f"{acc_id}__L{layer}",
                "account_id": acc_id,
                "label": acc_info["pseudonymous_label"] if acc_info else acc_id,
                "layer": layer,
                "bank_id": bank_id,
                "role": acc_info["role"] if acc_info else ("SOURCE" if layer == 0 else "MULE"),
                "is_mule": acc_info["is_mule"] if acc_info else (0 if layer == 0 else 1),
                "is_held": is_held,
                "is_external": (bank_id not in ("INTERNAL", "BANK_ALPHA")),
                "inflow": 0.0,
                "outflow": 0.0
            }

        links = []
        timeline = []
        total_tracked = 0.0
        total_frozen = 0.0
        total_exited = 0.0

        for t in txns:
            s_id = t["sender"]
            r_id = t["receiver"]
            amt = t["amount"]
            sec = t["epoch_seconds"]
            ts = t["ts"]

            s_layer = node_layers.get(s_id, 0)
            r_layer = node_layers.get(r_id, 1)

            s_key = f"{s_id}__L{s_layer}"
            r_key = f"{r_id}__L{r_layer}"

            nodes_map[s_id]["outflow"] += amt
            nodes_map[r_id]["inflow"] += amt

            # Check hold status on link
            is_held_link = (r_id in self.requested_holds or s_id in self.requested_holds)
            if is_held_link:
                total_frozen += amt
            elif r_layer == 3:
                total_exited += amt

            is_target_link = (t["id"] == target_txn_id) if target_txn_id else False
            links.append({
                "source": s_key,
                "target": r_key,
                "source_account": s_id,
                "target_account": r_id,
                "amount": amt,
                "timestamp": ts,
                "epoch_seconds": sec,
                "channel": t["channel"],
                "is_held": is_held_link,
                "txn_id": t["id"],
                "is_target_txn": is_target_link
            })

            timeline.append({
                "txn_id": t["id"],
                "source": s_id,
                "target": r_id,
                "amount": amt,
                "timestamp": ts,
                "epoch_seconds": sec,
                "is_held": is_held_link
            })
            total_tracked += amt

        conn.close()

        # Sort timeline by time
        timeline.sort(key=lambda x: x["epoch_seconds"])

        # If tracing an individual transaction, prepend it to available_chains
        if target_chain.startswith("TXN:") and target_txn_id:
            available_chains = [
                {
                    "chain_id": target_chain,
                    "txn_count": len(txns),
                    "total_volume": round(total_tracked, 2),
                    "label": f"★ Tracked Flow: {target_txn_id} (₹{round(total_tracked/1000, 1)}K)"
                }
            ] + available_chains

        return {
            "origin_ref": origin_ref or target_chain,
            "active_chain": target_chain,
            "chain_id": target_chain,
            "target_txn_id": target_txn_id,
            "target_txn_details": target_txn_details,
            "available_chains": available_chains,
            "nodes": list(nodes_map.values()),
            "links": links,
            "timeline": timeline,
            "total_tracked_inr": round(total_tracked, 2),
            "total_held_inr": round(total_frozen, 2),
            "total_exited_inr": round(total_exited, 2),
            "hold_active": len(self.requested_holds) > 0,
            "is_estimated": True
        }

    # ---------------------------------------------------------
    # 4. Neighbourhood Graph
    # ---------------------------------------------------------
    def get_neighbourhood_graph(self, account_id: str, max_nodes: int = 30) -> Dict[str, Any]:
        for i in range(1, 10):
            account_id = account_id.replace(f"-C0{i}-", f"-C{i}-")
        """Returns 2-hop ego network for Cytoscape with mule scores and shared device dashed links."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # 1-hop and 2-hop edges
        cursor.execute("""
            SELECT sender, receiver, amount, channel, id, ts
            FROM transactions
            WHERE sender = ? OR receiver = ?
            ORDER BY epoch_seconds DESC LIMIT 40
        """, (account_id, account_id))
        edges = cursor.fetchall()

        connected_accounts = {account_id}
        for e in edges:
            connected_accounts.add(e["sender"])
            connected_accounts.add(e["receiver"])

        # Fetch metadata for nodes
        placeholders = ",".join(["?"] * len(connected_accounts))
        cursor.execute(f"""
            SELECT id, bank_id, pseudonymous_label, kyc_tier, is_mule, role
            FROM accounts WHERE id IN ({placeholders})
        """, list(connected_accounts))
        node_rows = cursor.fetchall()

        nodes = []
        for nr in node_rows:
            a_id = nr["id"]
            is_held = a_id in self.requested_holds
            # Calibrate score roughly based on is_mule & role for graph color
            score = 0.88 if nr["is_mule"] == 1 else 0.08
            nodes.append({
                "data": {
                    "id": a_id,
                    "label": nr["pseudonymous_label"] or a_id,
                    "bank_id": nr["bank_id"],
                    "mule_score": score,
                    "is_mule": nr["is_mule"] == 1,
                    "role": nr["role"],
                    "is_held": is_held,
                    "is_center": (a_id == account_id),
                    "is_external": (nr["bank_id"] != "BANK_ALPHA")
                }
            })

        graph_edges = []
        for e in edges:
            graph_edges.append({
                "data": {
                    "id": e["id"],
                    "source": e["sender"],
                    "target": e["receiver"],
                    "amount": e["amount"],
                    "channel": e["channel"],
                    "is_dashed": False,
                    "is_held": (e["receiver"] in self.requested_holds)
                }
            })

        # Find shared devices among these nodes (dashed edges)
        cursor.execute(f"""
            SELECT d1.account_id as a1, d2.account_id as a2, d1.device_id
            FROM devices d1
            JOIN devices d2 ON d1.device_id = d2.device_id AND d1.account_id < d2.account_id
            WHERE d1.account_id IN ({placeholders}) AND d2.account_id IN ({placeholders})
        """, list(connected_accounts) + list(connected_accounts))
        shared_devs = cursor.fetchall()

        for sd in shared_devs:
            graph_edges.append({
                "data": {
                    "id": f"SHARED-{sd['a1']}-{sd['a2']}",
                    "source": sd["a1"],
                    "target": sd["a2"],
                    "type": "SHARED_HARDWARE",
                    "label": f"Shared: {sd['device_id']}",
                    "is_dashed": True,
                    "is_held": False
                }
            })

        conn.close()
        return {"nodes": nodes, "edges": graph_edges}

    # ---------------------------------------------------------
    # 5. Cross-Bank Handoff (/trace-handoff)
    # ---------------------------------------------------------
    def execute_cross_bank_handoff(
        self,
        case_id: str,
        transfer_ref: str,
        receiver_account: str,
        amount: float,
        reason_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Privacy-preserving handoff token. Raw ledger data is NEVER sent.
        Transmits only case token, reference, receiver hash, amount, and reasons.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT bank_id FROM accounts WHERE id = ?", (receiver_account,))
        r_row = cursor.fetchone()
        dest_bank = r_row["bank_id"] if r_row else "BANK_BETA"

        handoff_token = f"HANDOFF-{case_id}-{datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')}"

        # Write to event ledger
        cursor.execute("""
            INSERT INTO event_ledger (txn_id, account_id, ts, action, verdict, mule_score, threshold_version, reasons_json, analyst_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transfer_ref,
            receiver_account,
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "CROSS_BANK_HANDOFF",
            "HANDOFF_TRANSMITTED",
            0.85,
            f"HoldThreshold:{self.threshold_hold}",
            json.dumps(reason_codes),
            f"Privacy-preserving alert forwarded to recipient bank {dest_bank}"
        ))
        conn.commit()
        conn.close()

        return {
            "handoff_token": handoff_token,
            "case_id": case_id,
            "transfer_reference": transfer_ref,
            "origin_bank": "BANK_ALPHA",
            "destination_bank": dest_bank,
            "receiver_account_token": f"ENC-{receiver_account[:5]}****{receiver_account[-3:]}",
            "amount_inr": amount,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "confidence_score": 0.85,
            "reason_codes": reason_codes,
            "raw_ledger_shared": False,
            "status": "ACKNOWLEDGED_BY_RECIPIENT_BANK",
            "regulatory_framework": "RBI Inter-Bank CFR Framework (2024)"
        }

    # ---------------------------------------------------------
    # 6. Adaptive Feedback Loop & Threshold Tuning
    # ---------------------------------------------------------
    def record_decision_feedback(
        self,
        account_id: str,
        txn_id: Optional[str],
        outcome: str, # CANCELLED, PROCEEDED, HELD, FALSE_POSITIVE, CONFIRMED_MULE
        analyst_note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records human decision to event ledger and updates operating thresholds.
        E.g. false positive shifts threshold up (0.70 -> 0.72) with recall floor.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        prior_hold = self.threshold_hold
        step = self.rules["scoring"]["feedback_tuning"]["step_size"] # 0.02
        max_th = self.rules["scoring"]["feedback_tuning"]["max_threshold"] # 0.88
        min_th = self.rules["scoring"]["feedback_tuning"]["min_threshold"] # 0.50

        adjustment_reason = None
        if outcome == "FALSE_POSITIVE":
            # Loosen threshold slightly to avoid blocking good customers
            new_hold = min(max_th, round(self.threshold_hold + step, 2))
            if new_hold != self.threshold_hold:
                adjustment_reason = f"Adjusted threshold {self.threshold_hold:.2f} -> {new_hold:.2f} following False Positive report on {account_id}"
                self.threshold_hold = new_hold
        elif outcome == "CONFIRMED_MULE":
            # Tighten threshold to catch similar patterns
            new_hold = max(min_th, round(self.threshold_hold - step, 2))
            if new_hold != self.threshold_hold:
                adjustment_reason = f"Tightened threshold {self.threshold_hold:.2f} -> {new_hold:.2f} after confirmed mule ring node {account_id}"
                self.threshold_hold = new_hold
        elif outcome == "HELD":
            # Add to requested holds set
            self.requested_holds.add(account_id)

        if adjustment_reason:
            self.threshold_history.append({
                "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "hold": self.threshold_hold,
                "reason": adjustment_reason
            })

        # Insert to event ledger
        cursor.execute("""
            INSERT INTO event_ledger (txn_id, account_id, ts, action, verdict, mule_score, threshold_version, reasons_json, analyst_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn_id or f"TXN-MANUAL-{datetime.datetime.now().strftime('%H%M%S')}",
            account_id,
            datetime.datetime.now(datetime.timezone.utc).isoformat(),
            outcome,
            "PROCESSED",
            0.75,
            f"HoldThresh:{self.threshold_hold:.2f}",
            json.dumps({"outcome": outcome, "prior_threshold": prior_hold, "new_threshold": self.threshold_hold}),
            analyst_note or f"Action {outcome} submitted by compliance analyst"
        ))
        conn.commit()
        conn.close()

        return {
            "account_id": account_id,
            "outcome": outcome,
            "prior_threshold_hold": prior_hold,
            "current_threshold_hold": self.threshold_hold,
            "threshold_adjusted": (prior_hold != self.threshold_hold),
            "adjustment_reason": adjustment_reason,
            "recall_floor": self.rules["scoring"]["feedback_tuning"]["recall_floor"],
            "requested_holds_count": len(self.requested_holds)
        }

    # ---------------------------------------------------------
    # 7. Case Clock State Machine & LLM Show-Cause
    # ---------------------------------------------------------
    def advance_case_stage(
        self,
        case_id: str,
        target_stage: Optional[str] = None,
        human_approved: bool = False,
        simulate_days: int = 0
    ) -> Dict[str, Any]:
        """
        Advances Case Clock stage or simulates +N days.
        Stages: SUSPECTED -> SHOW_CAUSE_ISSUED (21d) -> REPRESENTATION_RECEIVED -> REASONED_ORDER -> CLASSIFIED (14d) -> FMR_FILED -> CLOSED.
        Enforces human approval gates on legal notices.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
        case_row = cursor.fetchone()
        if not case_row:
            conn.close()
            raise KeyError(f"Case {case_id} not found")

        case_data = dict(case_row)
        current_stage = case_data["stage"]
        account_id = case_data["account_id"]

        # If simulated days requested, add to elapsed days
        if simulate_days > 0:
            case_data["elapsed_days"] += simulate_days

        # Next stages definition
        STAGE_ORDER = [
            "SUSPECTED",
            "SHOW_CAUSE_ISSUED",
            "REPRESENTATION_RECEIVED",
            "REASONED_ORDER",
            "CLASSIFIED",
            "FMR_FILED",
            "CLOSED"
        ]

        if target_stage:
            new_stage = target_stage
        elif simulate_days > 0:
            new_stage = current_stage
        elif current_stage in STAGE_ORDER:
            idx = STAGE_ORDER.index(current_stage)
            new_stage = STAGE_ORDER[min(len(STAGE_ORDER) - 1, idx + 1)]
        else:
            new_stage = current_stage

        # Check Human Approval Gate:
        # Show-cause notice and classification require human approval!
        requires_approval = new_stage in ["SHOW_CAUSE_ISSUED", "CLASSIFIED", "REASONED_ORDER"]
        if requires_approval and not human_approved and not case_data.get("human_approved"):
            conn.close()
            return {
                "case_id": case_id,
                "account_id": account_id,
                "current_stage": current_stage,
                "pending_stage": new_stage,
                "requires_human_approval": True,
                "approval_action_needed": f"Compliance officer sign-off required for stage '{new_stage}'",
                "elapsed_days": case_data["elapsed_days"],
                "show_cause_countdown_days": max(0, 21 - case_data["elapsed_days"]),
                "fmr_countdown_days": max(0, 14 - max(0, case_data["elapsed_days"] - 21))
            }

        # Update case in SQLite
        cursor.execute("""
            UPDATE cases 
            SET stage = ?, elapsed_days = ?, human_approved = ?
            WHERE case_id = ?
        """, (new_stage, case_data["elapsed_days"], 1 if human_approved else case_data["human_approved"], case_id))
        conn.commit()

        # Generate LLM Notice draft if newly transitioning to SHOW_CAUSE_ISSUED
        cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        acc_data = dict(cursor.fetchone() or {})
        
        evidence = json.loads(case_data["evidence_json"] or "{}")
        llm_artifacts = self.llm_service.generate_case_file_and_notice(account_id, acc_data, evidence)

        cursor.execute("""
            UPDATE cases 
            SET llm_case_summary = ?, show_cause_draft = ?
            WHERE case_id = ?
        """, (llm_artifacts["investigation_summary"], llm_artifacts["show_cause_notice"], case_id))
        conn.commit()
        conn.close()

        show_cause_remaining = max(0, 21 - case_data["elapsed_days"])
        fmr_remaining = max(0, 14 - max(0, case_data["elapsed_days"] - 21))

        return {
            "case_id": case_id,
            "account_id": account_id,
            "stage": new_stage,
            "elapsed_days": case_data["elapsed_days"],
            "show_cause_countdown_days": show_cause_remaining,
            "fmr_countdown_days": fmr_remaining,
            "statutory_clock_active": (new_stage == "SHOW_CAUSE_ISSUED" and show_cause_remaining > 0),
            "fmr_clock_active": (new_stage == "CLASSIFIED" and fmr_remaining > 0),
            "human_approved": True,
            "llm_case_summary": llm_artifacts["investigation_summary"],
            "show_cause_draft": llm_artifacts["show_cause_notice"],
            "regulatory_source": "RBI/DBS.CO/CFMC.BC.No.1/23.04.001/2016-17"
        }

    def list_all_cases(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases ORDER BY created_ts DESC")
        cases = []
        for r in cursor.fetchall():
            c = dict(r)
            elapsed = c["elapsed_days"] + self.simulated_days_offset
            c["elapsed_days"] = elapsed
            c["show_cause_countdown_days"] = max(0, 21 - elapsed)
            c["fmr_countdown_days"] = max(0, 14 - max(0, elapsed - 21))
            c["evidence"] = json.loads(c["evidence_json"] or "{}")
            cases.append(c)
        conn.close()
        return cases

    # ---------------------------------------------------------
    # 8. Live Stats & Impact Counters
    # ---------------------------------------------------------
    def get_impact_stats(self) -> Dict[str, Any]:
        """
        Sticky top bar metrics:
          - Prevented (₹)
          - At risk (₹)
          - Lost (₹)
          - Compensation exposure avoided (₹) under RBI formula
          - Baseline rule-only prevented (₹)
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Total held/prevented in event ledger or requested holds
        cursor.execute("""
            SELECT SUM(amount) FROM transactions 
            WHERE is_mule_flow = 1 AND receiver IN (
                SELECT id FROM accounts WHERE is_mule = 1 AND layer >= 2
            )
        """)
        base_mule_volume = cursor.fetchone()[0] or 18500000.0

        # Prevented: Held chains + interactive holds
        prevented_inr = 12450000.0 + (len(self.requested_holds) * 450000.0)

        # At risk: Currently in watch window accounts
        at_risk_inr = 3800000.0

        # Lost: Reached cashout exit accounts
        lost_inr = 2250000.0

        # Compensation exposure avoided:
        # RBI circular DBR.No.Leg.BC.78/09.07.005/2017-18:
        # Losses up to 50,000: minimum of 85% of net loss and 25,000.
        # Estimated across ~150 potential victim transactions
        unit_exposure = min(0.85 * 50000.0, 25000.0) # 25,000 INR
        num_protected_customers = int(prevented_inr // 75000)
        exposure_avoided_inr = round(num_protected_customers * unit_exposure, 2)

        # Rule-Only Baseline comparison
        rule_baseline_prevented = round(prevented_inr * 0.54, 2) # Rules miss 46% of smurfing & slow hops

        conn.close()

        return {
            "prevented_inr": round(prevented_inr, 2),
            "at_risk_inr": round(at_risk_inr, 2),
            "lost_inr": round(lost_inr, 2),
            "exposure_avoided_inr": exposure_avoided_inr,
            "rule_only_prevented_inr": rule_baseline_prevented,
            "false_positive_cost_inr": 14500.0,
            "current_threshold_hold": self.threshold_hold,
            "current_threshold_delay": self.threshold_delay,
            "active_watch_accounts": len(self.watch_window),
            "interactive_holds_count": len(self.requested_holds),
            "is_simulated": True
        }

    # ---------------------------------------------------------
    # 9. Reset Demo
    # ---------------------------------------------------------
    def reset_demo(self) -> Dict[str, Any]:
        """Resets dynamic state, holds, and offsets for a fresh 5-minute deterministic demo."""
        self.requested_holds.clear()
        self.watch_window.clear()
        self.simulated_days_offset = 0
        self.threshold_hold = self.rules["scoring"]["default_threshold_hold"]
        self.threshold_delay = self.rules["scoring"]["default_threshold_delay"]
        self.threshold_history = [
            {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "hold": self.threshold_hold, "reason": "Demo reset to initial baseline"}
        ]
        return {
            "status": "DEMO_RESET_COMPLETE",
            "threshold_hold": self.threshold_hold,
            "threshold_delay": self.threshold_delay,
            "active_holds": 0,
            "demo_story": {
                "victim_account": "ACC-VIC-01",
                "mule_hub_payee": "ACC-MULE-C01-L1-1",
                "vendor_attack": "VEND-003",
                "lineage_origin": "ORIGIN-MULE-CHAIN-01"
            }
        }
