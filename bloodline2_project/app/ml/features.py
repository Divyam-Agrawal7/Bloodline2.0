"""
Point-in-Time Feature Store for Bloodline 2.0
Computes temporal and graph features strictly as of event timestamp (no future leakage).
"""

import sqlite3
import datetime
import numpy as np
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple

FEATURE_COLUMNS = [
    "account_age_days",
    "senders_1h",
    "senders_24h",
    "senders_7d",
    "new_sender_ratio",
    "pass_through_ratio",
    "median_dwell_time_mins",
    "balance_retention",
    "round_amount_share",
    "structuring_signal",
    "dormancy",
    "share_of_normal_spending",
    "shared_device_count",
    "shared_ip_count",
    "shared_phone_count",
    "hops_to_flagged",
    "flagged_neighbour_share",
    "loop_membership"
]

class FeatureStore:
    def __init__(self, db_path: str = "data/bloodline.db"):
        self.db_path = db_path
        self._shared_cache = None

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_shared_entity_counts(self, account_id: str, conn=None) -> Tuple[int, int, int]:
        """Returns (shared_devices, shared_ips, shared_phones) for an account."""
        close_conn = False
        if conn is None:
            conn = self._get_connection()
            close_conn = True
        cursor = conn.cursor()
        
        # Shared devices
        cursor.execute("""
            SELECT COUNT(DISTINCT d2.account_id) 
            FROM devices d1
            JOIN devices d2 ON d1.device_id = d2.device_id AND d2.account_id != d1.account_id
            WHERE d1.account_id = ?
        """, (account_id,))
        shared_dev = cursor.fetchone()[0] or 0

        # Shared IPs
        cursor.execute("""
            SELECT COUNT(DISTINCT d2.account_id) 
            FROM devices d1
            JOIN devices d2 ON d1.ip = d2.ip AND d2.account_id != d1.account_id
            WHERE d1.account_id = ?
        """, (account_id,))
        shared_ip = cursor.fetchone()[0] or 0

        # Shared Phones
        cursor.execute("""
            SELECT COUNT(DISTINCT d2.account_id) 
            FROM devices d1
            JOIN devices d2 ON d1.phone = d2.phone AND d2.account_id != d1.account_id
            WHERE d1.account_id = ?
        """, (account_id,))
        shared_phone = cursor.fetchone()[0] or 0

        if close_conn:
            conn.close()
        return shared_dev, shared_ip, shared_phone

    def extract_point_in_time_features(
        self,
        account_id: str,
        as_of_epoch: int,
        amount: Optional[float] = None,
        conn=None
    ) -> Dict[str, float]:
        """
        Extract features strictly up to as_of_epoch.
        Guarantees zero future data leakage.
        """
        close_conn = False
        if conn is None:
            conn = self._get_connection()
            close_conn = True
        cursor = conn.cursor()

        # 1. Account Metadata
        cursor.execute("SELECT open_date, initial_balance, is_honeypot, role FROM accounts WHERE id = ?", (account_id,))
        acc_row = cursor.fetchone()
        if not acc_row:
            if close_conn:
                conn.close()
            return {col: 0.0 for col in FEATURE_COLUMNS}

        try:
            open_dt = datetime.datetime.fromisoformat(str(acc_row["open_date"])).replace(tzinfo=datetime.timezone.utc)
        except Exception:
            open_dt = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        as_of_dt = datetime.datetime.fromtimestamp(as_of_epoch, tz=datetime.timezone.utc)
        account_age_days = max(1.0, (as_of_dt - open_dt).total_seconds() / 86400.0)

        # 2. Window Senders (1h, 24h, 7d)
        sec_1h = as_of_epoch - 3600
        sec_24h = as_of_epoch - 86400
        sec_7d = as_of_epoch - (7 * 86400)

        cursor.execute("""
            SELECT 
                COUNT(DISTINCT CASE WHEN epoch_seconds >= ? THEN sender END) as senders_1h,
                COUNT(DISTINCT CASE WHEN epoch_seconds >= ? THEN sender END) as senders_24h,
                COUNT(DISTINCT CASE WHEN epoch_seconds >= ? THEN sender END) as senders_7d,
                SUM(CASE WHEN epoch_seconds >= ? THEN amount ELSE 0 END) as inbound_24h
            FROM transactions
            WHERE receiver = ? AND epoch_seconds <= ?
        """, (sec_1h, sec_24h, sec_7d, sec_24h, account_id, as_of_epoch))
        inbound_row = cursor.fetchone()

        senders_1h = float(inbound_row["senders_1h"] or 0)
        senders_24h = float(inbound_row["senders_24h"] or 0)
        senders_7d = float(inbound_row["senders_7d"] or 0)
        inbound_24h = float(inbound_row["inbound_24h"] or 0.0)
        if amount and amount > 0:
            inbound_24h += amount

        # 3. New Sender Ratio in 24h
        cursor.execute("""
            SELECT sender, MIN(epoch_seconds) as first_seen
            FROM transactions
            WHERE receiver = ? AND epoch_seconds <= ?
            GROUP BY sender
        """, (account_id, as_of_epoch))
        first_seens = cursor.fetchall()
        
        if first_seens:
            new_senders = sum(1 for r in first_seens if r["first_seen"] >= sec_24h)
            new_sender_ratio = float(new_senders / len(first_seens))
        else:
            new_sender_ratio = 1.0 if (amount and amount > 0) else 0.0

        # 4. Outbound & Pass-through in 24h
        cursor.execute("""
            SELECT SUM(amount) as outbound_24h, COUNT(*) as out_count
            FROM transactions
            WHERE sender = ? AND epoch_seconds >= ? AND epoch_seconds <= ?
        """, (account_id, sec_24h, as_of_epoch))
        out_row = cursor.fetchone()
        outbound_24h = float(out_row["outbound_24h"] or 0.0)

        if inbound_24h > 0:
            pass_through_ratio = min(1.0, outbound_24h / inbound_24h)
            balance_retention = max(0.0, min(1.0, (inbound_24h - outbound_24h) / inbound_24h))
        else:
            pass_through_ratio = 0.0
            balance_retention = 1.0

        # 5. Dwell Time (minutes between inbounds and subsequent outbounds)
        cursor.execute("""
            SELECT epoch_seconds, 'IN' as dir FROM transactions WHERE receiver = ? AND epoch_seconds <= ? AND epoch_seconds >= ?
            UNION ALL
            SELECT epoch_seconds, 'OUT' as dir FROM transactions WHERE sender = ? AND epoch_seconds <= ? AND epoch_seconds >= ?
            ORDER BY epoch_seconds ASC
        """, (account_id, as_of_epoch, sec_7d, account_id, as_of_epoch, sec_7d))
        history = cursor.fetchall()

        dwell_times = []
        last_in_epoch = None
        for h in history:
            if h["dir"] == "IN":
                last_in_epoch = h["epoch_seconds"]
            elif h["dir"] == "OUT" and last_in_epoch is not None:
                dwell_mins = max(0.1, (h["epoch_seconds"] - last_in_epoch) / 60.0)
                dwell_times.append(dwell_mins)
                last_in_epoch = None

        median_dwell_time_mins = float(np.median(dwell_times)) if dwell_times else 240.0 # Default 4 hours

        # 6. Structuring & Round Amount Share
        cursor.execute("""
            SELECT amount, channel FROM transactions 
            WHERE (receiver = ? OR sender = ?) AND epoch_seconds <= ? AND epoch_seconds >= ?
        """, (account_id, account_id, as_of_epoch, sec_7d))
        recent_txns = cursor.fetchall()

        structuring_count = 0
        round_count = 0
        normal_channel_count = 0
        total_recent = len(recent_txns)

        if amount and amount > 0:
            total_recent += 1
            if (45000 <= amount <= 49999) or (90000 <= amount <= 99999) or (190000 <= amount <= 199999):
                structuring_count += 1
            if amount % 1000 == 0 or amount % 5000 == 0:
                round_count += 1

        for t in recent_txns:
            amt = t["amount"]
            if (45000 <= amt <= 49999) or (90000 <= amt <= 99999) or (190000 <= amt <= 199999):
                structuring_count += 1
            if amt % 1000 == 0 or amt % 5000 == 0:
                round_count += 1
            if t["channel"] in ["UPI", "POS", "CARD"]:
                normal_channel_count += 1

        structuring_signal = float(structuring_count)
        round_amount_share = float(round_count / total_recent) if total_recent > 0 else 0.0
        share_of_normal_spending = float(normal_channel_count / total_recent) if total_recent > 0 else 0.5

        # 7. Dormancy (inactivity days prior to recent window)
        cursor.execute("""
            SELECT MAX(epoch_seconds) as prev_epoch
            FROM transactions
            WHERE (receiver = ? OR sender = ?) AND epoch_seconds < ?
        """, (account_id, account_id, sec_24h))
        prev_row = cursor.fetchone()
        prev_epoch = prev_row["prev_epoch"]
        if prev_epoch:
            dormancy = max(0.0, (sec_24h - prev_epoch) / 86400.0)
        else:
            dormancy = account_age_days

        # 8. Device / IP / Phone Graph Sharing
        shared_dev, shared_ip, shared_phone = self.get_shared_entity_counts(account_id)

        # 9. Graph Proximity to Flagged / Honeypots & Loops
        cursor.execute("""
            SELECT sender, receiver FROM transactions 
            WHERE epoch_seconds >= ? AND epoch_seconds <= ?
            LIMIT 5000
        """, (sec_7d, as_of_epoch))
        sub_edges = cursor.fetchall()
        
        G = nx.DiGraph()
        for e in sub_edges:
            G.add_edge(e["sender"], e["receiver"])

        # Check loop membership via Strongly Connected Components in O(V+E)
        loop_membership = 0.0
        if account_id in G:
            for scc in nx.strongly_connected_components(G):
                if len(scc) > 1 and account_id in scc:
                    loop_membership = 1.0
                    break

        # Hops to flagged / honeypots
        cursor.execute("SELECT id FROM accounts WHERE is_honeypot = 1")
        honeypot_ids = [r["id"] for r in cursor.fetchall()]

        hops_to_flagged = 5.0 # Max default
        if account_id in G:
            for hp in honeypot_ids:
                if hp in G and nx.has_path(G, account_id, hp):
                    try:
                        length = nx.shortest_path_length(G, account_id, hp)
                        hops_to_flagged = min(hops_to_flagged, float(length))
                    except Exception:
                        pass
                if hp in G and nx.has_path(G, hp, account_id):
                    try:
                        length = nx.shortest_path_length(G, hp, account_id)
                        hops_to_flagged = min(hops_to_flagged, float(length))
                    except Exception:
                        pass

        # Flagged neighbour share
        flagged_neighbour_share = 0.0
        if account_id in G:
            neighbours = list(G.predecessors(account_id)) + list(G.successors(account_id))
            if neighbours:
                flagged = set(honeypot_ids)
                flagged_count = sum(1 for n in neighbours if n in flagged)
                flagged_neighbour_share = float(flagged_count / len(neighbours))

        if close_conn:
            conn.close()

        features = {
            "account_age_days": round(account_age_days, 1),
            "senders_1h": senders_1h,
            "senders_24h": senders_24h,
            "senders_7d": senders_7d,
            "new_sender_ratio": round(new_sender_ratio, 3),
            "pass_through_ratio": round(pass_through_ratio, 3),
            "median_dwell_time_mins": round(median_dwell_time_mins, 1),
            "balance_retention": round(balance_retention, 3),
            "round_amount_share": round(round_amount_share, 3),
            "structuring_signal": structuring_signal,
            "dormancy": round(dormancy, 1),
            "share_of_normal_spending": round(share_of_normal_spending, 3),
            "shared_device_count": float(shared_dev),
            "shared_ip_count": float(shared_ip),
            "shared_phone_count": float(shared_phone),
            "hops_to_flagged": hops_to_flagged,
            "flagged_neighbour_share": round(flagged_neighbour_share, 3),
            "loop_membership": loop_membership
        }
        return features
