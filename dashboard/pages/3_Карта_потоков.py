from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.flow_graph import render_flow_graph
from lib.flow_map import FlowEdge, all_flow_edges, edges_for_wallet, nodes_for_edges
from lib.sidebar import render_wallet_sidebar_tree
from lib.styles import apply_theme, hero
from lib.wallets import address_labels, wallet_role

st.set_page_config(page_title="Карта потоков", page_icon="◇", layout="wide")
apply_theme()


def _format_edge_option(edge: FlowEdge, labels: dict[str, str]) -> str:
    a = labels.get(edge.source, edge.source[:8])
    b = labels.get(edge.target, edge.target[:8])
    return f"{a} → {b} · {edge.label} ({edge.edge_kind})"


def _wallet_for_dds(edge: FlowEdge, current: str) -> str:
    cur = current.lower()
    if cur == edge.source or cur == edge.target:
        return current
    return edge.source if edge.edge_kind != "signer" else current


hero(
    "Карта потоков",
    "Связи между вашими 8 адресами · on-chain tx + Safe↔signer",
)

wallet = render_wallet_sidebar_tree()
labels = address_labels()
role = wallet_role(wallet)

refresh = st.session_state.get("refresh_data", False)
if refresh:
    st.session_state.refresh_data = False

show_all = st.sidebar.checkbox(
    "Показать все 8 узлов",
    value=False,
    help="Иначе только связи выбранного адреса и его соседей.",
)

if show_all:
    edges = all_flow_edges(include_signer_links=True, refresh=refresh)
    st.caption(
        f"Полный граф реестра · выбран в sidebar: "
        f"**{labels.get(wallet.lower(), wallet[:10])}** ({role})"
    )
else:
    edges = edges_for_wallet(
        wallet,
        all_flow_edges(include_signer_links=True, refresh=refresh),
    )
    st.caption(
        f"Связи для **{labels.get(wallet.lower(), wallet[:10])}** ({role}) · "
        f"{len(edges)} рёбер · только адреса из wallets.yaml"
    )

nodes = nodes_for_edges(edges, focus=wallet)

if not edges:
    st.info(
        "Нет связей между адресами реестра за кэшированный период. "
        "Расширьте даты или обновите кэш Etherscan на вкладке ДДС."
    )
    st.stop()

st.markdown(
    "Граф выровнен **слева направо**: Safe → подписанты (два кластера). "
    "Колёсико — zoom, перетаскивание — сдвиг. "
    "**Наведение** на ребро — суммы и tx; **выбор связи** ниже → **Открыть в ДДС**."
)

try:
    render_flow_graph(nodes, edges)
except ImportError:
    st.error("Установите pyvis: pip install pyvis")
    st.stop()

st.markdown("---")
st.subheader("Перейти в ДДС по связи")

edge_options = {e.edge_id: e for e in edges if e.legs}
if not edge_options:
    st.caption(
        "On-chain рёбра с tx — после переводов между вашими адресами. "
        "Пунктир signer — топология Safe (без tx)."
    )
    edge_options = {e.edge_id: e for e in edges}

picked_id = st.selectbox(
    "Связь (from → to)",
    options=list(edge_options.keys()),
    format_func=lambda eid: _format_edge_option(edge_options[eid], labels),
)

picked = edge_options[picked_id]
focus_tx = ""
focus_wallet = wallet

if picked.legs:
    leg_by_hash = {leg.tx_hash: leg for leg in picked.legs}
    tx_pick = st.selectbox(
        "Tx hash (если несколько на одном ребре)",
        options=list(leg_by_hash.keys()),
        format_func=lambda h: (
            f"{h[:10]}… {leg_by_hash[h].amount} {leg_by_hash[h].asset}"
        ),
    )
    focus_tx = tx_pick
    focus_wallet = _wallet_for_dds(picked, wallet)
else:
    st.caption("У выбранного ребра нет on-chain tx (например связь signer).")

col1, col2 = st.columns(2)
with col1:
    if st.button("Открыть в ДДС", type="primary", disabled=not focus_tx):
        st.session_state.wallet_address = focus_wallet
        st.session_state.wallet_label = labels.get(
            focus_wallet.lower(), focus_wallet[:10]
        )
        st.session_state.dds_focus_tx = focus_tx.lower()
        st.switch_page("pages/2_ДДС.py")
with col2:
    if focus_tx:
        st.link_button(
            "Etherscan tx",
            f"https://sepolia.etherscan.io/tx/{focus_tx}",
            width="stretch",
        )
