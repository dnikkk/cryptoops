from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.config import DDS_COLUMNS
from lib.dds import filter_by_category, filter_by_direction
from lib.dds_grid import render_dds_aggrid


@st.cache_data(ttl=300, show_spinner=False)
def cached_dds(wallet: str, refresh: bool) -> pd.DataFrame:
    from lib.dds import build_dds_dataframe

    return build_dds_dataframe(wallet, refresh=refresh)


def render_dds_export(df: pd.DataFrame) -> None:
    if df.empty:
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Экспорт CSV",
        csv,
        file_name="dds_export.csv",
        mime="text/csv",
        key="dds_csv_export_main",
        width="stretch",
    )


def render_dds_tabs(df: pd.DataFrame) -> None:
    tab_defs: list[tuple[str, str | None, str | None]] = [
        ("Все операции", None, None),
        ("Claim", "category", "Claim"),
        ("Swap", "category", "Swap"),
        ("LP", "category", "LP"),
        ("Deposit", "category", "Deposit"),
        ("Send", "direction", "Out"),
        ("Received", "direction", "In"),
    ]
    tabs = st.tabs([t[0] for t in tab_defs])
    for tab, (label, mode, value) in zip(tabs, tab_defs):
        with tab:
            if mode is None:
                view = df
            elif mode == "category":
                view = filter_by_category(df, value)
            else:
                view = filter_by_direction(df, value or "Out")
            _render_dds_table(view, empty_hint=label, grid_key=f"dds_grid_{label}")


def _render_dds_table(df: pd.DataFrame, *, empty_hint: str | None, grid_key: str) -> None:
    if df.empty:
        hint = empty_hint or "операций"
        st.info(f"Нет данных за выбранный период ({hint}).")
        return

    parents = df[df["row_level"] == "parent"]
    warn_col = parents["data_warning"].astype(str)
    warnings = parents[warn_col.str.startswith("⚠", na=False)]
    ok_marked = parents[warn_col.str.startswith("✓", na=False)]
    rejected = parents[warn_col.str.startswith("✗", na=False)]
    st.caption(
        f"{len(parents)} операций (parent) · {len(df)} строк всего · "
        f"child legs: {len(df) - len(parents)}"
        + (f" · ⚠ внимание: {len(warnings)}" if len(warnings) else "")
        + (f" · ✓ ok: {len(ok_marked)}" if len(ok_marked) else "")
        + (f" · ✗ reject: {len(rejected)}" if len(rejected) else "")
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Операций", len(parents))
    with c2:
        st.metric("Claim", len(parents[parents["category"] == "Claim"]))
    with c3:
        st.metric("Swap", len(parents[parents["category"] == "Swap"]))
    with c4:
        st.metric("LP", len(parents[parents["category"] == "LP"]))
    with c5:
        st.metric("Send", len(parents[parents["direction"] == "Out"]))
    with c6:
        st.metric("Received", len(parents[parents["direction"] == "In"]))

    display = df.copy()
    for col in DDS_COLUMNS:
        if col not in display.columns:
            display[col] = ""

    try:
        render_dds_aggrid(display, grid_key=grid_key)
    except ImportError:
        st.warning("Установите streamlit-aggrid: pip install streamlit-aggrid")
        st.dataframe(display.astype(str), width="stretch", hide_index=True)
