"""Minimal Sepolia JSON-RPC (no web3 — avoids typing_extensions / pydantic conflicts)."""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

from lib.config import ENV_FILE

load_dotenv(ENV_FILE)

_BALANCE_OF = "0x70a08231"  # balanceOf(address)


def rpc_url() -> str:
    return os.getenv("SEPOLIA_RPC_URL", "").strip()


def _call(method: str, params: list[Any]) -> Any:
    url = rpc_url()
    if not url:
        raise RuntimeError("SEPOLIA_RPC_URL не задан в cryptoops/.env")
    resp = requests.post(
        url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("error"):
        err = body["error"]
        msg = err.get("message", err) if isinstance(err, dict) else err
        raise RuntimeError(f"RPC error: {msg}")
    return body["result"]


def is_rpc_available() -> bool:
    if not rpc_url():
        return False
    try:
        _call("eth_chainId", [])
        return True
    except Exception:
        return False


def eth_get_balance(address: str) -> int:
    raw = _call("eth_getBalance", [address, "latest"])
    return int(raw, 16)


def erc20_balance_of(contract: str, holder: str) -> int:
    holder_hex = holder.lower().removeprefix("0x").zfill(64)
    data = _BALANCE_OF + holder_hex
    raw = _call(
        "eth_call",
        [{"to": contract, "data": data}, "latest"],
    )
    if not raw or raw == "0x":
        return 0
    return int(raw, 16)
