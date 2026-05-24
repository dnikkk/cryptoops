"""On-chain flows between registry wallets (8 nodes)."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from lib.etherscan import fetch_all_for_address
from lib.wallets import all_wallet_entries, address_labels, load_wallets


def _norm(addr: str) -> str:
    return addr.lower()


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
    edge_kind: str  # transfer | safe_exec | signer
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
        for leg in self.legs[:5]:
            lines.append(f"  {leg.tx_hash[:10]}… {leg.amount} {leg.asset}")
        if len(self.legs) > 5:
            lines.append(f"  … +{len(self.legs) - 5} tx")
        return "\n".join(lines)

    @property
    def primary_tx(self) -> str:
        return self.legs[0].tx_hash if self.legs else ""


def registry_addresses() -> set[str]:
    return {_norm(e.address) for e in all_wallet_entries()}


def safe_addresses() -> set[str]:
    return {_norm(s["address"]) for s in load_wallets().get("safes", [])}


def signer_topology_edges() -> list[FlowEdge]:
    """Static Safe → signer links (not from tx)."""
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
    # dedupe by tx_hash + asset + amount
    exists = {
        (l.tx_hash, l.asset, l.amount) for l in bucket[key].legs
    }
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
            if f not in reg or to not in reg or f == to:
                continue
            h = (t.get("hash") or "").lower()
            val = int(t.get("value") or 0)
            fn = (t.get("functionName") or "").lower()
            kind = "safe_exec" if "exec" in fn and to in safes else "transfer"
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
            if f not in reg or to not in reg or f == to:
                continue
            h = (t.get("hash") or "").lower()
            sym = t.get("tokenSymbol") or "?"
            dec = int(t.get("tokenDecimal") or 18)
            _add_leg(
                bucket,
                source=f,
                target=to,
                kind="transfer",
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
    include_signer_links: bool = True,
    refresh: bool = False,
) -> list[FlowEdge]:
    edges = list(_collect_onchain_edges_cached(refresh))
    if include_signer_links:
        edges.extend(signer_topology_edges())
    return edges


def edges_for_wallet(
    wallet: str,
    edges: list[FlowEdge] | None = None,
    *,
    include_signer_links: bool = True,
) -> list[FlowEdge]:
    w = _norm(wallet)
    pool = edges if edges is not None else all_flow_edges(
        include_signer_links=include_signer_links
    )
    return [e for e in pool if e.source == w or e.target == w]


def nodes_for_edges(
    edges: list[FlowEdge],
    *,
    focus: str | None = None,
) -> list[dict[str, Any]]:
    labels = address_labels()
    addrs: set[str] = set()
    for e in edges:
        addrs.add(e.source)
        addrs.add(e.target)
    nodes: list[dict[str, Any]] = []
    for addr in sorted(addrs):
        role = "safe" if addr in safe_addresses() else "eoa"
        nodes.append(
            {
                "id": addr,
                "label": labels.get(addr, f"{addr[:6]}…{addr[-4:]}"),
                "role": role,
                "focused": focus is not None and _norm(focus) == addr,
            }
        )
    return nodes
