from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import streamlit as st

from lib.config import EXPLORER_BASE
from lib.styles import role_badge
from lib.wallets import load_wallets, wallet_role


def _norm(addr: str) -> str:
    return addr.lower()


def _short(addr: str) -> str:
    return f"{addr[:6]}…{addr[-4:]}"


def init_session_state() -> None:
    defaults = {
        "wallet_address": "0x435A0e13cA88b467C3371E78418fAeaB5721a8d1",
        "wallet_label": "Safe #1",
        "date_from": date.today() - timedelta(days=365),
        "date_to": date.today(),
        "refresh_data": False,  # не True — лишний трафик Etherscan на каждый визит
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _select_wallet(address: str, label: str) -> None:
    if _norm(st.session_state.wallet_address) != _norm(address):
        st.session_state.wallet_address = address
        st.session_state.wallet_label = label
        st.rerun()


def _safe_button(address: str, label: str, *, key_suffix: str) -> None:
    active = _norm(st.session_state.wallet_address) == _norm(address)
    marker = "● " if active else ""
    text = f"{marker}{label}  {_short(address)}"
    if st.sidebar.button(
        text,
        key=f"wallet_pick_{key_suffix}",
        width="stretch",
        type="primary",
    ):
        _select_wallet(address, label)


def _signer_button(address: str, label: str, *, key_suffix: str) -> None:
    active = _norm(st.session_state.wallet_address) == _norm(address)
    marker = "● " if active else ""
    text = f"{marker}└ {label}  {_short(address)}"
    if st.sidebar.button(
        text,
        key=f"wallet_pick_{key_suffix}",
        width="stretch",
        type="secondary",
    ):
        _select_wallet(address, label)


def _render_safe_block(safe: dict) -> None:
    label = safe["label"]
    addr = safe["address"]
    safe_key = _norm(addr)[:10]
    st.sidebar.markdown(f"**{label}**")
    _safe_button(addr, label, key_suffix=f"{safe_key}_safe")
    for i, signer in enumerate(safe.get("signers", [])):
        _signer_button(
            signer["address"],
            signer["label"],
            key_suffix=f"{safe_key}_signer_{i}",
        )
    st.sidebar.markdown("")


def render_wallet_sidebar_tree() -> str:
    """Сеть → период → активный → выбор Safe/подписантов."""
    init_session_state()
    data = load_wallets()

    st.sidebar.markdown("### Сеть")
    st.sidebar.caption("Sepolia")

    st.sidebar.markdown("### Период")
    c1, c2 = st.sidebar.columns(2)
    with c1:
        st.session_state.date_from = st.date_input(
            "С", value=st.session_state.date_from, key="dds_date_from"
        )
    with c2:
        st.session_state.date_to = st.date_input(
            "По", value=st.session_state.date_to, key="dds_date_to"
        )

    st.session_state.refresh_data = st.sidebar.toggle(
        "Обновить кэш Etherscan",
        value=False,
        key="dds_refresh_toggle",
        help="По умолчанию данные из локального кэша (быстрее, меньше запросов API). "
        "Включите после новой tx в Sepolia, если её нет в таблице.",
    )
    if st.session_state.refresh_data:
        st.sidebar.caption("Следующая загрузка ДДС подтянет свежие данные с Etherscan.")
    else:
        st.sidebar.caption("Используется локальный кэш · авто-обновление ~5 мин на вкладке ДДС.")

    addr = st.session_state.wallet_address
    role = wallet_role(addr)
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**Активный:** {st.session_state.wallet_label} · `{_short(addr)}` {role_badge(role)}",
        unsafe_allow_html=True,
    )
    st.sidebar.link_button(
        "Etherscan",
        f"{EXPLORER_BASE}/address/{addr}",
        width="stretch",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Сменить кошелёк")
    for safe in data.get("safes", []):
        _render_safe_block(safe)

    return addr


def filter_df_by_date(df, date_col: str = "datetime"):
    if df is None or df.empty:
        return df
    dfrom = st.session_state.date_from
    dto = st.session_state.date_to

    def parse_dt(s):
        if not isinstance(s, str) or not s:
            return None
        try:
            return datetime.strptime(s.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None

    ts = df[date_col].apply(parse_dt)
    mask = ts.apply(lambda t: t is not None and dfrom <= t.date() <= dto)
    return df[mask].reset_index(drop=True)
