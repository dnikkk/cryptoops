from __future__ import annotations

import re
from typing import Any

import yaml

from lib.campaigns import merkle_claim_contracts, seed_tx_classifications, token_contracts
from lib.config import PROTOCOL_FILE
from lib.wallets import address_labels

_METHOD_PATTERNS: list[tuple[str, str, str]] = [
    (r"claim", "Claim", "MerkleClaim"),
    (r"bridge|crosschain|layerzero|stargate|across", "Swap", "Bridge"),
    (r"swap|exactinput|exactoutput|uniswap", "Swap", "Uniswap"),
    (r"addliquidity|removeliquidity|mint.*liquidity|decreaseLiquidity|increaseLiquidity", "LP", "Uniswap"),
    (r"supply|deposit|withdraw|borrow|repay", "Deposit", "Aave"),
    (r"transfer", "Transfer", "ERC20"),
    (r"approve", "Transfer", "ERC20"),
    (r"create", "Deploy", "Contract"),
]

_CATEGORY_TO_TYPE: dict[str, str] = {
    "Claim": "claim",
    "Swap": "swap",
    "LP": "lp",
    "Deposit": "deposit",
    "Transfer": "transfer",
    "Deploy": "deploy",
    "Gas": "gas",
    "Other": "other",
}

# Метки для особых deploy-транзакций
_SPECIAL_TYPE_OVERRIDES: dict[str, str] = {
    "create safe proxy": "safe-create",
    "gnosis safe wallet deployment": "safe-create",
}


def _norm(addr: str) -> str:
    return addr.lower()


def _load_protocol_addrs() -> dict[str, str]:
    if not PROTOCOL_FILE.exists():
        return {}
    with open(PROTOCOL_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k: _norm(v) for k, v in data.items() if isinstance(v, str) and v.startswith("0x")}


def protocol_for_address(addr: str) -> str | None:
    n = _norm(addr)
    for name, contract in _load_protocol_addrs().items():
        if contract == n:
            return name.replace("_", " ").title()
    return None


def analyze_tx_legs(
    wallet: str,
    token_legs: list[dict[str, Any]],
    nft_legs: list[dict[str, Any]],
) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Уточнение типа по ERC20/NFT legs (важно для Safe: outer tx = execTransaction).
    Returns: category, protocol, detail_notes, direction (In/Out/—).
    """
    w = _norm(wallet)
    if not token_legs and not nft_legs:
        return None, None, None, None

    if nft_legs:
        return "LP", "Uniswap", "NFT / LP position", "—"

    out_syms: list[str] = []
    in_syms: list[str] = []
    cpty: set[str] = set()

    for leg in token_legs:
        f, t = _norm(leg.get("from", "")), _norm(leg.get("to", ""))
        sym = (leg.get("tokenSymbol") or "?").strip()
        if f == w:
            out_syms.append(sym)
            if t != w:
                cpty.add(t)
        if t == w:
            in_syms.append(sym)
            if f != w:
                cpty.add(f)

    def _proto_for_counterparties() -> str:
        for addr in cpty:
            p = protocol_for_address(addr)
            if p:
                return p
        return "Uniswap"

    for addr in cpty:
        p = protocol_for_address(addr)
        if p and "aave" in p.lower():
            if out_syms and not in_syms:
                return "Deposit", p, f"Supply {' '.join(out_syms)}", "Out"
            if in_syms and not out_syms:
                return "Deposit", p, f"Withdraw {' '.join(in_syms)}", "In"

    if out_syms and in_syms:
        proto = _proto_for_counterparties()
        detail = f"{' + '.join(out_syms)} → {' + '.join(in_syms)}"
        return "Swap", proto, detail, "—"

    if out_syms and not in_syms:
        return (
            "Transfer",
            _proto_for_counterparties(),
            f"Send {' + '.join(out_syms)}",
            "Out",
        )
    if in_syms and not out_syms:
        return (
            "Transfer",
            _proto_for_counterparties(),
            f"Receive {' + '.join(in_syms)}",
            "In",
        )

    return None, None, None, None


def classify_transaction(
    tx: dict[str, Any],
    *,
    wallet_address: str,
) -> tuple[str, str, str]:
    """
    Returns (category, protocol, notes).
    """
    tx_hash = (tx.get("hash") or "").lower()
    seeds = seed_tx_classifications()
    if tx_hash in seeds:
        s = seeds[tx_hash]
        return s["category"], _protocol_from_tx(tx), s.get("notes", "")

    to_addr = _norm(tx.get("to") or "")
    fn = (tx.get("functionName") or tx.get("methodId") or "").lower()
    is_error = tx.get("isError") == "1" or tx.get("txreceipt_status") == "0"

    if tx.get("txreceipt_status") == "0" or tx.get("isError") == "1":
        pass  # still classify type

    if to_addr in merkle_claim_contracts() or "claim(" in fn:
        return "Claim", "MerkleClaim", "Merkle airdrop claim"

    if tx.get("contractAddress") and tx.get("contractAddress") != "":
        return "Deploy", "Contract", "Contract deployment"

    proto_by_to = protocol_for_address(to_addr)
    if proto_by_to:
        cat = _category_from_method(fn, default="Swap")
        return cat, proto_by_to, fn or ""

    for pattern, category, protocol in _METHOD_PATTERNS:
        if re.search(pattern, fn, re.I):
            return category, protocol, fn or category

    value = int(tx.get("value") or 0)
    if value > 0 and to_addr:
        return "Transfer", "Native", "ETH transfer"

    gas_used = int(tx.get("gasUsed") or 0)
    if gas_used > 0 and not to_addr:
        return "Gas", "Network", "Gas"

    return "Other", protocol_for_address(to_addr) or "—", fn or "On-chain call"


def _category_from_method(fn: str, default: str = "Other") -> str:
    for pattern, category, _ in _METHOD_PATTERNS:
        if re.search(pattern, fn, re.I):
            return category
    return default


def _protocol_from_tx(tx: dict[str, Any]) -> str:
    to_addr = tx.get("to") or ""
    p = protocol_for_address(to_addr)
    if p:
        return p
    if _norm(to_addr) in merkle_claim_contracts():
        return "MerkleClaim"
    return "—"


def label_address(addr: str) -> str:
    if not addr:
        return "—"
    labels = address_labels()
    return labels.get(_norm(addr), f"{addr[:6]}…{addr[-4:]}")


def direction_for_leg(
    *,
    wallet: str,
    from_addr: str,
    to_addr: str,
) -> str:
    w = _norm(wallet)
    f = _norm(from_addr)
    t = _norm(to_addr)
    if f == w and t != w:
        return "Out"
    if t == w and f != w:
        return "In"
    if f == w and t == w:
        return "—"
    return "—"


def token_symbol(contract: str, fallback: str = "?") -> str:
    tokens = token_contracts()
    info = tokens.get(_norm(contract))
    if info:
        return info["symbol"]
    return fallback


def transaction_type_label(
    category: str,
    method: str = "",
    *,
    protocol: str = "",
    leg_type: str | None = None,
    detail: str = "",
) -> str:
    """Короткое имя операции для префикса […] в notes."""
    fn = (method or "").lower()
    proto = (protocol or "").lower()
    detail_l = (detail or "").lower()

    if leg_type == "transfer":
        return "transfer"
    if leg_type == "internal":
        return "internal"
    if leg_type == "nft":
        return "lp"

    for key, label in _SPECIAL_TYPE_OVERRIDES.items():
        if key in fn or key in detail_l:
            return label

    if category in _CATEGORY_TO_TYPE and category not in ("Other", "Swap", "Deposit"):
        return _CATEGORY_TO_TYPE[category]

    if re.search(r"bridge|crosschain|layerzero|stargate", fn + proto):
        return "bridge"
    if re.search(r"\bapprove\b", fn):
        return "approve"
    if category == "Deposit":
        if "withdraw" in fn:
            return "withdraw"
        if "borrow" in fn:
            return "borrow"
        if "repay" in fn:
            return "repay"
        if "supply" in fn or "deposit" in fn:
            return "deposit"
    if category == "Swap" and re.search(r"swap|exact", fn):
        return "swap"
    if category == "LP":
        if "remove" in fn:
            return "lp-remove"
        if "add" in fn or "mint" in fn:
            return "lp-add"
        return "lp"

    if "exectransaction" in fn.replace(" ", ""):
        return "safe-exec"

    return _CATEGORY_TO_TYPE.get(category, category.lower() if category else "other")


def format_notes(
    category: str,
    detail: str,
    method: str = "",
    *,
    protocol: str = "",
    leg_type: str | None = None,
) -> str:
    """Notes с префиксом [тип] — swap, claim, bridge, …"""
    label = transaction_type_label(
        category, method, protocol=protocol, leg_type=leg_type, detail=detail
    )
    detail = (detail or "").strip()
    detail = re.sub(r"^\[[^\]]+\]\s*", "", detail)
    if detail:
        return f"[{label}] {detail}"
    return f"[{label}]"
