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
    "Время от подтверждения транзакции в Sepolia до появления в таблице ДДС: "
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
    "После новой on-chain операции дождитесь целевого SLA по типу операции "
    "или включите «Обновить кэш Etherscan» в боковой панели."
)

with st.expander("Заметки для ППП (политики, процедуры, процессы)"):
    st.markdown(
        """
**1. Финальный подписант Safe**

- Единый финальный подписант упрощает навигацию при чтении ДДС.

**2. Суть `parent` / `child`**

- `parent` — основная транзакция.
- `child` — отдельный leg внутри транзакции.

**3. Указатель `[...]` в колонке `notes`**

- `[claim]` — claim
- `[swap]` — swap
- `[lp]` — LP
- `[lp-add]` — add liquidity
- `[lp-remove]` — remove liquidity
- `[deposit]` — deposit / supply
- `[withdraw]` — withdraw
- `[borrow]` — borrow
- `[repay]` — repay
- `[transfer]` — transfer
- `[internal]` — internal tx
- `[approve]` — approve
- `[bridge]` — bridge
- `[deploy]` — deploy
- `[safe-create]` — Safe creation
- `[safe-exec]` — Safe execution
- `[gas]` — gas
- `[other]` — other

**4. Колонка `data_warning`**

- `✗` — on-chain success без движения средств; операция трактуется как reject / no-op.
- `⚠` — по данным Etherscan операция прочитана не полностью или требует дополнительной проверки.
- `✓` — входящие и исходящие строки согласованы; операция прочитана корректно.

**5. Временные метрики и эскалация**

- Для каждой операции может рассчитываться среднее время исполнения.
- При превышении допустимого интервала операция подлежит эскалации.
- Счётчик `past time from tx` используется для контроля фактического времени с момента транзакции.
"""
    )

with st.expander("Собственный airdrop / claim: учебный сценарий Merkle"):
    st.markdown(
        """
Краткая схема собственного airdrop на Sepolia — `cryptoops/README.md`, `campaigns/`.

1. Whitelist (CSV) → snapshot адресов и сумм  
2. Merkle tree → `merkleRoot` + `proof.json` на каждый адрес  
3. Deploy токена + контракта **MerkleClaim**  
4. Fund claim-контракта токенами  
5. Раздача proof получателям  
6. **Claim** on-chain (`claim(proof)`)  
7. Сверка: Etherscan + вкладка **Claim** в ДДС  

**Проверки для claim**

- `hasClaimed(address) = false`  
- proof из `proof.json` для адреса  
- правильный кошелёк (EOA / Safe / Rabby)  
- tx success + Transfer event  
- баланс получателя += amount  

**Контроль после claim**

- строка Claim в ДДС (SLA или обновление кэша)  
- остаток на MerkleClaim ≈ 0  
- `deploy.json` / реестр обновлён  
- tx hashes в учёте  
- повторный claim → `Already claimed`  
"""
    )
