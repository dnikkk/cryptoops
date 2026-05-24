"""On-chain flows: registry wallets + external counterparties."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from lib.etherscan import fetch_all_for_address
from lib.wallets import all_wallet_entries, address_labels, load_wallets


def _norm(addr: str) -> str:
    return (addr or "").lower()


def _short_addr(addr: str) -> str:
    return f"{addr[:6]}…{addr[-4:]}"


@dataclass
class FlowLeg:
    tx_hash: str
    asset: str
    amount: str
    leg_type: str  # eth | erc20 | safe_exec
    direction: str  # Out from source perspective


@dataclass
class FlowEdge:
    source: str
    target: str
    edge_kind: str  # transfer | safe_exec | signer | external
    legs: list[FlowLeg] = field(default_factory=list)

    @property
    def edge_id(self) -> str:
        return f"{_norm(self.source)}->{_norm(self.target)}:{self.edge_kind}"

    @property
    def label(self) -> str:
        if self.edge_kind == "signer":
            return "signer"
        if not self.legs:
            return self.edge_kind
        if len(self.legs) == 1:
            leg = self.legs[0]
            return f"{leg.amount} {leg.asset}"
        return f"{len(self.legs)} tx"

    @property
    def title(self) -> str:
        lines = [f"{self.edge_kind}: {self.label}"]
        for leg in self.legs[:8]:
            lines.append(f"  {leg.tx_hash[:10]}… {leg.amount} {leg.asset}")
        if len(self.legs) > 8:
            lines.append(f"  … +{len(self.legs) - 8} tx")
        return "\n".join(lines)

    @property
    def primary_tx(self) -> str:
        return self.legs[0].tx_hash if self.legs else ""

    def involves_registry(self, registry: set[str]) -> bool:
        return self.source in registry or self.target in registry


def registry_addresses() -> set[str]:
    return {_norm(e.address) for e in all_wallet_entries()}


def safe_addresses() -> set[str]:
    return {_norm(s["address"]) for s in load_wallets().get("safes", [])}


def signer_topology_edges() -> list[FlowEdge]:
    edges: list[FlowEdge] = []
    data = load_wallets()
    for safe in data.get("safes", []):
        s_addr = safe["address"]
        for signer in safe.get("signers", []):
            edges.append(
                FlowEdge(
                    source=_norm(signer["address"]),
                    target=_norm(s_addr),
                    edge_kind="signer",
                    legs=[],
                )
            )
    return edges


def _human_eth(wei: int) -> str:
    if wei <= 0:
        return "0"
    whole = wei / 10**18
    s = f"{whole:.6f}".rstrip("0").rstrip(".")
    return s or "0"


def _human_token(raw: str, decimals: int) -> str:
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return raw or "0"
    if decimals <= 0:
        return str(v)
    whole = v / (10**decimals)
    s = f"{whole:.6f}".rstrip("0").rstrip(".")
    return s or "0"


def _edge_kind_for_eth(
    *,
    source: str,
    target: str,
    registry: set[str],
    safes: set[str],
    function_name: str,
) -> str:
    fn = (function_name or "").lower()
    if "exec" in fn and target in safes and source in registry:
        return "safe_exec"
    if source in registry and target in registry:
        return "transfer"
    return "external"


def _add_leg(
    bucket: dict[tuple[str, str, str], FlowEdge],
    *,
    source: str,
    target: str,
    kind: str,
    leg: FlowLeg,
) -> None:
    key = (_norm(source), _norm(target), kind)
    if key not in bucket:
        bucket[key] = FlowEdge(
            source=_norm(source),
            target=_norm(target),
            edge_kind=kind,
            legs=[],
        )
    exists = {(l.tx_hash, l.asset, l.amount) for l in bucket[key].legs}
    if (leg.tx_hash, leg.asset, leg.amount) not in exists:
        bucket[key].legs.append(leg)


def clear_flow_edges_cache() -> None:
    _collect_onchain_edges_cached.cache_clear()


@lru_cache(maxsize=2)
def _collect_onchain_edges_cached(refresh: bool = False) -> tuple[FlowEdge, ...]:
    reg = registry_addresses()
    safes = safe_addresses()
    bucket: dict[tuple[str, str, str], FlowEdge] = {}

    for entry in all_wallet_entries():
        raw = fetch_all_for_address(entry.address, refresh=refresh)
        for t in raw.get("txlist", []):
            f = _norm(t.get("from", ""))
            to = _norm(t.get("to") or "")
            if not f or not to or f == to:
                continue
            if f not in reg and to not in reg:
                continue
            h = (t.get("hash") or "").lower()
            val = int(t.get("value") or 0)
            kind = _edge_kind_for_eth(
                source=f,
                target=to,
                registry=reg,
                safes=safes,
                function_name=t.get("functionName") or "",
            )
            _add_leg(
                bucket,
                source=f,
                target=to,
                kind=kind,
                leg=FlowLeg(
                    tx_hash=h,
                    asset="ETH",
                    amount=_human_eth(val),
                    leg_type="eth",
                    direction="Out",
                ),
            )

        for t in raw.get("tokentx", []):
            f = _norm(t.get("from", ""))
            to = _norm(t.get("to") or "")
            if not f or not to or f == to:
                continue
            if f not in reg and to not in reg:
                continue
            h = (t.get("hash") or "").lower()
            sym = t.get("tokenSymbol") or "?"
            dec = int(t.get("tokenDecimal") or 18)
            kind = "transfer" if f in reg and to in reg else "external"
            _add_leg(
                bucket,
                source=f,
                target=to,
                kind=kind,
                leg=FlowLeg(
                    tx_hash=h,
                    asset=sym,
                    amount=_human_token(t.get("value", "0"), dec),
                    leg_type="erc20",
                    direction="Out",
                ),
            )

    return tuple(bucket.values())


def all_flow_edges(
    *,
    include_signer_links: bool = False,
    include_external: bool = True,
    refresh: bool = False,
) -> list[FlowEdge]:
    edges = list(_collect_onchain_edges_cached(refresh))
    if not include_external:
        reg = registry_addresses()
        edges = [e for e in edges if e.source in reg and e.target in reg]
    if include_signer_links:
        edges.extend(signer_topology_edges())
    return edges


def edges_for_wallet(
    wallet: str,
    edges: list[FlowEdge] | None = None,
    *,
    include_signer_links: bool = False,
    include_external: bool = True,
) -> list[FlowEdge]:
    w = _norm(wallet)
    pool = edges if edges is not None else all_flow_edges(
        include_signer_links=include_signer_links,
        include_external=include_external,
    )
    return [e for e in pool if e.source == w or e.target == w]


def node_role(addr: str, registry: set[str] | None = None) -> str:
    reg = registry or registry_addresses()
    a = _norm(addr)
    if a in safe_addresses():
        return "safe"
    if a in reg:
        return "eoa"
    return "external"


def nodes_for_edges(
    edges: list[FlowEdge],
    *,
    focus: str | None = None,
) -> list[dict[str, Any]]:
    labels = address_labels()
    registry = registry_addresses()
    addrs: set[str] = set()
    for e in edges:
        addrs.add(e.source)
        addrs.add(e.target)

    nodes: list[dict[str, Any]] = []
    for addr in sorted(addrs):
        role = node_role(addr, registry)
        if role == "external":
            label = _short_addr(addr)
        else:
            label = labels.get(addr, _short_addr(addr))
        nodes.append(
            {
                "id": addr,
                "label": label,
                "role": role,
                "focused": focus is not None and _norm(focus) == addr,
            }
        )
    return nodes


def registry_layout_positions(
    *,
    spread: float = 1.0,
) -> dict[str, tuple[int, int]]:
    data = load_wallets()
    positions: dict[str, tuple[int, int]] = {}
    cluster_gap = int(980 * spread)
    signer_dx = int(400 * spread)
    row_gap = int(230 * spread)

    for cluster_idx, safe in enumerate(data.get("safes", [])):
        base_x = cluster_idx * cluster_gap
        s_addr = _norm(safe["address"])
        positions[s_addr] = (base_x, 0)
        signers = safe.get("signers", [])
        n = len(signers)
        for i, signer in enumerate(signers):
            y = int((i - (n - 1) / 2) * row_gap)
            positions[_norm(signer["address"])] = (base_x + signer_dx, y)

    return positions


def layout_positions_for_nodes(
    nodes: list[dict[str, Any]],
    *,
    focus: str | None = None,
) -> dict[str, tuple[int, int]]:
    """Registry fixed LR; external nodes on the right arc around focus wallet."""
    reg_layout = registry_layout_positions()
    layout: dict[str, tuple[int, int]] = {}
    externals: list[str] = []

    for n in nodes:
        nid = n["id"]
        if n["role"] == "external":
            externals.append(nid)
        elif nid in reg_layout:
            layout[nid] = reg_layout[nid]

    if not externals:
        return layout

    focus_id = _norm(focus or "")
    anchor = layout.get(focus_id)
    if anchor is None:
        xs = [p[0] for p in layout.values()] or [0]
        ys = [p[1] for p in layout.values()] or [0]
        anchor = (max(xs) + 420, sum(ys) / max(len(ys), 1))

    ax, ay = anchor
    n_ext = len(externals)
    radius = 380 + min(n_ext, 30) * 8
    for i, ext in enumerate(sorted(externals)):
        angle = -math.pi / 2 + (2 * math.pi * i / max(n_ext, 1))
        layout[ext] = (
            int(ax + radius * math.cos(angle)),
            int(ay + radius * 0.55 * math.sin(angle)),
        )

    return layout
