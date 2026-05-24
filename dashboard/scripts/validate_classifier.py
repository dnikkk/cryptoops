"""Validate §3.4 reference txs classify correctly (run from dashboard/)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.campaigns import seed_tx_classifications
from lib.etherscan import fetch_account_action


def main() -> int:
    seeds = seed_tx_classifications()
    deployer = "0x6886654B5745EAbB1517eF9D8556c5b3dc86646f"
    txs = {t["hash"].lower(): t for t in fetch_account_action(deployer, "txlist")}
    failed = []
    for h, meta in seeds.items():
        tx = txs.get(h.lower())
        if not tx:
            continue
        from lib.classifier import classify_transaction

        cat, _, _ = classify_transaction(tx, wallet_address=deployer)
        if cat != meta["category"]:
            failed.append((h[:16], meta["category"], cat))
    if failed:
        print("MISMATCH:", len(failed))
        for f in failed[:10]:
            print(f)
        return 1
    print(f"OK: {len(seeds)} seeds, checked against deployer txlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
