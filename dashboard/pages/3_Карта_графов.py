from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.config import EXPLORER_BASE
from lib.flow_graph import render_flow_graph
from lib.flow_map import (
    FlowEdge,
    all_flow_edges,
    edges_for_wallet,
    node_role,
    nodes_for_edges,
    registry_addresses,
)
from lib.sidebar import render_wallet_sidebar_tree
from lib.styles import apply_theme, hero
from lib.wallets import address_labels, wallet_role

st.set_page_config(page_title="Карта графов", page_icon="◇", layout="wide")
apply_theme()


def _wallet_for_dds(edge: FlowEdge, current: str) -> str:
    reg = registry_addresses()
    cur = current.lower()
    if cur == edge.source or cur == edge.target:
        return current
    if edge.source in reg:
        return edge.source
    if edge.target in reg:
        return edge.target
    return current


def _label_for_addr(addr: str, labels: dict[str, str]) -> str:
    role = node_role(addr)
    if role == "external":
        return f"`{addr[:10]}…{addr[-6:]}` (внешний)"
    return f"**{labels.get(addr, addr[:10])}** ({'Safe' if role == 'safe' else 'EOA'})"


hero(
    "Карта графов",
    "Связи выбранного кошелька: 8 адресов реестра и внешние контрагенты (on-chain)",
)

wallet = render_wallet_sidebar_tree()
labels = address_labels()
role = wallet_role(wallet)

refresh = st.session_state.get("refresh_data", False)
if refresh:
    st.session_state.refresh_data = False

include_external = st.sidebar.checkbox(
    "Внешние адреса (контрагенты)",
    value=True,
)
include_signer = st.sidebar.checkbox(
    "Топология signer → Safe",
    value=False,
)
show_all_registry = st.sidebar.checkbox(
    "Все 8 адресов реестра",
    value=False,
)

pool = all_flow_edges(
    include_signer_links=include_signer,
    include_external=include_external,
    refresh=refresh,
)

if show_all_registry:
    edges = pool
    st.caption(
        f"Полный граф · активный: "
        f"**{labels.get(wallet.lower(), wallet[:10])}** ({role}) · {len(edges)} рёбер"
    )
else:
    edges = edges_for_wallet(
        wallet,
        pool,
        include_signer_links=include_signer,
        include_external=include_external,
    )
    st.caption(
        f"Связи **{labels.get(wallet.lower(), wallet[:10])}** ({role}) · {len(edges)} рёбер"
    )

nodes = nodes_for_edges(edges, focus=wallet)

if not edges:
    st.info(
        "Нет связей за кэшированный период. Расширьте даты или обновите кэш Etherscan."
    )
    st.stop()

onchain = [e for e in edges if e.legs]
ext_count = sum(1 for n in nodes if n["role"] == "external")
edge_options = {e.edge_id: e for e in onchain}

st.markdown(
    f"**{len(onchain)}** on-chain связей · **{ext_count}** внешних узлов. "
    "**Клик по ребру** — детали ниже."
)
st.caption(
    "Синий Safe · зелёный EOA · серый внешний · "
    "зелёное ребро — между адресами реестра · оранжевое — внешний контрагент · "
    "голубое — execTransaction · масштаб — кнопками или вертикальным скролом · перетаскивание включено"
)

clicked_edge = render_flow_graph(
    nodes,
    edges,
    focus_wallet=wallet,
    selected_edge_id=st.session_state.get("flow_pick_edge"),
)

all_edge_ids = {e.edge_id for e in edges}
pick_edge = st.session_state.get("flow_pick_edge", "")
if (
    clicked_edge
    and clicked_edge != pick_edge
    and clicked_edge in all_edge_ids
):
    st.session_state.flow_pick_edge = clicked_edge
    st.rerun()
    pick_edge = clicked_edge

st.markdown("---")
st.subheader("Перейти в ДДС по связи")

if not edge_options:
    st.warning("Нет on-chain связей с транзакциями.")
    st.stop()

if not pick_edge:
    st.info("Выберите **ребро** на графе — ниже появятся детали и переход в ДДС.")
    st.stop()

if pick_edge not in edge_options:
    st.warning(
        "У выбранной связи нет on-chain транзакций "
        "(например, для связи signer → Safe). Выберите другое ребро."
    )
    st.stop()

picked = edge_options[pick_edge]
st.markdown(
    f"**Связь:** {_label_for_addr(picked.source, labels)} → "
    f"{_label_for_addr(picked.target, labels)}"
)
st.caption(f"Тип: `{picked.edge_kind}` · {picked.label}")

focus_wallet = _wallet_for_dds(picked, wallet)
legs = list(picked.legs)
n_legs = len(legs)

st.markdown(f"**Транзакции по связи ({n_legs})**")

def _go_dds(*, tx_hashes: list[str]) -> None:
    st.session_state.wallet_address = focus_wallet
    st.session_state.wallet_label = labels.get(
        focus_wallet.lower(), focus_wallet[:10]
    )
    st.session_state.pop("dds_focus_tx", None)
    if len(tx_hashes) == 1:
        st.session_state.dds_focus_tx = tx_hashes[0].lower()
        st.session_state.pop("dds_focus_txs", None)
    else:
        st.session_state.dds_focus_txs = [h.lower() for h in tx_hashes]
        st.session_state.pop("dds_focus_tx", None)
    st.switch_page("pages/2_ДДС.py")


col_all, col_reset = st.columns([3, 1])
with col_all:
    if st.button(
        "Открыть все транзакции связи в ДДС",
        type="primary",
        disabled=n_legs == 0,
    ):
        _go_dds(tx_hashes=[leg.tx_hash for leg in legs])
with col_reset:
    if st.button("Сбросить выбор"):
        st.session_state.pop("flow_pick_edge", None)
        st.rerun()

for i, leg in enumerate(legs, start=1):
    h = leg.tx_hash.lower()
    c1, c2, c3 = st.columns([5, 1, 1])
    with c1:
        st.markdown(
            f"**{i}.** `{h[:10]}…{h[-6:]}` · **{leg.amount}** {leg.asset} "
            f"· _{leg.leg_type}_"
        )
    with c2:
        st.link_button(
            "↗",
            f"{EXPLORER_BASE}/tx/{h}",
            width="stretch",
            help="Etherscan",
            key=f"flow_ex_{pick_edge}_{i}",
        )
    with c3:
        if st.button("ДДС", key=f"flow_dds_{pick_edge}_{i}", width="stretch"):
            _go_dds(tx_hashes=[h])
