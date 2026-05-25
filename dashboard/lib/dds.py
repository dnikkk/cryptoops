from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from lib.classifier import (
    analyze_tx_legs,
    classify_transaction,
    direction_for_leg,
    format_notes,
    label_address,
    token_symbol,
)
from lib.config import DDS_COLUMNS, EXPLORER_BASE, NO_PRICE
from lib.etherscan import fetch_all_for_address, fetch_contract_creation
from lib.receipt_legs import (
    fetch_tx_receipt,
    needs_receipt_supplement,
    receipt_has_cow_or_limit_order,
    supplement_token_legs_from_receipt,
)
from lib.safe_tx import is_safe_noop_exec
from lib.wallets import dds_notes_by_address, is_safe, wallet_role


def _with_wallet_tag(notes: str, tag: str) -> str:
    if not tag:
        return notes
    if notes and tag not in notes:
        return f"{tag} · {notes}"
    return tag


def _norm(addr: str) -> str:
    return addr.lower()


def _human_amount(raw: str, decimals: int) -> str:
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return raw or "0"
    if decimals <= 0:
        return str(v)
    whole = v / (10**decimals)
    s = f"{whole:.8f}".rstrip("0").rstrip(".")
    return s or "0"


def _tx_datetime(tx: dict[str, Any]) -> datetime:
    ts = int(tx.get("timeStamp") or 0)
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _status(tx: dict[str, Any]) -> str:
    if tx.get("isError") == "1" or tx.get("txreceipt_status") == "0":
        return "failed"
    return "success"


def _empty_row() -> dict[str, Any]:
    row = {c: "" for c in DDS_COLUMNS}
    row["child_index"] = ""
    return row


def _price_cols() -> dict[str, str]:
    return {
        "value_usd": NO_PRICE,
        "value_eur": NO_PRICE,
        "value_eth": NO_PRICE,
        "value_btc": NO_PRICE,
    }


def _compute_legs_summary(child_rows: list[dict[str, Any]]) -> str:
    outs: list[str] = []
    ins: list[str] = []
    for row in child_rows:
        amt, asset, direction = row.get("amount", ""), row.get("asset", ""), row.get("direction", "")
        if not amt or amt == "—" or not asset or asset == "—":
            continue
        part = f"{amt} {asset}"
        if direction == "Out":
            outs.append(part)
        elif direction == "In":
            ins.append(part)
    if outs and ins:
        return f"Out {' + '.join(outs)} → In {' + '.join(ins)}"
    if outs:
        return f"Out {' + '.join(outs)}"
    if ins:
        return f"In {' + '.join(ins)}"
    return "—"


def _compute_data_warning(
    child_rows: list[dict[str, Any]],
    *,
    receipt_fetched: bool,
    cow_order: bool = False,
    safe_noop: bool = False,
    legs_summary: str = "",
) -> str:
    if safe_noop:
        return (
            "✗ Safe reject / no-op — движение средств отсутствует "
            "(в интерфейсе: отмена; в сети: success, пустой calldata)"
        )
    if not child_rows:
        return "⚠ отсутствуют детализирующие строки"
    has_out = any(r.get("direction") == "Out" for r in child_rows)
    has_in = any(r.get("direction") == "In" for r in child_rows)
    if cow_order and not any(
        r.get("direction") == "In" and r.get("asset") not in ("ETH", "WETH")
        for r in child_rows
    ):
        return (
            "⚠ подписан CoW / лимитный ордер — зачисление токена может быть в другой транзакции"
        )
    if has_out and not has_in:
        suffix = " (логи исполнения проверены)" if receipt_fetched else " — проверьте Etherscan или обновите кэш"
        return f"⚠ зафиксирован Out без In — операция выглядит незавершённой{suffix}"
    if has_out and has_in and legs_summary and "→" in legs_summary:
        return "✓ движение согласовано (Out → In)"
    if has_in and not has_out and len(child_rows) == 1:
        return "✓ одна входящая строка"
    return ""


def _synthetic_parent_from_tokentx(
    leg: dict[str, Any], wallet: str, wallet_address: str
) -> dict[str, Any]:
    w = wallet
    f, t = _norm(leg.get("from", "")), _norm(leg.get("to", ""))
    if f == w:
        from_a, to_a = wallet_address, leg.get("to", "")
    else:
        from_a, to_a = leg.get("from", ""), wallet_address
    return {
        "hash": leg["hash"],
        "timeStamp": leg.get("timeStamp", "0"),
        "from": from_a,
        "to": to_a,
        "functionName": "",
        "isError": "0",
        "txreceipt_status": "1",
        "value": "0",
        "gasUsed": "0",
    }


def _safe_creation_parent(
    wallet_address: str, creation: dict[str, Any]
) -> dict[str, Any]:
    return {
        "hash": creation.get("txHash", ""),
        "timeStamp": creation.get("timestamp", "0"),
        "from": creation.get("contractCreator", ""),
        "to": "",
        "contractAddress": wallet_address,
        "functionName": "create Safe proxy",
        "isError": "0",
        "txreceipt_status": "1",
        "value": "0",
        "gasUsed": "0",
        "_dds_safe_create": True,
    }


def _collect_parent_txs(
    wallet: str,
    wallet_address: str,
    txlist: list[dict[str, Any]],
    tokentx: list[dict[str, Any]],
    *,
    safe_mode: bool,
    refresh: bool = False,
) -> list[dict[str, Any]]:
    """
    Parent tx: любая операция, где кошелёк from или to (входящий ETH, faucet, Safe exec).
    """
    parents_by_hash: dict[str, dict[str, Any]] = {}

    for t in txlist:
        h = (t.get("hash") or "").lower()
        if not h:
            continue
        if _norm(t.get("from", "")) == wallet or _norm(t.get("to", "")) == wallet:
            parents_by_hash[h] = t

    for t in tokentx:
        h = (t.get("hash") or "").lower()
        if not h:
            continue
        if _norm(t.get("from", "")) != wallet and _norm(t.get("to", "")) != wallet:
            continue
        if h in parents_by_hash:
            continue
        parents_by_hash[h] = _synthetic_parent_from_tokentx(t, wallet, wallet_address)

    if safe_mode:
        creation = fetch_contract_creation(wallet_address, refresh=refresh)
        if creation and creation.get("txHash"):
            h = creation["txHash"].lower()
            if h not in parents_by_hash:
                parents_by_hash[h] = _safe_creation_parent(wallet_address, creation)

    return list(parents_by_hash.values())


def _resolve_direction(
    wallet: str,
    from_addr: str,
    to_addr: str,
    value_eth: int,
    leg_dir: str | None,
) -> str:
    if leg_dir:
        return leg_dir
    if _norm(to_addr) == wallet and value_eth > 0:
        return "In"
    if _norm(from_addr) == wallet and value_eth > 0:
        return "Out"
    if _norm(to_addr) == wallet and _norm(from_addr) != wallet:
        return "In"
    if _norm(from_addr) == wallet:
        return "Out"
    return direction_for_leg(wallet=wallet, from_addr=from_addr, to_addr=to_addr)


def _counterparty_for_tx(wallet: str, from_addr: str, to_addr: str) -> str:
    if _norm(to_addr) == wallet:
        return label_address(from_addr)
    return label_address(to_addr)


def _parent_notes(
    tx: dict[str, Any],
    wallet: str,
    base_notes: str,
    *,
    safe_mode: bool,
) -> str:
    if not safe_mode:
        return base_notes
    signer = tx.get("from", "")
    fn = (tx.get("functionName") or "").lower()
    if _norm(tx.get("to", "")) == wallet and "exec" in fn and _norm(signer) != wallet:
        return f"{base_notes} · Safe exec · signer {label_address(signer)}".strip(" ·")
    return base_notes


def build_dds_dataframe(
    wallet_address: str,
    *,
    refresh: bool = False,
) -> pd.DataFrame:
    wallet = _norm(wallet_address)
    raw = fetch_all_for_address(wallet_address, refresh=refresh)
    txlist = raw.get("txlist", [])
    internal = raw.get("txlistinternal", [])
    tokentx = raw.get("tokentx", [])
    nfttx = raw.get("tokennfttx", [])

    safe_mode = is_safe(wallet_address)
    parents = _collect_parent_txs(
        wallet,
        wallet_address,
        txlist,
        tokentx,
        safe_mode=safe_mode,
        refresh=refresh,
    )
    role = wallet_role(wallet_address)
    wallet_tag = dds_notes_by_address().get(wallet, "")

    by_hash_internal: dict[str, list[dict]] = {}
    for t in internal:
        h = (t.get("hash") or "").lower()
        by_hash_internal.setdefault(h, []).append(t)

    by_hash_token: dict[str, list[dict]] = {}
    for t in tokentx:
        h = (t.get("hash") or "").lower()
        by_hash_token.setdefault(h, []).append(t)

    by_hash_nft: dict[str, list[dict]] = {}
    for t in nfttx:
        h = (t.get("hash") or "").lower()
        by_hash_nft.setdefault(h, []).append(t)

    rows: list[dict[str, Any]] = []

    for tx in parents:
        tx_hash = (tx.get("hash") or "").lower()
        dt = _tx_datetime(tx)
        token_legs = list(by_hash_token.get(tx_hash, []))
        internal_legs = list(by_hash_internal.get(tx_hash, []))
        receipt_fetched = False
        receipt_logs: list[dict[str, Any]] = []
        if needs_receipt_supplement(wallet, token_legs, internal_legs):
            token_legs, receipt_fetched, receipt_logs = supplement_token_legs_from_receipt(
                tx_hash,
                wallet,
                token_legs,
                refresh=refresh,
            )
            by_hash_token[tx_hash] = token_legs
        fn_early = (tx.get("functionName") or "").lower()
        if (
            safe_mode
            and "exec" in fn_early
            and not token_legs
            and not internal_legs
            and not receipt_logs
        ):
            receipt = fetch_tx_receipt(tx_hash, refresh=refresh)
            if receipt:
                receipt_logs = receipt.get("logs") or []
                receipt_fetched = True
        cow_order = (
            receipt_has_cow_or_limit_order(receipt_logs, wallet)
            if receipt_logs
            else False
        )
        nft_legs = by_hash_nft.get(tx_hash, [])

        if tx.get("_dds_safe_create"):
            category, protocol, notes = (
                "Deploy",
                "Gnosis Safe",
                "Gnosis Safe wallet deployment",
            )
            leg_cat, leg_proto, leg_detail, leg_dir = None, None, None, None
        else:
            category, protocol, notes = classify_transaction(
                tx, wallet_address=wallet_address
            )
            leg_cat, leg_proto, leg_detail, leg_dir = analyze_tx_legs(
                wallet, token_legs, nft_legs
            )
            if leg_cat and category in ("Other", "Transfer", "Gas"):
                category = leg_cat
                protocol = leg_proto or protocol
                if leg_detail:
                    notes = leg_detail

        if cow_order and category in ("Other", "Transfer"):
            category = "Swap"
            protocol = "CoW / Uniswap"
            notes = "CoW / limit order signed (settlement may be separate tx)"

        from_addr = tx.get("from", "")
        to_addr = tx.get("to") or ""
        value_eth = int(tx.get("value") or 0)

        if (
            not tx.get("_dds_safe_create")
            and _norm(to_addr) == wallet
            and value_eth > 0
            and _norm(from_addr) != wallet
        ):
            category = "Transfer"
            protocol = "Network"
            notes = f"Receive ETH from {label_address(from_addr)}"

        notes = _parent_notes(tx, wallet, notes, safe_mode=safe_mode)
        method = tx.get("functionName") or tx.get("methodId") or ""
        notes = format_notes(category, notes, method, protocol=protocol)
        asset = "ETH" if value_eth else "—"
        amount = _human_amount(str(value_eth), 18) if value_eth else "—"

        if leg_cat == "Swap" and leg_detail and "→" in leg_detail:
            parts = leg_detail.split("→", 1)
            asset = f"{parts[0].strip()}→{parts[1].strip()}"
            amount = "—"

        direction = _resolve_direction(
            wallet, from_addr, to_addr, value_eth, leg_dir
        )

        parent_row = {
            "datetime": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "row_level": "parent",
            "parent_tx_hash": "",
            "child_index": "",
            "leg_type": "tx",
            "tx_hash": tx_hash,
            "category": category,
            "direction": direction,
            "asset": asset,
            "amount": amount,
            "legs_summary": "",
            "data_warning": "",
            "counterparty": _counterparty_for_tx(wallet, from_addr, to_addr),
            "protocol": protocol,
            "method": method,
            "wallet_role": role,
            "status": _status(tx),
            "notes": (
                f"{notes} · {wallet_tag.lower()}" if wallet_tag else notes
            ),
            **_price_cols(),
        }

        child_rows: list[dict[str, Any]] = []
        child_idx = 0
        for leg in token_legs:
            child_idx += 1
            sym = leg.get("tokenSymbol") or token_symbol(
                leg.get("contractAddress", ""), "?"
            )
            dec = int(leg.get("tokenDecimal") or 18)
            src = leg.get("_dds_source", "")
            leg_type = "event" if src == "weth_deposit" else "transfer"
            leg_note = (
                "WETH deposit (wrap)"
                if src == "weth_deposit"
                else f"ERC20 {sym}"
            )
            child_rows.append(
                {
                    "datetime": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "row_level": "child",
                    "parent_tx_hash": tx_hash,
                    "child_index": str(child_idx),
                    "leg_type": leg_type,
                    "tx_hash": tx_hash,
                    "category": category,
                    "direction": direction_for_leg(
                        wallet=wallet,
                        from_addr=leg.get("from", ""),
                        to_addr=leg.get("to", ""),
                    ),
                    "asset": sym,
                    "amount": _human_amount(leg.get("value", "0"), dec),
                    "legs_summary": "",
                    "data_warning": "",
                    "counterparty": label_address(
                        leg.get("to") if _norm(leg.get("from", "")) == wallet else leg.get("from", "")
                    ),
                    "protocol": protocol,
                    "method": "Transfer",
                    "wallet_role": role,
                    "status": _status(tx),
                    "notes": format_notes(
                        category,
                        leg_note,
                        method,
                        protocol=protocol,
                        leg_type=leg_type,
                    ),
                    **_price_cols(),
                }
            )

        for leg in internal_legs:
            child_idx += 1
            val = int(leg.get("value") or 0)
            child_rows.append(
                {
                    "datetime": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "row_level": "child",
                    "parent_tx_hash": tx_hash,
                    "child_index": str(child_idx),
                    "leg_type": "internal",
                    "tx_hash": tx_hash,
                    "category": category,
                    "direction": direction_for_leg(
                        wallet=wallet,
                        from_addr=leg.get("from", ""),
                        to_addr=leg.get("to", ""),
                    ),
                    "asset": "ETH",
                    "amount": _human_amount(str(val), 18),
                    "legs_summary": "",
                    "data_warning": "",
                    "counterparty": label_address(leg.get("to", "")),
                    "protocol": protocol,
                    "method": "Internal",
                    "wallet_role": role,
                    "status": _status(tx),
                    "notes": format_notes(
                        category, "Internal ETH", method, protocol=protocol, leg_type="internal"
                    ),
                    **_price_cols(),
                }
            )

        for leg in by_hash_nft.get(tx_hash, []):
            child_idx += 1
            child_rows.append(
                {
                    "datetime": dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "row_level": "child",
                    "parent_tx_hash": tx_hash,
                    "child_index": str(child_idx),
                    "leg_type": "nft",
                    "tx_hash": tx_hash,
                    "category": "LP",
                    "direction": direction_for_leg(
                        wallet=wallet,
                        from_addr=leg.get("from", ""),
                        to_addr=leg.get("to", ""),
                    ),
                    "asset": leg.get("tokenName") or "NFT",
                    "amount": leg.get("tokenID", "1"),
                    "legs_summary": "",
                    "data_warning": "",
                    "counterparty": label_address(leg.get("to", "")),
                    "protocol": protocol,
                    "method": "NFT",
                    "wallet_role": role,
                    "status": _status(tx),
                    "notes": format_notes(
                        "LP", "NFT position", method, protocol=protocol, leg_type="nft"
                    ),
                    **_price_cols(),
                }
            )

        # Re-classify from supplemented legs (e.g. Safe swap missing in tokentx)
        if token_legs:
            leg_cat, leg_proto, leg_detail, leg_dir = analyze_tx_legs(
                wallet, token_legs, nft_legs
            )
            if leg_cat and parent_row["category"] in ("Other", "Transfer", "Gas"):
                parent_row["category"] = leg_cat
                parent_row["protocol"] = leg_proto or parent_row["protocol"]
                if leg_detail and "→" in leg_detail:
                    parent_row["asset"] = leg_detail.replace(" → ", "→").replace(" + ", "+")
                    parent_row["amount"] = "—"
                if leg_dir:
                    parent_row["direction"] = leg_dir
                for cr in child_rows:
                    if cr.get("leg_type") == "transfer":
                        cr["category"] = leg_cat
                        cr["protocol"] = parent_row["protocol"]

        legs_summary = _compute_legs_summary(child_rows)
        safe_noop = is_safe_noop_exec(tx, receipt_logs, child_rows)
        if safe_noop:
            parent_row["category"] = "Other"
            parent_row["protocol"] = "Gnosis Safe"
            parent_row["direction"] = "—"
            noop_notes = _parent_notes(
                tx,
                wallet,
                "Safe exec без calldata — отмена/reject (on-chain no-op)",
                safe_mode=safe_mode,
            )
            parent_row["notes"] = format_notes(
                "Other", noop_notes, method, protocol="Gnosis Safe"
            )
            legs_summary = "— (без движения)"
        parent_row["legs_summary"] = legs_summary
        parent_row["data_warning"] = _compute_data_warning(
            child_rows,
            receipt_fetched=receipt_fetched,
            cow_order=cow_order,
            safe_noop=safe_noop,
            legs_summary=legs_summary,
        )
        rows.append(parent_row)
        rows.extend(child_rows)

    if not rows:
        return pd.DataFrame(columns=DDS_COLUMNS)

    df = pd.DataFrame(rows)
    for col in DDS_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[DDS_COLUMNS]
    df["child_index"] = df["child_index"].apply(
        lambda x: "" if x == "" or x is None else str(x)
    )
    df["_sort_ts"] = pd.to_datetime(df["datetime"], utc=True, errors="coerce")
    df = df.sort_values(["_sort_ts", "parent_tx_hash", "row_level", "child_index"], ascending=[False, True, True, True])
    df = df.drop(columns=["_sort_ts"])
    return df.reset_index(drop=True)


def filter_by_direction(df: pd.DataFrame, direction: str) -> pd.DataFrame:
    if df.empty:
        return df
    parents = df[df["row_level"] == "parent"]
    matched_hashes = set(
        parents[parents["direction"] == direction]["tx_hash"].tolist()
    )
    if not matched_hashes:
        return df.iloc[0:0]
    mask = (df["row_level"] == "parent") & (df["direction"] == direction)
    mask |= (df["row_level"] == "child") & (df["parent_tx_hash"].isin(matched_hashes))
    return df[mask].reset_index(drop=True)


def filter_by_category(df: pd.DataFrame, category: str | None) -> pd.DataFrame:
    if df.empty or category is None:
        return df
    parents = df[df["row_level"] == "parent"]
    matched_hashes = set(parents[parents["category"] == category]["tx_hash"].tolist())
    if not matched_hashes:
        return df.iloc[0:0]
    mask = (df["row_level"] == "parent") & (df["category"] == category)
    mask |= (df["row_level"] == "child") & (df["parent_tx_hash"].isin(matched_hashes))
    return df[mask].reset_index(drop=True)


def tx_explorer_url(tx_hash: str) -> str:
    return f"{EXPLORER_BASE}/tx/{tx_hash}"
