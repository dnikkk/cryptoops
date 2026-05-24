"""Prefetch Etherscan data for all registry wallets."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.etherscan import fetch_all_for_address
from lib.wallets import all_wallet_entries


def main() -> None:
    for entry in all_wallet_entries():
        print(f"Fetching {entry.label} …")
        fetch_all_for_address(entry.address, refresh=True)
        print(f"  done {entry.address}")
    print("Cache warm complete.")


if __name__ == "__main__":
    main()
