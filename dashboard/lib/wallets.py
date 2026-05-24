from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import yaml

from lib.config import WALLETS_FILE


@dataclass(frozen=True)
class WalletEntry:
    address: str
    label: str
    role: str  # "safe" | "eoa"


def _norm(addr: str) -> str:
    return addr.lower()


@lru_cache(maxsize=1)
def load_wallets() -> dict[str, Any]:
    with open(WALLETS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def all_wallet_entries() -> list[WalletEntry]:
    data = load_wallets()
    entries: list[WalletEntry] = []
    for safe in data.get("safes", []):
        entries.append(
            WalletEntry(
                address=safe["address"],
                label=safe["label"],
                role="safe",
            )
        )
        for signer in safe.get("signers", []):
            entries.append(
                WalletEntry(
                    address=signer["address"],
                    label=signer["label"],
                    role="eoa",
                )
            )
    return entries


def address_labels() -> dict[str, str]:
    labels: dict[str, str] = {}
    for e in all_wallet_entries():
        labels[_norm(e.address)] = e.label
    return labels


def dds_notes_by_address() -> dict[str, str]:
    """Extra note for ДДС table (e.g. Deployer), keyed by lowercase address."""
    data = load_wallets()
    notes: dict[str, str] = {}
    for safe in data.get("safes", []):
        for signer in safe.get("signers", []):
            note = signer.get("dds_note")
            if note:
                notes[_norm(signer["address"])] = note
    return notes


def wallet_role(address: str) -> str:
    addr = _norm(address)
    for e in all_wallet_entries():
        if _norm(e.address) == addr:
            return "Safe" if e.role == "safe" else "EOA"
    return "EOA"


def safe_signers(safe_address: str) -> list[dict[str, str]]:
    data = load_wallets()
    for safe in data.get("safes", []):
        if _norm(safe["address"]) == _norm(safe_address):
            return safe.get("signers", [])
    return []


def is_safe(address: str) -> bool:
    return wallet_role(address) == "Safe"
