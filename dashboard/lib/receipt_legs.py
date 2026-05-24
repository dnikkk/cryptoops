"""ERC-20 Transfer legs from transaction receipt logs (when tokentx is incomplete)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from lib.campaigns import token_contracts
from lib.classifier import token_symbol
from lib.config import CACHE_DIR, CHAIN_ID, ENV_FILE, ETHERSCAN_API
from lib.etherscan import api_key
from dotenv import load_dotenv

load_dotenv(ENV_FILE)

TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)
WETH_DEPOSIT_TOPIC = (
    "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
)
# CoW / Universal Router order indicator (wallet in topics)
_COW_ORDER_TOPIC_PREFIX = "0x01bf7c8b"
RATE_LIMIT_SLEEP = 0.25


def _norm(addr: str) -> str:
    return addr.lower()


def _receipt_cache_path(tx_hash: str) -> Path:
    d = CACHE_DIR / "receipts"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_norm(tx_hash)}.json"


def fetch_tx_receipt(tx_hash: str, *, refresh: bool = False) -> dict[str, Any] | None:
    path = _receipt_cache_path(tx_hash)
    if not refresh and path.exists():
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict) and payload.get("result"):
            return payload["result"]

    params = {
        "chainid": CHAIN_ID,
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": tx_hash,
        "apikey": api_key(),
    }
    time.sleep(RATE_LIMIT_SLEEP)
    resp = requests.get(ETHERSCAN_API, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"result": result, "fetched_at": time.time()}, f, indent=2)
    return result


def _topic_address(topic: str) -> str:
    if not topic or len(topic) < 42:
        return ""
    return "0x" + topic[-40:].lower()


def _token_decimals(contract: str) -> int:
    info = token_contracts().get(_norm(contract))
    if info:
        return int(info.get("decimals", 18))
    return 18


def parse_weth_deposit_logs(
    logs: list[dict[str, Any]],
    *,
    tx_hash: str,
    wallet: str,
) -> list[dict[str, Any]]:
    """WETH wrap: ETH sent to WETH contract → WETH credited to wallet."""
    w = _norm(wallet)
    h = _norm(tx_hash)
    legs: list[dict[str, Any]] = []
    for log in logs:
        topics = log.get("topics") or []
        if len(topics) < 2:
            continue
        if _norm(topics[0]) != WETH_DEPOSIT_TOPIC:
            continue
        dst = _topic_address(topics[1])
        if dst != w:
            continue
        data = log.get("data") or "0x"
        try:
            value = int(data, 16) if data not in ("0x", "") else 0
        except ValueError:
            value = 0
        if value == 0:
            continue
        weth = _norm(log.get("address") or "")
        legs.append(
            {
                "hash": h,
                "from": weth,
                "to": dst,
                "value": str(value),
                "contractAddress": weth,
                "tokenSymbol": "WETH",
                "tokenDecimal": "18",
                "_dds_source": "weth_deposit",
            }
        )
    return legs


def receipt_has_cow_or_limit_order(
    logs: list[dict[str, Any]],
    wallet: str,
) -> bool:
    w = _norm(wallet)
    for log in logs:
        topics = log.get("topics") or []
        if len(topics) < 2:
            continue
        if not _norm(topics[0]).startswith(_COW_ORDER_TOPIC_PREFIX):
            continue
        if _topic_address(topics[1]) == w:
            return True
    return False


def parse_all_receipt_legs(
    logs: list[dict[str, Any]],
    *,
    tx_hash: str,
    wallet: str,
) -> list[dict[str, Any]]:
    erc20 = parse_erc20_transfer_logs(logs, tx_hash=tx_hash, wallet=wallet)
    weth = parse_weth_deposit_logs(logs, tx_hash=tx_hash, wallet=wallet)
    return merge_token_legs(erc20, weth)


def parse_erc20_transfer_logs(
    logs: list[dict[str, Any]],
    *,
    tx_hash: str,
    wallet: str,
) -> list[dict[str, Any]]:
    """Tokentx-compatible leg dicts for transfers involving wallet."""
    w = _norm(wallet)
    h = _norm(tx_hash)
    legs: list[dict[str, Any]] = []
    for log in logs:
        topics = log.get("topics") or []
        if len(topics) < 3:
            continue
        if _norm(topics[0]) != TRANSFER_TOPIC:
            continue
        from_a = _topic_address(topics[1])
        to_a = _topic_address(topics[2])
        if from_a != w and to_a != w:
            continue
        data = log.get("data") or "0x"
        try:
            value = int(data, 16) if data not in ("0x", "") else 0
        except ValueError:
            value = 0
        if value == 0:
            continue
        contract = _norm(log.get("address") or "")
        legs.append(
            {
                "hash": h,
                "from": from_a,
                "to": to_a,
                "value": str(value),
                "contractAddress": contract,
                "tokenSymbol": token_symbol(contract, contract[:10] + "…"),
                "tokenDecimal": str(_token_decimals(contract)),
                "_dds_source": "receipt_log",
            }
        )
    return legs


def _leg_key(leg: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _norm(leg.get("from", "")),
        _norm(leg.get("to", "")),
        _norm(leg.get("contractAddress", "")),
        str(leg.get("value", "")),
    )


def merge_token_legs(
    existing: list[dict[str, Any]],
    from_receipt: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen = {_leg_key(l) for l in existing}
    merged = list(existing)
    for leg in from_receipt:
        k = _leg_key(leg)
        if k not in seen:
            merged.append(leg)
            seen.add(k)
    return merged


def needs_receipt_supplement(
    wallet: str,
    token_legs: list[dict[str, Any]],
    internal_legs: list[dict[str, Any]],
) -> bool:
    """Fetch receipt when internal/value movement exists but ERC20 legs are missing."""
    w = _norm(wallet)
    if token_legs:
        outs = ins = 0
        for leg in token_legs:
            f, t = _norm(leg.get("from", "")), _norm(leg.get("to", ""))
            if f == w:
                outs += 1
            if t == w:
                ins += 1
        if outs > 0 and ins == 0:
            return True
        if ins > 0 and outs == 0 and len(internal_legs) > 0:
            return True
        return False

    for leg in internal_legs:
        f, t = _norm(leg.get("from", "")), _norm(leg.get("to", ""))
        val = int(leg.get("value") or 0)
        if val > 0 and (f == w or t == w):
            return True
    return False


def supplement_token_legs_from_receipt(
    tx_hash: str,
    wallet: str,
    token_legs: list[dict[str, Any]],
    *,
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], bool, list[dict[str, Any]]]:
    """
    Returns (merged legs, receipt_was_fetched, receipt_logs).
    """
    receipt = fetch_tx_receipt(tx_hash, refresh=refresh)
    if not receipt:
        return token_legs, False, []
    logs = receipt.get("logs") or []
    if not isinstance(logs, list):
        return token_legs, True, []
    extra = parse_all_receipt_legs(logs, tx_hash=tx_hash, wallet=wallet)
    return merge_token_legs(token_legs, extra), True, logs
