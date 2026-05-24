"""Secrets: local .env, os.environ, Streamlit Cloud st.secrets."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from lib.config import ENV_FILE

load_dotenv(ENV_FILE)


def get_setting(name: str, *, default: str = "") -> str:
    """ETHERSCAN_API_KEY, SEPOLIA_RPC_URL — из env, Streamlit Secrets или .env."""
    val = os.getenv(name, "").strip()
    if val:
        return val
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()
        # вложенная секция [cryptoops] в secrets.toml
        block = st.secrets.get("cryptoops")
        if block is not None and name in block:
            return str(block[name]).strip()
    except Exception:
        pass
    load_dotenv(ENV_FILE, override=False)
    return os.getenv(name, default).strip()


def require_setting(name: str, *, hint: str) -> str:
    val = get_setting(name)
    if not val:
        raise ValueError(
            f"{name} не задан. {hint} "
            "Локально: cryptoops/.env · Cloud: Streamlit → Settings → Secrets."
        )
    return val
