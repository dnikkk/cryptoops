"""SLA: время появления on-chain операции в ДДС (Etherscan index + локальный кэш)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from lib.config import CACHE_DIR

# Целевое время: от подтверждения tx в сети до строки в ДДС (учебный Sepolia).
DDS_VISIBILITY_TARGETS: list[dict[str, Any]] = [
    {
        "category": "Swap",
        "target_minutes": 30,
        "note": "Router/CoW; settlement может быть отдельной tx",
    },
    {
        "category": "Claim",
        "target_minutes": 15,
        "note": "MerkleClaim + ERC20 transfer",
    },
    {
        "category": "Deposit",
        "target_minutes": 30,
        "note": "Aave supply/withdraw",
    },
    {
        "category": "LP",
        "target_minutes": 45,
        "note": "NFT positions, несколько legs",
    },
    {
        "category": "Transfer",
        "target_minutes": 10,
        "note": "ETH/ERC20",
    },
    {
        "category": "Safe reject",
        "target_minutes": 10,
        "note": "execTransaction без движения средств (пустой calldata)",
    },
]


def _norm(addr: str) -> str:
    return addr.lower()


def estimate_cache_lag_minutes(wallet_address: str) -> float | None:
    """
    Грубая оценка: (время последнего fetch кэша) − (timeStamp последней tx в кэше).
    Не заменяет поминутный SLA по категориям, но показывает «отстаём ли мы от сети».
    """
    path = CACHE_DIR / _norm(wallet_address) / "txlist.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    fetched_at = payload.get("fetched_at")
    txs = payload.get("result") or []
    if not fetched_at or not txs:
        return None
    try:
        latest_ts = max(int(t.get("timeStamp") or 0) for t in txs)
    except ValueError:
        return None
    if latest_ts <= 0:
        return None
    return max(0.0, (float(fetched_at) - latest_ts) / 60.0)


def cache_age_minutes(wallet_address: str) -> float | None:
    """Сколько минут назад обновляли txlist кэш."""
    path = CACHE_DIR / _norm(wallet_address) / "txlist.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    fetched_at = payload.get("fetched_at")
    if not fetched_at:
        return None
    return max(0.0, (time.time() - float(fetched_at)) / 60.0)
