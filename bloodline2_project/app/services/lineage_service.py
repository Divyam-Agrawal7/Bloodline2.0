from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
from app.db.store import BloodlineDatastore
from app.models.schemas import LineageResponse, LineageNode, LineageLink, TimelineStep

class LineageService:
    def __init__(self, store: Optional[BloodlineDatastore] = None):
        self.store = store or BloodlineDatastore.get_instance()

    def build_money_dna(
        self,
        origin_txn_id: str,
        time_window_hours: int = 72,
        max_hops: int = 4,
        proportional_decay: bool = True
    ) -> LineageResponse:
        origin_txn = self.store.transactions.get(origin_txn_id)
        if not origin_txn:
            # Fallback if txn not found: pick first tainted or default
            for t in self.store.transactions.values():
                if t.get("is_tainted"):
                    origin_txn = t
                    origin_txn_id = t["transaction_id"]
                    break

        if not origin_txn:
            return LineageResponse(
                origin_transaction_id=origin_txn_id,
                origin_amount=0.0,
                currency="USD",
                time_window_hours=time_window_hours,
                nodes=[],
                links=[],
                timeline_steps=[],
                total_tainted_tracked=0.0,
                total_frozen=0.0,
                total_exited=0.0
            )

        origin_amount = float(origin_txn["amount"])
        origin_sender = origin_txn["sender_account_id"]
        origin_receiver = origin_txn["receiver_account_id"]
        origin_time_str = origin_txn["timestamp"]
        if isinstance(origin_time_str, datetime):
            origin_time = origin_time_str
        else:
            try:
                origin_time = datetime.fromisoformat(origin_time_str.replace("Z", "+00:00"))
            except Exception:
                origin_time = datetime.now(timezone.utc) - timedelta(hours=12)

        cutoff_time = origin_time + timedelta(hours=time_window_hours)

        nodes_dict: Dict[str, LineageNode] = {}
        links_list: List[LineageLink] = []
        timeline_events: List[Dict[str, Any]] = []

        # Hop 0: Origin Sender
        sender_acc = self.store.accounts.get(origin_sender, {})
        nodes_dict[origin_sender] = LineageNode(
            id=origin_sender,
            account_id=origin_sender,
            account_label=sender_acc.get("pseudonymous_label", origin_sender),
            hop_layer=0,
            tainted_amount_received=origin_amount,
            total_inflow=origin_amount,
            frozen_status=(sender_acc.get("status") in ["FROZEN", "RESTRICTED"]),
            mule_score=sender_acc.get("mule_score", 0.05)
        )

        # Hop 1: Origin Receiver
        receiver_acc = self.store.accounts.get(origin_receiver, {})
        nodes_dict[origin_receiver] = LineageNode(
            id=origin_receiver,
            account_id=origin_receiver,
            account_label=receiver_acc.get("pseudonymous_label", origin_receiver),
            hop_layer=1,
            tainted_amount_received=origin_amount,
            total_inflow=origin_amount,
            frozen_status=(receiver_acc.get("status") in ["FROZEN", "RESTRICTED"]),
            mule_score=receiver_acc.get("mule_score", 0.9)
        )

        # Hop 0 -> 1 Link
        links_list.append(LineageLink(
            source=origin_sender,
            target=origin_receiver,
            tainted_flow_amount=origin_amount,
            actual_transfer_amount=origin_amount,
            timestamp=origin_time.isoformat(),
            transaction_id=origin_txn["transaction_id"],
            hop=1,
            channel=origin_txn.get("channel", "WIRE")
        ))

        timeline_events.append({
            "timestamp": origin_time.isoformat(),
            "txn_id": origin_txn["transaction_id"],
            "amount": origin_amount,
            "desc": f"Origin payment of ${origin_amount:,.2f} initiated from {origin_sender} to aggregator {origin_receiver}."
        })

        # Track tainted balance available at each node: {node_id: tainted_amount}
        tainted_balances = defaultdict(float)
        tainted_balances[origin_receiver] = origin_amount

        # Layer-by-layer forward tracing
        current_layer_accounts = {origin_receiver}
        current_hop = 1

        total_frozen_amount = 0.0
        total_exited_amount = 0.0

        while current_hop < max_hops and current_layer_accounts:
            next_layer_accounts = set()
            current_hop += 1

            for acc_id in current_layer_accounts:
                curr_tainted = tainted_balances[acc_id]
                if curr_tainted <= 0:
                    continue

                # Find downstream transfers from this account after origin_time and <= cutoff_time
                downstream_txns = []
                for tid, txn in self.store.transactions.items():
                    if txn["sender_account_id"] == acc_id and txn["transaction_id"] != origin_txn["transaction_id"]:
                        t_time_str = txn["timestamp"]
                        if isinstance(t_time_str, datetime):
                            t_time = t_time_str
                        else:
                            try:
                                t_time = datetime.fromisoformat(t_time_str.replace("Z", "+00:00"))
                            except Exception:
                                t_time = origin_time + timedelta(minutes=30)
                        
                        if t_time >= origin_time and t_time <= cutoff_time:
                            downstream_txns.append((t_time, txn))

                # Sort by time
                downstream_txns.sort(key=lambda x: x[0])

                if not downstream_txns:
                    # Account didn't forward: either frozen or resting
                    acc_info = self.store.accounts.get(acc_id, {})
                    if acc_info.get("status") in ["FROZEN", "RESTRICTED"]:
                        total_frozen_amount += curr_tainted
                    continue

                total_outflow_subsequent = sum(float(tx[1]["amount"]) for tx in downstream_txns)
                
                # Proportional allocation
                for t_time, txn in downstream_txns:
                    rec_id = txn["receiver_account_id"]
                    tx_amt = float(txn["amount"])

                    # Allocation formula: proportional fraction of tainted pool
                    if total_outflow_subsequent > 0:
                        allocated_ratio = min(1.0, tx_amt / total_outflow_subsequent)
                    else:
                        allocated_ratio = 1.0

                    allocated_tainted = round(curr_tainted * allocated_ratio, 2)
                    if allocated_tainted <= 0:
                        continue

                    # Update recipient in nodes_dict
                    rec_acc = self.store.accounts.get(rec_id, {})
                    is_frozen = (rec_acc.get("status") in ["FROZEN", "RESTRICTED"] or txn.get("status") == "HELD")
                    
                    if rec_id not in nodes_dict:
                        nodes_dict[rec_id] = LineageNode(
                            id=rec_id,
                            account_id=rec_id,
                            account_label=rec_acc.get("pseudonymous_label", rec_id),
                            hop_layer=current_hop,
                            tainted_amount_received=allocated_tainted,
                            total_inflow=tx_amt,
                            frozen_status=is_frozen,
                            mule_score=rec_acc.get("mule_score", 0.8)
                        )
                    else:
                        nodes_dict[rec_id].tainted_amount_received += allocated_tainted
                        nodes_dict[rec_id].total_inflow += tx_amt

                    tainted_balances[rec_id] += allocated_tainted
                    next_layer_accounts.add(rec_id)

                    # Add link
                    links_list.append(LineageLink(
                        source=acc_id,
                        target=rec_id,
                        tainted_flow_amount=allocated_tainted,
                        actual_transfer_amount=tx_amt,
                        timestamp=t_time.isoformat(),
                        transaction_id=txn["transaction_id"],
                        hop=current_hop,
                        channel=txn.get("channel", "FAST_PAY")
                    ))

                    timeline_events.append({
                        "timestamp": t_time.isoformat(),
                        "txn_id": txn["transaction_id"],
                        "amount": allocated_tainted,
                        "desc": f"Hop {current_hop}: Transfer of ${tx_amt:,.2f} (${allocated_tainted:,.2f} tainted) from {acc_id} to {rec_id} via {txn.get('channel')}."
                    })

                    if is_frozen:
                        total_frozen_amount += allocated_tainted
                    elif "EXIT" in rec_id or rec_acc.get("account_type") in ["EXCHANGE_GATEWAY", "ATM"]:
                        total_exited_amount += allocated_tainted

            current_layer_accounts = next_layer_accounts

        # Generate sequential timeline steps for the timeline scrubber
        timeline_steps: List[TimelineStep] = []
        running_tainted = 0.0
        for idx, ev in enumerate(timeline_events):
            running_tainted += ev["amount"]
            timeline_steps.append(TimelineStep(
                step_index=idx + 1,
                timestamp=ev["timestamp"],
                active_transaction_ids=[ev["txn_id"]],
                cumulative_tainted_amount=min(origin_amount, round(running_tainted, 2)),
                exited_or_frozen_amount=round(total_frozen_amount + total_exited_amount, 2),
                description=ev["desc"]
            ))

        total_tracked = sum(n.tainted_amount_received for n in nodes_dict.values() if n.hop_layer == 1)

        return LineageResponse(
            origin_transaction_id=origin_txn_id,
            origin_amount=origin_amount,
            currency=origin_txn.get("currency", "USD"),
            time_window_hours=time_window_hours,
            nodes=list(nodes_dict.values()),
            links=links_list,
            timeline_steps=timeline_steps,
            total_tainted_tracked=round(total_tracked, 2),
            total_frozen=round(total_frozen_amount, 2),
            total_exited=round(total_exited_amount, 2),
            tracing_methodology="Proportional allocation over time window. Estimated lineage is an attribution assumption, not a legal finding."
        )
