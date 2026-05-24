from __future__ import annotations

import os
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from web3 import Web3

from lib.config import ENV_FILE, EXPLORER_BASE, NO_PRICE
from lib.etherscan import fetch_account_action
from lib.prices import fetch_symbol_prices_usd, format_usd, price_for_symbol, value_usd
from lib.wallets import address_labels

load_dotenv(ENV_FILE)

ERC20_BALANCE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

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


def _human(raw: int, decimals: int) -> tuple[str, float]:
    if decimals <= 0:
        v = float(raw)
        s = str(raw)
    else:
        v = raw / (10**decimals)
        s = f"{v:.8f}".rstrip("0").rstrip(".") or "0"
    return s, v


def _w3() -> Web3 | None:
    rpc = os.getenv("SEPOLIA_RPC_URL", "").strip()
    if not rpc:
        return None
    try:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
        if w3.is_connected():
            return w3
    except Exception:
        pass
    return None


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
    w3 = _w3()
    tokens = discover_tokens_from_tokentx(address)
    rows: list[dict[str, Any]] = []
    market_prices = fetch_symbol_prices_usd()

    if w3:
        eth_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
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

    for _contract, meta in tokens.items():
        balance_str = "0"
        balance_num = 0.0
        if w3:
            try:
                c = w3.eth.contract(
                    address=Web3.to_checksum_address(meta["contract"]),
                    abi=ERC20_BALANCE_ABI,
                )
                raw = c.functions.balanceOf(
                    Web3.to_checksum_address(address)
                ).call()
                dec = meta["decimals"]
                try:
                    dec = c.functions.decimals().call()
                except Exception:
                    pass
                sym = meta["symbol"]
                try:
                    sym = c.functions.symbol().call()
                except Exception:
                    pass
                balance_str, balance_num = _human(raw, dec)
                meta["symbol"] = sym
                meta["decimals"] = dec
            except Exception:
                balance_str = "—"
                balance_num = 0.0
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

    priced = [r["_value_usd_num"] for r in rows if r["_value_usd_num"] is not None]
    total_num = sum(priced) if priced else None

    for r in rows:
        del r["_value_usd_num"]

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
