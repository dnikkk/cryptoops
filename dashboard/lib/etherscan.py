from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from lib.config import CACHE_DIR, CHAIN_ID, ETHERSCAN_API
from lib.env_config import require_setting

RATE_LIMIT_SLEEP = 0.25


def _norm(addr: str) -> str:
    return addr.lower()


def api_key() -> str:
    return require_setting(
        "ETHERSCAN_API_KEY",
        hint="Нужен для загрузки транзакций с Etherscan.",
    )


def _cache_path(address: str, action: str) -> Path:
    d = CACHE_DIR / _norm(address)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{action}.json"


def _read_cache(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, dict) and "result" in payload:
        return payload["result"] if isinstance(payload["result"], list) else []
    if isinstance(payload, list):
        return payload
    return []


def _write_cache(path: Path, result: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"result": result, "fetched_at": time.time()}, f, indent=2)


def fetch_account_action(
    address: str,
    action: str,
    *,
    use_cache: bool = True,
    refresh: bool = False,
) -> list[dict[str, Any]]:
    """Etherscan v2 account module: txlist, txlistinternal, tokentx, tokennfttx."""
    path = _cache_path(address, action)
    if use_cache and not refresh and path.exists():
        cached = _read_cache(path)
        if cached is not None:
            return cached

    params = {
        "chainid": CHAIN_ID,
        "module": "account",
        "action": action,
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 10000,
        "sort": "desc",
        "apikey": api_key(),
    }
    time.sleep(RATE_LIMIT_SLEEP)
    resp = requests.get(ETHERSCAN_API, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") == "0" and data.get("message") not in ("No transactions found", "OK"):
        msg = data.get("result", data.get("message", "Unknown API error"))
        if isinstance(msg, str) and "rate limit" in msg.lower():
            raise RuntimeError(f"Etherscan rate limit: {msg}")
        if isinstance(msg, str) and "No transactions" in msg:
            result: list[dict[str, Any]] = []
        else:
            raise RuntimeError(f"Etherscan API: {msg}")

    result = data.get("result", [])
    if isinstance(result, str) or result is None:
        result = []
    if not isinstance(result, list):
        result = []

    _write_cache(path, result)
    return result


def fetch_all_for_address(
    address: str,
    *,
    refresh: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    actions = ("txlist", "txlistinternal", "tokentx", "tokennfttx")
    out: dict[str, list[dict[str, Any]]] = {}
    for action in actions:
        out[action] = fetch_account_action(
            address, action, refresh=refresh
        )
    return out


def fetch_contract_creation(
    address: str,
    *,
    refresh: bool = False,
) -> dict[str, Any] | None:
    """Etherscan: deployer + tx hash создания контракта (Safe proxy)."""
    path = _cache_path(address, "contract_creation")
    if not refresh and path.exists():
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict) and payload.get("result"):
            return payload["result"]

    params = {
        "chainid": CHAIN_ID,
        "module": "contract",
        "action": "getcontractcreation",
        "contractaddresses": address,
        "apikey": api_key(),
    }
    time.sleep(RATE_LIMIT_SLEEP)
    resp = requests.get(ETHERSCAN_API, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("result")
    row: dict[str, Any] | None = None
    if isinstance(result, list) and result:
        row = result[0]
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"result": row, "fetched_at": time.time()}, f, indent=2)
    return row
