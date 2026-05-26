"""CryptoOps DDS Dashboard — entry point.

Run from cryptoops/dashboard:
  streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from lib.config import GITHUB_REPO, github_doc
from lib.styles import apply_theme, hero
from lib.sidebar import init_session_state, render_wallet_sidebar_tree

st.set_page_config(
    page_title="CryptoOps · О проекте",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_session_state()
render_wallet_sidebar_tree()

hero(
    "CryptoOps Treasury",
    "Операционный дашборд ДДС для Sepolia: Merkle airdrop, Safe, Rabby EOA",
)

st.markdown(
    """
### Что это

**CryptoOps** — монитор **Etherscan (Sepolia)** для учета проведенных сделок и on-chain операций
по выбранным кошелькам.

Для сценария **Claim** были подготовлены 4 airdrop: 2 для кошельков **Rabby** и 2 для
кошельков **Safe**. Затем были выполнены операции claim этих токенов и операции **LP**
через мультсиг.

Приложение также отслеживает все типы операций, которые отображаются во вкладках
страницы **ДДС**.

### Источники данных

**Источник данных для ДДС** — **Etherscan API v2** (`ETHERSCAN_API_KEY` в `cryptoops/.env`):
история on-chain операций, internal tx, ERC20 и NFT по выбранным адресам на Sepolia.

**Для работы приложения дополнительно используются:**

- Локальный кэш: `dashboard/cache/{address}/`
- `campaigns/*/deploy.json` — служебные данные из репозитория для классификатора claim / deploy
- **RPC** (`SEPOLIA_RPC_URL`) — текущие балансы на странице «Балансы»

Рыночные цены testnet-токенов **недоступны** — в колонках USD/EUR/ETH/BTC отображается **—**.

### Навигация

Разделы приложения:

1. **О проекте** — этот экран  
2. **ДДС** — движения по кошельку (вкладки + плоская таблица, `row_level`)  
3. **Карта графов** — связи кошельков и контрагентов (on-chain)  
4. **Балансы** — текущие токены и оценка USD (не ДДС)  
5. **SLA** — цели видимости операций в ДДС

### Кампании Merkle (завершены)

| ID | Получатель |
|----|------------|
| `eftihia-sepolia-001` | 3 EOA профиля A |
| `eftemonia-sepolia-002` | 3 EOA профиля A |
| `eftihia-safe-sepolia-003` | Safe #1 |
| `eftemonia-safe-sepolia-004` | Safe #2 |
"""
)

# st.markdown("### Документация")
# st.markdown(f"Репозиторий: [{GITHUB_REPO}]({GITHUB_REPO})")

# docs = [
#     ("Playbook (README)", github_doc("README.md")),
#     ("Runbook (кампании 001–004)", github_doc("RUNBOOK.md")),
#     ("Кампании", github_doc("campaigns/README.md")),
#     ("Дашборд", github_doc("dashboard/README.md")),
#     ("Foundry setup", github_doc("FOUNDRY.md")),
#     ("Спецификация ДДС", github_doc(".cursor/prompts/streamlit-dds-dashboard.md")),
# ]
# cols = st.columns(2)
# for i, (title, url) in enumerate(docs):
#     with cols[i % 2]:
#         st.link_button(title, url, width="stretch")

with st.expander("Реестр Safe (кратко)"):
    st.markdown(
        """
**Safe #1** — Rabby-A #1, #2 (Deployer), #3

**Safe #2** — Rabby-B #1, #2, #3
"""
    )
