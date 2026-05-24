"""Flow map graph — Streamlit custom component (vis-network)."""

from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

from lib.flow_map import FlowEdge, layout_positions_for_nodes

_COMPONENT_DIR = Path(__file__).resolve().parent.parent / "components" / "flow_graph"
_flow_graph_component = components.declare_component(
    "flow_graph",
    path=str(_COMPONENT_DIR),
)


def _edge_label_parts(edge: FlowEdge) -> tuple[str, int]:
    """Label text and font size on edge."""
    if edge.edge_kind == "signer" or not edge.legs:
        return "", 20
    if len(edge.legs) > 1:
        return f"{len(edge.legs)} tx", 22
    leg = edge.legs[0]
    text = f"{leg.amount} {leg.asset}"
    if len(text) > 22:
        text = f"{text[:19]}…"
    return text, 20


def _serialize_edges(
    edges: list[FlowEdge],
    *,
    selected_edge_id: str,
) -> list[dict]:
    """Parallel edges between same pair get alternating curves and roundness."""
    pair_idx: dict[tuple[str, str], int] = {}
    out: list[dict] = []
    selected = (selected_edge_id or "").strip()

    for e in edges:
        key = (e.source, e.target)
        idx = pair_idx.get(key, 0)
        pair_idx[key] = idx + 1
        curve = "curvedCW" if idx % 2 == 0 else "curvedCCW"
        roundness = 0.38 + idx * 0.14
        label, label_size = _edge_label_parts(e)
        out.append(
            {
                "id": e.edge_id,
                "from": e.source,
                "to": e.target,
                "kind": e.edge_kind,
                "label": label,
                "labelSize": label_size,
                "title": e.title,
                "curve": curve,
                "roundness": min(roundness, 0.82),
                "selected": e.edge_id == selected,
            }
        )
    return out


def render_flow_graph(
    nodes: list[dict],
    edges: list[FlowEdge],
    *,
    focus_wallet: str | None = None,
    selected_edge_id: str | None = None,
    height: int = 920,
) -> str | None:
    """
    Render graph; return clicked edge_id (or None).
    Scale is fixed from container width; zoom disabled.
    """
    layout = layout_positions_for_nodes(nodes, focus=focus_wallet)
    ys = [layout[n["id"]][1] for n in nodes if n["id"] in layout]
    anchor_y = sum(ys) / len(ys) if ys else 0

    vis_nodes = []
    for n in nodes:
        nid = n["id"]
        x, y = layout.get(nid, (0, 0))
        vis_nodes.append(
            {
                "id": nid,
                "label": n["label"],
                "title": f"{n['label']}\n{nid}",
                "role": n["role"],
                "focused": bool(n.get("focused")),
                "x": x,
                "y": y,
            }
        )

    clicked = _flow_graph_component(
        nodes=vis_nodes,
        edges=_serialize_edges(edges, selected_edge_id=selected_edge_id or ""),
        selectedEdgeId=(selected_edge_id or "").strip(),
        anchorY=anchor_y,
        height=height,
        key="flow_graph_network",
        default=None,
    )
    if clicked is None or clicked == "":
        return None
    return str(clicked)
