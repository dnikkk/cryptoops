from __future__ import annotations

import time

import requests
import streamlit as st

from lib.config import NO_PRICE

COINGECKO_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"

# Символ → CoinGecko id (оценка testnet-токенов с тем же ticker)
SYMBOL_TO_COINGECKO: dict[str, str] = {
    "ETH": "ethereum",
    "WETH": "weth",
    "DAI": "dai",
    "USDC": "usd-coin",
    "USDT": "tether",
    "GNO": "gnosis",
    "WBTC": "wrapped-bitcoin",
}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_symbol_prices_usd() -> dict[str, float]:
    """Курсы USD для известных символов."""
    ids = ",".join(sorted(set(SYMBOL_TO_COINGECKO.values())))
    id_to_symbol = {v: k for k, v in SYMBOL_TO_COINGECKO.items()}
    try:
        time.sleep(0.2)
        r = requests.get(
            COINGECKO_SIMPLE,
            params={"ids": ids, "vs_currencies": "usd"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        out: dict[str, float] = {}
        for cg_id, row in data.items():
            sym = id_to_symbol.get(cg_id)
            if sym and "usd" in row:
                out[sym] = float(row["usd"])
        return out
    except Exception:
        return {}


def price_for_symbol(symbol: str, prices: dict[str, float]) -> float | None:
    return prices.get(symbol.upper())


def format_usd(value: float | None) -> str:
    if value is None:
        return NO_PRICE
    return f"${value:,.2f}"


def value_usd(balance: float, price: float | None) -> float | None:
    if price is None:
        return None
    return balance * price
