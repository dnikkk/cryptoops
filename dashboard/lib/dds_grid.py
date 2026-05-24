"""AG Grid renderer for DDS tables (readability vs st.dataframe)."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_aggrid.shared import GridUpdateMode

from lib.config import EXPLORER_BASE

_MAX_GRID_HEIGHT = 520
_ROW_HEIGHT_PX = 38
_HEADER_HEIGHT_PX = 44

_NOTES_WIDTH = 440
_METHOD_WIDTH = _NOTES_WIDTH

_COL_WIDTHS: dict[str, int] = {
    "datetime": 165,
    "row_level": 72,
    "child_index": 52,
    "category": 88,
    "direction": 72,
    "asset": 120,
    "amount": 100,
    "legs_summary": 300,
    "data_warning": 340,
    "counterparty": 140,
    "protocol": 110,
    "method": _METHOD_WIDTH,
    "status": 72,
    "notes": _NOTES_WIDTH,
    "tx_hash": 118,
    "leg_type": 88,
    "wallet_role": 72,
    "value_usd": 72,
    "value_eur": 72,
    "value_eth": 72,
    "value_btc": 72,
}

_WRAP_COLS = frozenset({"notes", "method", "data_warning", "legs_summary", "counterparty"})

_DISPLAY_ORDER = [
    "datetime",
    "row_level",
    "child_index",
    "category",
    "direction",
    "asset",
    "amount",
    "legs_summary",
    "data_warning",
    "counterparty",
    "protocol",
    "method",
    "status",
    "notes",
    "tx_hash",
    "leg_type",
    "wallet_role",
    "value_usd",
    "value_eth",
]

_ROW_STYLE = JsCode(
    """
function(params) {
    if (params.data.row_level === 'parent') {
        return {
            'backgroundColor': '#1a2744',
            'color': '#E8EDF5',
            'fontWeight': '600',
            'borderBottom': '1px solid rgba(61, 220, 151, 0.2)',
        };
    }
    return {
        'backgroundColor': '#111827',
        'color': '#C5D0E0',
        'borderBottom': '1px solid rgba(255,255,255, 0.04)',
    };
}
"""
)

_STATUS_CELL_STYLE = JsCode(
    """
function(params) {
    const v = params.value || '';
    if (v.indexOf('✗') === 0) {
        return {'color': '#FC8181', 'fontWeight': '600'};
    }
    if (v.indexOf('✓') === 0) {
        return {'color': '#3DDC97', 'fontWeight': '500'};
    }
    if (v.indexOf('⚠') === 0) {
        return {'color': '#F6AD55', 'fontWeight': '500'};
    }
    return null;
}
"""
)


def _prepare_grid_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["tx_link"] = out["tx_hash"].apply(
        lambda h: f"{EXPLORER_BASE}/tx/{h}" if h else ""
    )
    cols = [c for c in _DISPLAY_ORDER if c in out.columns]
    if "tx_link" not in cols:
        cols.append("tx_link")
    return out[cols]


def render_dds_aggrid(df: pd.DataFrame, *, grid_key: str) -> None:
    if df.empty:
        return

    grid_df = _prepare_grid_df(df)
    for col in grid_df.columns:
        grid_df[col] = grid_df[col].fillna("").astype(str)

    gb = GridOptionsBuilder.from_dataframe(grid_df)
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=False,
        wrapText=False,
        autoHeight=False,
        suppressMovable=False,
    )
    gb.configure_grid_options(
        domLayout="normal",
        suppressHorizontalScroll=False,
        alwaysShowHorizontalScroll=True,
        getRowStyle=_ROW_STYLE,
        rowHeight=_ROW_HEIGHT_PX,
        headerHeight=40,
        animateRows=False,
    )

    for col in grid_df.columns:
        width = _COL_WIDTHS.get(col, 100)
        wrap = col in _WRAP_COLS
        cell_style = _STATUS_CELL_STYLE if col == "data_warning" else None
        gb.configure_column(
            col,
            width=width,
            minWidth=width,
            maxWidth=width * 2 if wrap else width,
            wrapText=wrap,
            autoHeight=wrap,
            cellStyle=cell_style,
            hide=col == "tx_link",
        )

    if "tx_hash" in grid_df.columns:
        gb.configure_column(
            "tx_hash",
            headerName="tx",
            width=_COL_WIDTHS["tx_hash"],
            minWidth=_COL_WIDTHS["tx_hash"],
            cellRenderer=JsCode(
                """
                class UrlCellRenderer {
                    init(params) {
                        const link = params.data.tx_link;
                        const hash = params.value || '';
                        const short = hash ? hash.slice(0, 8) + '…' : '';
                        this.eGui = document.createElement('a');
                        this.eGui.innerText = short;
                        this.eGui.href = link || '#';
                        this.eGui.target = '_blank';
                        this.eGui.rel = 'noopener noreferrer';
                        this.eGui.style.color = '#63b3ed';
                        this.eGui.style.textDecoration = 'none';
                    }
                    getGui() { return this.eGui; }
                }
                """
            ),
        )

    grid_options = gb.build()

    custom_css = {
        ".ag-root-wrapper": {
            "border": "1px solid rgba(61, 220, 151, 0.18)",
            "border-radius": "10px",
            "font-family": "'DM Sans', sans-serif",
        },
        ".ag-header": {
            "background-color": "#0f1a2e",
            "color": "#9BA8C0",
            "font-weight": "600",
            "border-bottom": "1px solid rgba(61, 220, 151, 0.25)",
        },
        ".ag-row": {"font-size": "13px"},
        ".ag-cell": {"line-height": "1.35", "padding-top": "6px", "padding-bottom": "6px"},
    }

    grid_height = min(
        _MAX_GRID_HEIGHT,
        _HEADER_HEIGHT_PX + len(grid_df) * _ROW_HEIGHT_PX + 12,
    )

    AgGrid(
        grid_df,
        gridOptions=grid_options,
        theme="balham-dark",
        height=grid_height,
        custom_css=custom_css,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=False,
        key=grid_key,
    )
