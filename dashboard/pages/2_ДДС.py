from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.dds_ui import cached_dds, render_dds_export, render_dds_tabs
from lib.sidebar import filter_df_by_date, render_wallet_sidebar_tree
from lib.wallets import is_safe
from lib.styles import apply_theme, hero

st.set_page_config(page_title="ДДС", page_icon="◇", layout="wide")
apply_theme()

hero("ДДС", "Движение денежных средств · Sepolia · плоская таблица (parent / child)")

wallet = render_wallet_sidebar_tree()

focus_tx = (st.session_state.pop("dds_focus_tx", None) or "").lower().strip()
if focus_tx:
    st.info(
        f"Фокус с карты потоков: tx `{focus_tx[:10]}…{focus_tx[-6:]}` — "
        "в таблице ниже только строки этой операции."
    )

refresh = st.session_state.get("refresh_data", False)
if refresh:
    cached_dds.clear()
    st.session_state.refresh_data = False

try:
    with st.status("Загрузка транзакций Etherscan…", expanded=True) as status:
        df = cached_dds(wallet, refresh)
        status.update(label=f"Готово: {len(df)} строк", state="complete")
except ValueError as e:
    st.error(str(e))
    st.stop()
except RuntimeError as e:
    st.warning(str(e))
    st.stop()
except Exception as e:
    st.error(f"Ошибка загрузки: {e}")
    st.stop()

df = filter_df_by_date(df)
if focus_tx:
    narrowed = df[df["tx_hash"].str.lower() == focus_tx]
    if narrowed.empty:
        st.warning("Tx не найдена в ДДС для этого кошелька/периода — смените адрес или даты.")
    else:
        df = narrowed
if is_safe(wallet):
    filter_hint = (
        "**Safe:** операции, где Safe — получатель `execTransaction` или "
        "участник в ERC20-логах (не `tx.from` подписанта)"
    )
else:
    filter_hint = "**EOA:** исходящие tx (`tx.from` = выбранный адрес)"

st.caption(
    f"Адрес: `{wallet}` · {filter_hint} · период: "
    f"{st.session_state.date_from} — {st.session_state.date_to}"
)
if is_safe(wallet) and df.empty:
    st.warning(
        "Нет операций за период. Попробуйте расширить даты или включить "
        "«Обновить кэш Etherscan». Для личных tx подписанта выберите Rabby-A/B под Safe."
    )

render_dds_export(df)
render_dds_tabs(df)
