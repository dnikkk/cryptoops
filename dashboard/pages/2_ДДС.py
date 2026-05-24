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

focus_txs_raw = st.session_state.pop("dds_focus_txs", None)
focus_tx = (st.session_state.pop("dds_focus_tx", None) or "").lower().strip()
focus_txs: set[str] = set()
if focus_txs_raw:
    focus_txs = {str(h).lower().strip() for h in focus_txs_raw if h}
elif focus_tx:
    focus_txs = {focus_tx}

if focus_txs:
    if len(focus_txs) == 1:
        only = next(iter(focus_txs))
        st.info(
            f"Фокус с карты графов: tx `{only[:10]}…{only[-6:]}` — "
            "в таблице только эта операция."
        )
    else:
        st.info(
            f"Фокус с карты графов: **{len(focus_txs)} tx** на выбранном ребре — "
            "в таблице только эти операции."
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
if focus_txs:
    narrowed = df[df["tx_hash"].str.lower().isin(focus_txs)]
    if narrowed.empty:
        st.warning(
            "Tx с ребра не найдены в ДДС для этого кошелька/периода — "
            "смените адрес, расширьте даты или обновите кэш Etherscan."
        )
    else:
        found = narrowed["tx_hash"].str.lower().nunique()
        if found < len(focus_txs):
            st.caption(
                f"В ДДС найдено **{found}** из **{len(focus_txs)}** tx с ребра "
                "(остальные могут быть вне периода или другого кошелька)."
            )
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
