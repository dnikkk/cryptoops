from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from lib.sidebar import render_wallet_sidebar_tree
from lib.sla_dds import (
    DDS_VISIBILITY_TARGETS,
    cache_age_minutes,
    estimate_cache_lag_minutes,
)
from lib.styles import apply_theme, hero

st.set_page_config(page_title="SLA", page_icon="◇", layout="wide")
apply_theme()

hero("SLA", "Видимость on-chain операций в ДДС · Sepolia")

wallet = render_wallet_sidebar_tree()

st.markdown("### SLA видимости в ДДС")
st.caption(
    "Время от подтверждения tx в Sepolia до появления в таблице ДДС: "
    "индексация Etherscan + локальный кэш + (опционально) «Обновить кэш»."
)

lag = estimate_cache_lag_minutes(wallet)
cache_age = cache_age_minutes(wallet)
c1, c2 = st.columns(2)
with c1:
    if lag is not None:
        st.metric(
            "Оценка отставания кэша",
            f"{lag:.0f} мин",
            help="fetched_at − timeStamp последней tx",
        )
    else:
        st.metric("Оценка отставания кэша", "—")
with c2:
    if cache_age is not None:
        st.metric("Возраст кэша txlist", f"{cache_age:.0f} мин")
    else:
        st.metric("Возраст кэша txlist", "—")

sla_df = pd.DataFrame(DDS_VISIBILITY_TARGETS)
sla_df = sla_df.rename(
    columns={
        "category": "Операция",
        "target_minutes": "SLA (мин), цель",
        "note": "Комментарий",
    }
)
st.dataframe(sla_df, width="stretch", hide_index=True)

st.info(
    "После новой on-chain операции подождите SLA по типу или включите "
    "«Обновить кэш Etherscan» в sidebar."
)

with st.expander("Own airdrop / claim sandbox (учебный Merkle-дроп)"):
    st.markdown(
        """
Краткий путь своего дропа на Sepolia — `cryptoops/README.md`, `campaigns/`.

1. Whitelist (CSV) → snapshot адресов и сумм  
2. Merkle tree → `merkleRoot` + `proof.json` на каждый адрес  
3. Deploy токена + контракта **MerkleClaim**  
4. Fund claim-контракта токенами  
5. Раздача proof получателям  
6. **Claim** on-chain (`claim(proof)`)  
7. Сверка: Etherscan + вкладка **Claim** в ДДС  

**Execution (claim)** — чеклист при тесте песочницы:

- `hasClaimed(address) = false`  
- proof из `proof.json` для адреса  
- правильный кошелёк (EOA / Safe / Rabby)  
- tx success + Transfer event  
- баланс получателя += amount  

**Post-flight** — после claim:

- строка Claim в ДДС (SLA или обновление кэша)  
- остаток на MerkleClaim ≈ 0  
- `deploy.json` / реестр обновлён  
- tx hashes в учёте  
- повторный claim → `Already claimed`  
"""
    )
