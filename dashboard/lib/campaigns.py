from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from lib.config import CAMPAIGNS_DIR


def _norm(addr: str) -> str:
    return addr.lower()


@lru_cache(maxsize=1)
def load_all_campaigns() -> list[dict[str, Any]]:
    campaigns: list[dict[str, Any]] = []
    for path in sorted(CAMPAIGNS_DIR.glob("*/deploy.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["_path"] = str(path)
        campaigns.append(data)
    return campaigns


def merkle_claim_contracts() -> set[str]:
    addrs: set[str] = set()
    for c in load_all_campaigns():
        claim = c.get("merkleClaim", {}).get("contract")
        if claim:
            addrs.add(_norm(claim))
    return addrs


def token_contracts() -> dict[str, dict[str, Any]]:
    """contract address -> {symbol, decimals, campaignId}"""
    out: dict[str, dict[str, Any]] = {}
    for c in load_all_campaigns():
        tok = c.get("token", {})
        contract = tok.get("contract")
        if contract:
            out[_norm(contract)] = {
                "symbol": tok.get("symbol", "?"),
                "decimals": int(tok.get("decimals", 18)),
                "campaignId": c.get("campaignId", ""),
            }
    return out


def seed_tx_classifications() -> dict[str, dict[str, str]]:
    """Reference tx hashes from spec §3.4 + deploy.json for classifier tests."""
    seeds: dict[str, dict[str, str]] = {
        "0x4e8c211fbfedceef8399137234c60b08091725e5fb269eb87a885cd42fb5baa1": {
            "category": "Deploy",
            "notes": "001 token deploy",
        },
        "0x46b7cf30783c16dae4e8dc384f0d4317135617c02701e29feb8c9c95fcd9de61": {
            "category": "Deploy",
            "notes": "001 claim contract deploy",
        },
        "0x90128029d0f150fabeeb117caf2ca8859cc736a1ccf365e64c115fc1846b67d5": {
            "category": "Transfer",
            "notes": "001 fund claim",
        },
        "0x6d89e25f607f768e1ce7773de6db6e9ca7cf1e12f7e76286ab3b5f7b1b9d6844": {
            "category": "Claim",
            "notes": "001 claim 6886",
        },
        "0x534d917b0ed9ae543e3885b743ed1152456d059d64187e7a9b9a19f6e2834403": {
            "category": "Claim",
            "notes": "001 claim 898E",
        },
        "0x00c55f7eb74bd69e7bfaf42e0975426876b9ca62b9fd97ffa45c0220716c7f9d": {
            "category": "Claim",
            "notes": "001 claim F336",
        },
        "0xf572e9d1a3e0825ba7b2d13dbaac447fae618b61fe761a51d094d0405813edb7": {
            "category": "Deploy",
            "notes": "002 token deploy",
        },
        "0x03143470990f7b895fb5a6ab113613329d9d93e1cfa7185722403f420c1439f1": {
            "category": "Deploy",
            "notes": "002 claim deploy",
        },
        "0x3cf73d4d440204a8b3373375d1263f32b31c984c070129ec9f6caf3d926716b1": {
            "category": "Transfer",
            "notes": "002 fund claim",
        },
        "0xc2bad7ad7e2c70c37fd53835a781f613e43cec45f1e3f33883fce9b725dba5ad": {
            "category": "Claim",
            "notes": "002 claim 6886",
        },
        "0x977ebf9cddc084b11636ae6475a34b01775b72fff5ba9173a6055f3d95b54b91": {
            "category": "Claim",
            "notes": "002 claim 898E",
        },
        "0xafb5ba8093e008a4e26e938d1063924a901bf90c5835e0ad401eae9c1680d41e": {
            "category": "Claim",
            "notes": "002 claim F336",
        },
        "0x6cf77e133ee1432ebd6cde49a5758295433621e8ff920ab8cd5a9cd182d50ddf": {
            "category": "Deploy",
            "notes": "003 token deploy",
        },
        "0xff86889e5aa406785a8f3f626543fb6b8d47085ef121e1bbfcde6c3b61a799be": {
            "category": "Deploy",
            "notes": "003 claim deploy",
        },
        "0xb0d7a367690ebaece6833e85a4d238afd86e40e28b78347c067628e52de0c80a": {
            "category": "Transfer",
            "notes": "003 fund claim",
        },
        "0xf36658c96e51192a4c7f6ccdd8912015a8a023427d6e325dd22a96f5b1e19499": {
            "category": "Claim",
            "notes": "003 claim Safe #1",
        },
        "0xe88b42f88019d59b85224f941d4be667f5073a4141e923a8cb153c44253c61b2": {
            "category": "Deploy",
            "notes": "004 token deploy",
        },
        "0x8de0f0203cb5545f7196df7fe243b74d6c031a31bb11f5a08ec9a0a54e6c4383": {
            "category": "Deploy",
            "notes": "004 claim deploy",
        },
        "0xabdeeb48fc762de5e474a8102b2465dea5920cadda3531848e9836dbaf5d588c": {
            "category": "Transfer",
            "notes": "004 fund claim",
        },
        "0x30820fc07393d943dc2b990d1a590d89281e7971c5965a99074f775794d67a86": {
            "category": "Claim",
            "notes": "004 claim Safe #2",
        },
    }

    for c in load_all_campaigns():
        cid = c.get("campaignId", "")
        tok = c.get("token", {})
        if tok.get("deployTx"):
            h = tok["deployTx"].lower()
            seeds.setdefault(
                h,
                {"category": "Deploy", "notes": f"{cid} token deploy"},
            )
        mc = c.get("merkleClaim", {})
        if mc.get("deployTx"):
            h = mc["deployTx"].lower()
            seeds.setdefault(
                h,
                {"category": "Deploy", "notes": f"{cid} MerkleClaim deploy"},
            )
        if mc.get("fundTx"):
            h = mc["fundTx"].lower()
            seeds.setdefault(
                h,
                {"category": "Transfer", "notes": f"{cid} fund claim"},
            )
        for r in c.get("recipients", []):
            if r.get("claimTx"):
                h = r["claimTx"].lower()
                seeds[h] = {"category": "Claim", "notes": f"{cid} claim"}
    return seeds
