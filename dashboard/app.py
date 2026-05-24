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
    "Операционный дашборд ДДС на Sepolia — Merkle airdrop, Safe, Rabby EOA",
)

st.markdown(
    """
### Что это

**CryptoOps** — учебный контур Merkle airdrop на **Sepolia testnet** (chainId `11155111`):
whitelist → Merkle tree (off-chain) → деплой `TestToken` + `MerkleClaim` → claim получателями.

Этот дашборд отвечает на вопрос: **куда и откуда двинулись средства** по выбранному адресу
(EOA или Gnosis Safe), без опоры на UI Rabby / Safe App / Aave / Uniswap.

### EOA vs Safe

| Режим | Что попадает в ДДС |
|-------|---------------------|
| **EOA** (Rabby) | Исходящие tx: `tx.from` = адрес EOA (claim 001/002, swap с сайта) |
| **Safe** | Операции **кошелька Safe**: `execTransaction` **на** Safe + исходящие ERC20, где `from` = Safe |

**Почему так:** в Etherscan у Safe в поле `from` часто виден **подписант** (EOA), а не адрес Safe.
Claim 003/004 и DeFi через Safe App всё равно относятся к Safe — дашборд собирает их по этим правилам.

**Подписанты в sidebar** — те же Rabby-адреса; кнопка подписанта показывает **личные** tx EOA
(`tx.from` = Rabby), а зелёная кнопка Safe — **операции Safe** (другой срез).

### Источники данных

- **Etherscan API v2** (`ETHERSCAN_API_KEY` в `cryptoops/.env`) — tx, internal, ERC20, NFT
- **Сиды** — `campaigns/*/deploy.json` (claim/deploy tx для классификатора)
- **RPC** (`SEPOLIA_RPC_URL`) — балансы на стр. «Балансы»
- Локальный кэш: `dashboard/cache/{address}/`

Рыночные цены testnet-токенов **не доступны** — в колонках USD/EUR/ETH/BTC стоит **—**.

### Навигация

Используйте боковое меню Streamlit:

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

st.markdown("### Документация")
st.markdown(f"Репозиторий: [{GITHUB_REPO}]({GITHUB_REPO})")

docs = [
    ("Playbook (README)", github_doc("README.md")),
    ("Runbook (кампании 001–004)", github_doc("RUNBOOK.md")),
    ("Кампании", github_doc("campaigns/README.md")),
    ("Дашборд", github_doc("dashboard/README.md")),
    ("Foundry setup", github_doc("FOUNDRY.md")),
    ("Спецификация ДДС", github_doc(".cursor/prompts/streamlit-dds-dashboard.md")),
]
cols = st.columns(2)
for i, (title, url) in enumerate(docs):
    with cols[i % 2]:
        st.link_button(title, url, width="stretch")

with st.expander("Реестр Safe (кратко)"):
    st.markdown(
        """
**Safe #1** — Rabby-A #1, #2 (Deployer), #3

**Safe #2** — Rabby-B #1, #2, #3
"""
    )
