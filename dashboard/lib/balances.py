from __future__ import annotations

from typing import Any

import pandas as pd
from dotenv import load_dotenv

from lib.config import ENV_FILE, EXPLORER_BASE, NO_PRICE
from lib.etherscan import fetch_account_action
from lib.prices import fetch_symbol_prices_usd, format_usd, price_for_symbol, value_usd
from lib.rpc import erc20_balance_of, eth_get_balance, is_rpc_available, rpc_url

load_dotenv(ENV_FILE)

DISPLAY_COLUMNS = [
    "symbol",
    "balance",
    "price_usd",
    "value_usd",
    "contract",
    "decimals",
    "etherscan",
]


def _norm(addr: str) -> str:
    return addr.lower()


def _checksum(addr: str) -> str:
    """0x-prefixed address for RPC (Etherscan checksum not required on Sepolia RPC)."""
    a = addr.strip()
    if not a.startswith("0x"):
        a = "0x" + a
    return a


def _human(raw: int, decimals: int) -> tuple[str, float]:
    if decimals <= 0:
        v = float(raw)
        s = str(raw)
    else:
        v = raw / (10**decimals)
        s = f"{v:.8f}".rstrip("0").rstrip(".") or "0"
    return s, v


def discover_tokens_from_tokentx(address: str) -> dict[str, dict[str, Any]]:
    txs = fetch_account_action(address, "tokentx")
    tokens: dict[str, dict[str, Any]] = {}
    for t in txs:
        contract = _norm(t.get("contractAddress", ""))
        if not contract:
            continue
        if contract not in tokens:
            tokens[contract] = {
                "contract": t.get("contractAddress"),
                "symbol": t.get("tokenSymbol", "?"),
                "decimals": int(t.get("tokenDecimal") or 18),
            }
    return tokens


def _row(
    *,
    symbol: str,
    balance_str: str,
    balance_num: float,
    contract: str,
    decimals: int | str,
    etherscan: str,
    price: float | None,
) -> dict[str, Any]:
    usd = value_usd(balance_num, price)
    return {
        "symbol": symbol,
        "balance": balance_str,
        "price_usd": format_usd(price) if price is not None else NO_PRICE,
        "value_usd": format_usd(usd),
        "_value_usd_num": usd,
        "contract": contract,
        "decimals": decimals,
        "etherscan": etherscan,
    }


def fetch_balances_dataframe(address: str) -> pd.DataFrame:
    addr = _checksum(address)
    rpc_ok = is_rpc_available()
    if not rpc_ok and not rpc_url():
        raise RuntimeError(
            "SEPOLIA_RPC_URL не задан в cryptoops/.env — нужен для чтения балансов."
        )

    tokens = discover_tokens_from_tokentx(address)
    rows: list[dict[str, Any]] = []
    market_prices = fetch_symbol_prices_usd()

    if rpc_ok:
        try:
            eth_wei = eth_get_balance(addr)
            bal_str, bal_num = _human(eth_wei, 18)
            rows.append(
                _row(
                    symbol="ETH",
                    balance_str=bal_str,
                    balance_num=bal_num,
                    contract="—",
                    decimals=18,
                    etherscan=f"{EXPLORER_BASE}/address/{address}",
                    price=price_for_symbol("ETH", market_prices),
                )
            )
        except Exception as exc:
            rows.append(
                {
                    "symbol": "ETH",
                    "balance": f"ошибка RPC: {exc}",
                    "price_usd": NO_PRICE,
                    "value_usd": NO_PRICE,
                    "contract": "—",
                    "decimals": 18,
                    "etherscan": f"{EXPLORER_BASE}/address/{address}",
                    "_value_usd_num": None,
                }
            )

    for _contract, meta in tokens.items():
        balance_str = "0"
        balance_num = 0.0
        if rpc_ok:
            try:
                raw = erc20_balance_of(_checksum(meta["contract"]), addr)
                dec = int(meta["decimals"])
                balance_str, balance_num = _human(raw, dec)
            except Exception:
                balance_str = "—"
                balance_num = 0.0
        else:
            balance_str = "— (нет RPC)"

        sym = str(meta["symbol"])
        token_price = price_for_symbol(sym, market_prices)
        rows.append(
            _row(
                symbol=sym,
                balance_str=balance_str,
                balance_num=balance_num if balance_str != "—" else 0.0,
                contract=meta["contract"],
                decimals=meta["decimals"],
                etherscan=f"{EXPLORER_BASE}/token/{meta['contract']}?a={address}",
                price=token_price,
            )
        )

    if not rows:
        return pd.DataFrame(
            [
                {
                    "symbol": "—",
                    "balance": "нет токенов",
                    "price_usd": NO_PRICE,
                    "value_usd": NO_PRICE,
                    "contract": "—",
                    "decimals": "—",
                    "etherscan": "—",
                }
            ]
        )

    priced = [r["_value_usd_num"] for r in rows if r.get("_value_usd_num") is not None]
    total_num = sum(priced) if priced else None

    for r in rows:
        r.pop("_value_usd_num", None)

    total_row = {
        "symbol": "TOTAL",
        "balance": "—",
        "price_usd": "—",
        "value_usd": format_usd(total_num),
        "contract": "—",
        "decimals": "—",
        "etherscan": "—",
    }
    df = pd.DataFrame(rows + [total_row])
    return df[DISPLAY_COLUMNS]
