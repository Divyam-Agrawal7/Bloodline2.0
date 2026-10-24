import networkx as nx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.db.store import BloodlineDatastore
from app.models.schemas import GraphNode, GraphEdge, NetworkGraphResponse

class GraphService:
    def __init__(self, store: Optional[BloodlineDatastore] = None):
        self.store = store or BloodlineDatastore.get_instance()

    def get_account_network(
        self,
        account_id: str,
        hop_depth: int = 2,
        min_amount: Optional[float] = None,
        edge_types: Optional[List[str]] = None
    ) -> NetworkGraphResponse:
        g = self.store.graph
        if account_id not in g:
            # Return empty or fallback
            return NetworkGraphResponse(
                center_account_id=account_id,
                hop_depth=hop_depth,
                nodes=[],
                edges=[]
            )

        # Extract k-hop ego network
        subgraph_nodes = {account_id}
        current_layer = {account_id}
        for _ in range(hop_depth):
            next_layer = set()
            for node in current_layer:
                # Undirected neighborhood for comprehensive investigative context
                neighbors = set(g.predecessors(node)).union(set(g.successors(node)))
                next_layer.update(neighbors)
            subgraph_nodes.update(next_layer)
            current_layer = next_layer

        nodes_res: List[GraphNode] = []
        edges_res: List[GraphEdge] = []

        for node_id in subgraph_nodes:
            node_attrs = g.nodes[node_id]
            node_type = node_attrs.get("type", "account")
            label = node_attrs.get("label", node_id)
            risk_score = node_attrs.get("risk_score")
            status = node_attrs.get("status", "ACTIVE")

            # Account info enrichment if available
            acc = self.store.accounts.get(node_id)
            meta = {}
            if acc:
                meta = {
                    "account_type": acc.get("account_type"),
                    "balance": acc.get("balance"),
                    "is_dormant_reactivated": acc.get("is_dormant_reactivated", False),
                    "velocity_in_24h": acc.get("velocity_in_24h", 0),
                    "velocity_out_24h": acc.get("velocity_out_24h", 0),
                }

            nodes_res.append(GraphNode(
                id=node_id,
                label=label,
                type=node_type,
                risk_score=risk_score,
                status=status,
                metadata=meta
            ))

        # Extract edges within subgraph
        subgraph = g.subgraph(subgraph_nodes)
        for u, v, key, data in subgraph.edges(keys=True, data=True):
            e_type = data.get("type", "TRANSFERRED_TO")
            if edge_types and e_type not in edge_types:
                continue

            amount = data.get("amount")
            if min_amount is not None and amount is not None and amount < min_amount:
                continue

            edges_res.append(GraphEdge(
                id=str(key),
                source=u,
                target=v,
                type=e_type,
                amount=amount,
                currency=data.get("currency", "USD"),
                timestamp=data.get("timestamp"),
                channel=data.get("channel"),
                status=data.get("status"),
                is_predicted=data.get("is_predicted", False),
                probability=data.get("probability")
            ))

        return NetworkGraphResponse(
            center_account_id=account_id,
            hop_depth=hop_depth,
            nodes=nodes_res,
            edges=edges_res
        )

    def detect_mule_patterns(self, account_id: str) -> Dict[str, Any]:
        """
        Analyzes fan-in, fan-out, rapid pass-through, structuring, cycles,
        and shared device/IP/phone links for the account.
        """
        g = self.store.graph
        in_txns = []
        out_txns = []

        if account_id in g:
            for u, v, k, data in g.in_edges(account_id, keys=True, data=True):
                if data.get("type") == "TRANSFERRED_TO":
                    in_txns.append(data)
            for u, v, k, data in g.out_edges(account_id, keys=True, data=True):
                if data.get("type") == "TRANSFERRED_TO":
                    out_txns.append(data)

        in_count = len(in_txns)
        out_count = len(out_txns)
        total_inflow = sum(t.get("amount", 0) for t in in_txns)
        total_outflow = sum(t.get("amount", 0) for t in out_txns)

        # 1. Pass-through ratio
        pass_through_ratio = 0.0
        if total_inflow > 0:
            pass_through_ratio = min(round(total_outflow / total_inflow, 3), 1.0)

        # 2. Fan-in / Fan-out
        is_fan_out = (in_count <= 2 and out_count >= 3 and total_outflow >= 0.8 * total_inflow)
        is_fan_in = (in_count >= 3 and out_count <= 1 and total_inflow >= 10000.0)

        # 3. Structuring detection ($9,000 to $9,999)
        structuring_txns = [
            t for t in in_txns + out_txns
            if 9000 <= t.get("amount", 0) < 10000
        ]
        has_structuring = len(structuring_txns) >= 2

        # 4. Cycles detection
        has_cycle = False
        try:
            # Check cycles in transfer graph
            transfer_subgraph = nx.DiGraph()
            for u, v, k, data in g.edges(keys=True, data=True):
                if data.get("type") == "TRANSFERRED_TO":
                    transfer_subgraph.add_edge(u, v)
            if account_id in transfer_subgraph:
                cycles = list(nx.simple_cycles(transfer_subgraph))
                for cycle in cycles:
                    if account_id in cycle and len(cycle) >= 3:
                        has_cycle = True
                        break
        except Exception:
            has_cycle = False

        # 5. Shared entity links
        shared_devices = []
        shared_ips = []
        shared_phones = []

        if account_id in g:
            for neighbor in g.successors(account_id):
                n_type = g.nodes[neighbor].get("type")
                if n_type == "device":
                    shared_devices.append(neighbor)
                elif n_type == "ip":
                    shared_ips.append(neighbor)
                elif n_type == "phone":
                    shared_phones.append(neighbor)

        # 6. Dormant account flag
        acc = self.store.accounts.get(account_id, {})
        is_dormant_reactivated = acc.get("is_dormant_reactivated", False)

        return {
            "account_id": account_id,
            "in_count": in_count,
            "out_count": out_count,
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "pass_through_ratio": pass_through_ratio,
            "is_fan_out": is_fan_out,
            "is_fan_in": is_fan_in,
            "has_structuring": has_structuring,
            "has_cycle": has_cycle,
            "is_dormant_reactivated": is_dormant_reactivated,
            "shared_devices": shared_devices,
            "shared_ips": shared_ips,
            "shared_phones": shared_phones
        }
