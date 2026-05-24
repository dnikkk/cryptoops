import streamlit as st

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
  letter-spacing: -0.02em;
  font-weight: 700 !important;
}

.treasury-hero {
  background: linear-gradient(135deg, #0f1a2e 0%, #162544 50%, #0d2818 100%);
  border: 1px solid rgba(61, 220, 151, 0.25);
  border-radius: 16px;
  padding: 1.5rem 1.75rem;
  margin-bottom: 1.25rem;
}

.treasury-hero h1 {
  margin: 0 0 0.35rem 0;
  font-size: 1.75rem;
  color: #E8EDF5;
}

.treasury-hero p {
  margin: 0;
  color: #9BA8C0;
  font-size: 0.95rem;
}

.badge-safe {
  display: inline-block;
  background: rgba(99, 179, 237, 0.15);
  color: #63b3ed;
  border: 1px solid rgba(99, 179, 237, 0.4);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.badge-eoa {
  display: inline-block;
  background: rgba(61, 220, 151, 0.12);
  color: #3DDC97;
  border: 1px solid rgba(61, 220, 151, 0.35);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.signer-tree {
  font-size: 0.82rem;
  color: #8B9BB4;
  margin-left: 0.5rem;
  line-height: 1.5;
  font-family: 'JetBrains Mono', monospace;
}

div[data-testid="stSidebar"] {
  border-right: 1px solid rgba(61, 220, 151, 0.12);
}

.kpi-card {
  background: #141E33;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255,255,255,0.06);
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="treasury-hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def role_badge(role: str) -> str:
    if role == "Safe":
        return '<span class="badge-safe">Safe</span>'
    return '<span class="badge-eoa">EOA</span>'
