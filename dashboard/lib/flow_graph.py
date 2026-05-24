"""PyVis network graph for wallet flow map."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit.components.v1 as components
from pyvis.network import Network

from lib.flow_map import FlowEdge
from lib.wallets import load_wallets


def _norm(addr: str) -> str:
    return addr.lower()


def registry_layout_positions(
    *,
    spread: float = 1.0,
) -> dict[str, tuple[int, int]]:
    """Fixed left-to-right layout: Safe → signers, two clusters side by side."""
    data = load_wallets()
    positions: dict[str, tuple[int, int]] = {}
    cluster_gap = int(980 * spread)
    signer_dx = int(400 * spread)
    row_gap = int(230 * spread)

    for cluster_idx, safe in enumerate(data.get("safes", [])):
        base_x = cluster_idx * cluster_gap
        s_addr = _norm(safe["address"])
        positions[s_addr] = (base_x, 0)

        signers = safe.get("signers", [])
        n = len(signers)
        for i, signer in enumerate(signers):
            y = int((i - (n - 1) / 2) * row_gap)
            positions[_norm(signer["address"])] = (base_x + signer_dx, y)

    return positions


def _graph_options() -> str:
    opts = {
        "nodes": {
            "font": {
                "size": 20,
                "face": "Segoe UI, Arial, sans-serif",
                "color": "#E8EDF5",
                "strokeWidth": 0,
            },
            "margin": 14,
            "borderWidth": 2,
        },
        "edges": {
            "font": {
                "size": 15,
                "face": "Segoe UI, Arial, sans-serif",
                "color": "#D0DAEB",
                "strokeWidth": 0,
                "align": "horizontal",
            },
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.75}},
            "smooth": {
                "enabled": True,
                "type": "curvedCW",
                "roundness": 0.12,
            },
        },
        "physics": {"enabled": False},
        "interaction": {
            "hover": True,
            "tooltipDelay": 120,
            "zoomView": True,
            "dragView": True,
            "dragNodes": True,
        },
        "layout": {"improvedLayout": False},
    }
    return json.dumps(opts)


def _layout_for_nodes(nodes: list[dict]) -> dict[str, tuple[int, int]]:
    spread = 1.45 if len(nodes) <= 5 else (1.2 if len(nodes) <= 7 else 1.0)
    full = registry_layout_positions(spread=spread)
    visible = {n["id"] for n in nodes}
    return {k: v for k, v in full.items() if k in visible}


def render_flow_graph(
    nodes: list[dict],
    edges: list[FlowEdge],
    *,
    height: int = 960,
) -> None:
    layout = _layout_for_nodes(nodes)
    zoom_boost = 1.18 if len(nodes) <= 5 else (1.08 if len(nodes) <= 7 else 1.0)

    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#0B1220",
        font_color="#E8EDF5",
        directed=True,
        notebook=False,
    )
    net.set_options(_graph_options())

    for n in nodes:
        nid = n["id"]
        is_safe = n["role"] == "safe"
        color = "#63b3ed" if is_safe else "#3DDC97"
        focused = bool(n.get("focused"))
        size = 52 if focused else 44
        border = "#FFD700" if focused else "#1a2744"
        shape = "box" if is_safe else "ellipse"

        x, y = layout.get(nid, (0, 0))

        net.add_node(
            nid,
            label=n["label"],
            title=f"{n['label']}\n{nid}",
            color=color,
            shape=shape,
            x=x,
            y=y,
            fixed=False,
            borderWidth=4 if focused else 2,
            borderWidthSelected=5,
            borderColor=border,
            size=size,
            font={"size": 24 if focused else 22, "color": "#E8EDF5"},
        )

    for e in edges:
        color = "#6B7A94" if e.edge_kind == "signer" else "#B8C4D8"
        width = 2 if e.edge_kind == "signer" else 3
        dashes = e.edge_kind == "signer"
        if e.edge_kind == "signer":
            edge_label = ""
        else:
            edge_label = e.label if len(e.label) <= 18 else f"{e.label[:15]}…"
        net.add_edge(
            e.source,
            e.target,
            title=e.title,
            label=edge_label,
            color=color,
            width=width,
            dashes=dashes,
        )

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "flow.html"
        net.save_graph(str(html_path))
        html = html_path.read_text(encoding="utf-8")

    fit_script = f"""
<script>
(function fitFlowGraph() {{
  var zoomBoost = {zoom_boost};
  function tryFit() {{
    if (typeof network !== "undefined" && network) {{
      var ids = network.body.data.nodes.getIds();
      network.fit({{
        nodes: ids,
        animation: {{ duration: 350, easingFunction: "easeInOutQuad" }},
      }});
      setTimeout(function() {{
        var s = network.getScale();
        network.moveTo({{
          scale: Math.min(s * zoomBoost, 1.85),
          animation: {{ duration: 280 }},
        }});
      }}, 380);
      return;
    }}
    setTimeout(tryFit, 80);
  }}
  if (document.readyState === "complete") tryFit();
  else window.addEventListener("load", tryFit);
}})();
</script>
"""
    html = html.replace("</body>", fit_script + "\n</body>")

    components.html(html, height=height + 48, scrolling=False)
