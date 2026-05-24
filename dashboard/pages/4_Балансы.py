from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.balances import fetch_balances_dataframe
from lib.sidebar import render_wallet_sidebar_tree
from lib.styles import apply_theme, hero

st.set_page_config(page_title="Балансы", page_icon="◇", layout="wide")
apply_theme()

hero("Балансы", "Текущие токены на адресе · Sepolia · оценка в USD")

wallet = render_wallet_sidebar_tree()

with st.spinner("Чтение балансов и курса ETH…"):
    try:
        df = fetch_balances_dataframe(wallet)
    except Exception as e:
        st.error(f"Не удалось загрузить балансы: {e}")
        st.info(
            "Проверьте `SEPOLIA_RPC_URL` в `.env` или Streamlit Secrets (Settings)."
        )
        st.stop()

total_row = df[df["symbol"] == "TOTAL"]
if not total_row.empty:
    st.metric("Итого USD", total_row.iloc[0]["value_usd"])

st.dataframe(
    df,
    width="stretch",
    hide_index=True,
    column_config={
        "etherscan": st.column_config.LinkColumn("Etherscan", display_text="↗"),
        "contract": st.column_config.TextColumn("Контракт"),
        "balance": st.column_config.TextColumn("Баланс"),
        "price_usd": st.column_config.TextColumn("Цена USD"),
        "value_usd": st.column_config.TextColumn("Стоимость USD"),
    },
)

st.caption(
    "USD: CoinGecko (ETH, WETH, DAI, USDC, …). Учебные токены кампаний (EFTIHIA, EFTEMONIA) — **—**."
)
st.info("Снимок остатков, не ДДС. Движения — на странице «ДДС».")
