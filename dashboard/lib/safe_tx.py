"""Gnosis Safe execTransaction helpers (empty / no-op executions)."""

from __future__ import annotations

from typing import Any

SAFE_MULTISIG_TOPIC = "0x66753cd2356569ee081232e3be8909b950e0a76c1f8460c3a5e3c2be32b11bed"
EXEC_SUCCESS_TOPIC = "0x442e715f626346e8c54381002da614f62bee8d27386535b2521ec8540898556e"
SAFE_RECEIVED_TOPIC = "0x3d0ce9bfc3ed7d6862dbb28b2dea94561fe714a1b4d019aa8af39730d1ad7c3d"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WETH_DEPOSIT_TOPIC = (
    "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
)

# Inner calldata selectors we expect on real DeFi actions inside Safe exec
_ACTION_SELECTORS = (
    "8d80ff0a",  # Universal Router / multicall
    "a9059cbb",  # transfer
    "095ea7b3",  # approve
    "b61d27f6",  # execTransaction nested
    "e8e33700",  # addLiquidity
    "38ed1739",  # swapExactTokensForTokens
)


def _norm(addr: str) -> str:
    return addr.lower()


def safe_exec_has_empty_inner_data(tx: dict[str, Any]) -> bool:
    """True when execTransaction's inner `bytes data` is empty (no DeFi call)."""
    inp = (tx.get("input") or "").lower()
    if not inp.startswith("0x6a761202"):
        return False
    for sel in _ACTION_SELECTORS:
        if sel in inp:
            return False
    hexdata = inp[10:]
    if len(hexdata) < 64 * 6:
        return False
    try:
        # execTransaction ABI: word[2] = offset to inner `bytes data`
        data_offset_word = hexdata[2 * 64 : 3 * 64]
        data_offset = int(data_offset_word, 16) * 2
        if data_offset + 64 > len(hexdata):
            return False
        data_len = int(hexdata[data_offset : data_offset + 64], 16)
        return data_len == 0
    except ValueError:
        return False


def receipt_is_safe_noop_only(logs: list[dict[str, Any]]) -> bool:
    """
    Receipt has only Safe housekeeping logs (no ERC20/WETH movement).
    Matches cancelled/rejected proposals that still mined as execTransaction.
    """
    if not logs:
        return False
    saw_safe_event = False
    for log in logs:
        topics = log.get("topics") or []
        if not topics:
            continue
        t0 = _norm(topics[0])
        if t0 in (TRANSFER_TOPIC, WETH_DEPOSIT_TOPIC):
            return False
        if t0 in (SAFE_MULTISIG_TOPIC, EXEC_SUCCESS_TOPIC, SAFE_RECEIVED_TOPIC):
            saw_safe_event = True
    return saw_safe_event


def is_safe_noop_exec(
    tx: dict[str, Any],
    receipt_logs: list[dict[str, Any]],
    child_rows: list[dict[str, Any]],
) -> bool:
    fn = (tx.get("functionName") or "").lower()
    if "exec" not in fn:
        return False
    if child_rows:
        return False
    if int(tx.get("value") or 0) > 0:
        return False
    if not safe_exec_has_empty_inner_data(tx):
        return False
    if receipt_logs:
        return receipt_is_safe_noop_only(receipt_logs)
    return True
