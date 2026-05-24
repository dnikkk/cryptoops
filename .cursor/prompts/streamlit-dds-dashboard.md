# Handoff: Streamlit DDS Dashboard (CryptoOps)

> Скопируйте этот файл целиком в **новый чат** (или `/streamlit-dds`).  
> Цель: упорядочить уже сделанное on-chain / DeFi и построить отчётность (ДДС), не плодя новые кампании до ясной картины.

---

## 1. Задача

Построить **Streamlit multipage app** — операционный дашборд / **ДДС (движение денежных средств)** по крипто-операциям пользователя на **Sepolia** (позже расширяемо на mainnet).

Пользователь запутался: часть действий (Aave deposit/withdraw, Uniswap LP) делалась через **Rabby** на сайтах, часть — через **Gnosis Safe**; нужно видеть **по выбранному адресу** (EOA или Safe), кто реальный `from` / владелец позиции on-chain.

**Не в scope первой итерации:** новые Merkle-кампании, деплой контрактов (есть отдельный Playbook в `cryptoops/README.md`).

---

## 2. Репозиторий и документация

| Путь | Назначение |
|------|------------|
| `C:\Users\d_nik\pypro\cryptoops\` | Merkle airdrop, кампании 001–004, `.env` |
| `cryptoops/README.md` | Playbook 0→claim |
| `cryptoops/campaigns/*/deploy.json` | Реестр контрактов, claim tx |
| `cryptoops/RUNBOOK.md` | EOA vs Safe claim |
| `cryptoops/.cursor/` | Правила и команды агента |

**Место кода:** `cryptoops/dashboard/` (или `cryptoops/streamlit/`) — зафиксировать в README дашборда.

### UI: творческий дизайн, без копирования чужих проектов

- **Не** использовать внешние UI-референсы (другие репозитории, bond-dashboard и т.п.).
- **Придумать** собственную визуальную систему под тему «on-chain treasury / ДДС»: палитра, типографика, карточки KPI, иконки категорий (Claim / Swap / LP / Deposit), визуальное различие **EOA vs Safe**.
- Допустимо: кастомный CSS через `st.markdown(unsafe_allow_html=True)` + `.streamlit/config.toml` (theme base, primary color).
- Цель: узнаваемый, аккуратный ops-dashboard, не дефолтный «голый» Streamlit.

### Референс только на виджеты Streamlit (не на внешний дизайн)

Использовать встроенные API — не искать сторонние UI-kit в интернете:

| Задача | Виджет |
|--------|--------|
| Навигация multipage | `pages/` + `st.navigation` или классическая структура `pages/*.py` |
| Фильтры | `st.sidebar.selectbox`, `st.date_input`, `st.toggle` |
| Вкладки ДДС | `st.tabs` |
| Таблица операций | `st.dataframe` (column_config: `LinkColumn` для tx) или `st.data_editor` read-only |
| KPI сверху | `st.metric` в `st.columns` |
| Графики потоков | `plotly` + `st.plotly_chart` или `st.graphviz_chart` |
| Диаграмма процесса | Mermaid в `st.markdown("```mermaid...")` или `streamlit-mermaid` если в deps |
| Загрузка данных | `@st.cache_data` + `st.spinner` / `st.status` |
| Ошибки API | `st.warning`, `st.error`, `st.toast` |
| Экспорт | `st.download_button` (CSV) |
| SLA чеклисты | `st.checkbox` + `st.session_state` |
| Пояснения | `st.expander`, `st.info`, `st.caption` |
| Внешние ссылки | `st.link_button` на Etherscan / Safe |
| Пустое состояние | `st.empty` + текст «нет операций за период» |

Документация виджетов: https://docs.streamlit.io/develop/api-reference (достаточно официальной; не требуется surf вне docs).

---

## 3. Уже проведённая работа (факты)

### 3.1 Сеть

- **Sepolia** (chainId 11155111)
- Explorer: `https://sepolia.etherscan.io`
- RPC из `cryptoops/.env` → `SEPOLIA_RPC_URL`
- Etherscan API: `ETHERSCAN_API_KEY` (v2 unified API для Sepolia)

### 3.2 Роли кошельков (два профиля Chrome / два Rabby)

**Профиль A** — Safe **#1** + те же EOAs, что в Merkle **001–002**:

| Метка | Адрес | Тип |
|-------|--------|-----|
| Deployer / Rabby‑A #0 | `0x6886654B5745EAbB1517eF9D8556c5b3dc86646f` | EOA |
| Rabby‑A #1 | `0x898EfFDB03Ba6623640cF9E8BE39de7ad78c6680` | EOA |
| Rabby‑A #2 | `0xF3364d8E63a051D6Ee5C20B95757468a10b2a97B` | EOA |
| Safe #1 | `0x435A0e13cA88b467C3371E78418fAeaB5721a8d1` | Safe |

**Подписанты Safe #1 (полный список owners = те же три EOA профиля A):**

1. `0x898EfFDB03Ba6623640cF9E8BE39de7ad78c6680`
2. `0x6886654B5745EAbB1517eF9D8556c5b3dc86646f`
3. `0xF3364d8E63a051D6Ee5C20B95757468a10b2a97B`

Эти же три адреса — **самостоятельные EOA** для ДДС (блок «Отдельные EOA» / профиль A).

**Профиль B** — Safe **#2** и **отдельный набор** Rabby EOAs:

| Метка | Адрес | Тип |
|-------|--------|-----|
| Rabby‑B #1 | `0xFEa86eb2A7A5bf99CA1C2C2e81490A7ef13D164e` | EOA |
| Rabby‑B #2 | `0x1bb2961B8d2E490Bd61F89CE87eb9072d5c85730` | EOA |
| Rabby‑B #3 | `0x2B232f0B685F7cC8701fDF6987CC6D3769B164FA` | EOA |
| Safe #2 | `0x03E400726D7744f255a160c51De83A035435dEff` | Safe |

**Подписанты Safe #2 (полный список от пользователя):** три адреса выше. Claim 004 выполнял signer `0x2B232f0B685F7cC8701fDF6987CC6D3769B164FA`.

**Не путать:** `0xF336…` относится к **профилю A**, не ко второму списку. В сайдбаре Safe #2 вешает под собой только **FEa8 / 1bb2 / 2B23**.

### 3.3 Кампании Merkle (все claim ✅)

| ID | Токен | Получатели | Token | MerkleClaim |
|----|-------|------------|-------|-------------|
| `eftihia-sepolia-001` | EFTIHIA 6 dec | 3 EOA | `0x8d271a6651405A052315f686703abDA6900F1389` | `0x313330E4a25b1F52Fa5f6De31bDE4F21FD917eA6` |
| `eftemonia-sepolia-002` | EFTEMONIA 8 dec | 3 EOA | `0xD8F12d08DF8752c7CD1d372D1Ae17BE44AD8f05D` | `0x876360751b9AC12Cb688b1Fa2f21f43D453BAb52` |
| `eftihia-safe-sepolia-003` | EFTIHIA | Safe #1 | `0x9bA2351D4442ec6A028Ffef0aE5373c939f71722` | `0xfc8A1CDC055C8CcD330B94bf4C592510f9cD888a` |
| `eftemonia-safe-sepolia-004` | EFTEMONIA | Safe #2 | `0x7a869cD50504B6F1Ac033dEE2B3fc50608B32147` | `0x9D139B500bDDF8D35d11E9829ebD0dd32FAaf416` |

Детали и claim tx: `campaigns/<id>/deploy.json`.

### 3.4 Эталонные on-chain tx (все 4 кампании)

Обязательно импортировать `campaigns/*/deploy.json`. Таблица для автотестов классификатора:

| Кампания | Тип | Tx hash |
|----------|-----|---------|
| **001** | token deploy | `0x4e8c211fbfedceef8399137234c60b08091725e5fb269eb87a885cd42fb5baa1` |
| **001** | claim deploy | `0x46b7cf30783c16dae4e8dc384f0d4317135617c02701e29feb8c9c95fcd9de61` |
| **001** | fund claim | `0x90128029d0f150fabeeb117caf2ca8859cc736a1ccf365e64c115fc1846b67d5` |
| **001** | claim 6886… | `0x6d89e25f607f768e1ce7773de6db6e9ca7cf1e12f7e76286ab3b5f7b1b9d6844` |
| **001** | claim 898E… | `0x534d917b0ed9ae543e3885b743ed1152456d059d64187e7a9b9a19f6e2834403` |
| **001** | claim F336… | `0x00c55f7eb74bd69e7bfaf42e0975426876b9ca62b9fd97ffa45c0220716c7f9d` |
| **002** | token deploy | `0xf572e9d1a3e0825ba7b2d13dbaac447fae618b61fe761a51d094d0405813edb7` |
| **002** | claim deploy | `0x03143470990f7b895fb5a6ab113613329d9d93e1cfa7185722403f420c1439f1` |
| **002** | fund claim | `0x3cf73d4d440204a8b3373375d1263f32b31c984c070129ec9f6caf3d926716b1` |
| **002** | claim 6886… | `0xc2bad7ad7e2c70c37fd53835a781f613e43cec45f1e3f33883fce9b725dba5ad` |
| **002** | claim 898E… | `0x977ebf9cddc084b11636ae6475a34b01775b72fff5ba9173a6055f3d95b54b91` |
| **002** | claim F336… | `0xafb5ba8093e008a4e26e938d1063924a901bf90c5835e0ad401eae9c1680d41e` |
| **003** | token deploy | `0x6cf77e133ee1432ebd6cde49a5758295433621e8ff920ab8cd5a9cd182d50ddf` |
| **003** | claim deploy | `0xff86889e5aa406785a8f3f626543fb6b8d47085ef121e1bbfcde6c3b61a799be` |
| **003** | fund claim | `0xb0d7a367690ebaece6833e85a4d238afd86e40e28b78347c067628e52de0c80a` |
| **003** | claim Safe #1 | `0xf36658c96e51192a4c7f6ccdd8912015a8a023427d6e325dd22a96f5b1e19499` |
| **004** | token deploy | `0xe88b42f88019d59b85224f941d4be667f5073a4141e923a8cb153c44253c61b2` |
| **004** | claim deploy | `0x8de0f0203cb5545f7196df7fe243b74d6c031a31bb11f5a08ec9a0a54e6c4383` |
| **004** | fund claim | `0xabdeeb48fc762de5e474a8102b2465dea5920cadda3531848e9836dbaf5d588c` |
| **004** | claim Safe #2 | `0x30820fc07393d943dc2b990d1a590d89281e7971c5965a99074f775794d67a86` |

### 3.5 DeFi и сеть

- **Только Sepolia testnet** (chainId `11155111`). Mainnet и Unichain Sepolia — не в MVP.
- Типы DeFi (Aave, Uniswap, LP, swap и т.д.) **не задавать вручную** в ТЗ: агент определяет из tx/logs по каждому адресу реестра.
- Off-chain UI протоколов может не показывать историю — **ДДС строится только из блокчейна**.

### 3.6 Архитектура airdrop (контекст)

Нет отдельного «минта токена без дропа»: `TestToken` + `MerkleClaim` + `mint` в одном `forge script`.  
Off-chain: `scripts/` (Merkle). On-chain deploy: `script/Deploy.s.sol`.

---

## 4. Спецификация Streamlit app

### 4.1 Multipage

| # | Страница | Содержание |
|---|----------|------------|
| 1 | **О проекте** | Короткое умное описание: CryptoOps, Sepolia, EOA vs Safe, что такое ДДС в app, откуда данные (Etherscan). |
| 2 | **ДДС** | Основная аналитика (см. вкладки + sidebar). |
| 3 | **Карта потоков** | Mermaid / graph: whitelist → Merkle → deploy → claim → (swap → LP → Aave). Зависимости по выбранному кошельку. |
| 4 | **SLA** | Заготовка чеклистов из `cryptoops/README.md` § SLA — `st.checkbox` / таблица статусов |
| 5 | **Балансы** | Текущие токены на выбранном адресе (Sepolia); не ДДС. Детали UI уточнить после MVP ДДС. Unichain — позже |

### 4.2 Sidebar

**Стр. 2 (ДДС) — иерархия кошельков (обязательно):**

Показать связь **Safe → подписанты (Rabby EOA)**, чтобы было видно: операции Safe on-chain ≠ «кошелёк Rabby в Connect», а подписанты — отдельные EOA.

Рекомендуемый UI в sidebar:

```
Сеть: Sepolia
Период: [date range]

─── Кошелёк для ДДС ───
▼ Safe #1  0x435A…a8d1
    ○ 0x898E…6680  ○ 0x6886…646f  ○ 0xF336…a97B  (все три owners)
▼ Safe #2  0x03E4…dEff
    ○ 0xFEa8…164e  ○ 0x1bb2…5730  ○ 0x2B23…4FA  (все три — owners)

─── Отдельные EOA (ДДС по tx.from — не Safe) ───
○ профиль A: 0x6886…  0x898E…  0xF336…
○ профиль B: 0xFEa8…  0x1bb2…  0x2B23…   (повторять подписантов здесь допустимо)
```

Поведение:

- **Выбор Safe** → таблица ДДС: `tx.from == Safe` (операции кастоди/DeFi с Safe).
- Подписанты под Safe — **свернутый список** (read-only или `st.caption`): «кто может подписать»; опционально ссылка на последний `executedBySigner` из claim tx.
- **Выбор EOA в блоке «Отдельные EOA»** → ДДС по `tx.from == EOA` (claim 001/002, swap с Rabby на сайте).
- Не смешивать: подписант под Safe **не** подменяет выбранный адрес Safe в ДДС.

Данные иерархии: `dashboard/wallets.yaml` (или `labels.json`) — см. §10.

**Стр. 3–4:** тот же выбранный «головной» адрес (Safe или EOA) из `st.session_state`, без дублирования дерева если тесно — достаточно compact selectbox + badge `EOA` / `Safe`.

### 4.3 Страница 2 — пять вкладок (`st.tabs`)

1. **Все операции** — полный ДДС по выбранному адресу  
2. **Claim** — MerkleClaim `claim()`, Transfer от claim-контракта  
3. **Swap** — Uniswap Router / Universal Router swaps  
4. **LP** — liquidity add/remove (определяется из tx)  
5. **Deposit** — supply/withdraw lending и аналоги (определяется из tx)

### 4.4 Модель строк ДДС (иерархия транзакций)

**Предпочтительно (MVP):**

- **Родительская строка** = одна **глобальная** on-chain операция (`tx_hash` верхнего уровня для выбранного адреса): категория, протокол, время, сводный `notes`, ссылка Etherscan.
- По клику / expander (`st.expander` на строку или master-detail в `st.dataframe`) — **дочерние строки**: internal tx, token transfers, отдельные log-события, которые составляют эту операцию.
- Колонки связи: `row_level` (`parent` | `child`), `parent_tx_hash`, `child_index`, `leg_type` (transfer / internal / event).

**Альтернатива (если expander тяжёлый):** одна строка = глобальная tx, детали в колонках `legs_summary`, `token_in`, `token_out`, `amount_in`, `amount_out` без дублирования parent rows.

Правило учёта: пользователь видит **одну глобальную операцию**; подчинённые tx не считаются отдельными «главными» строками в сводной вкладке «Все операции» (только под родителем).

### 4.5 Колонки ДДС

| Колонка | Описание |
|---------|----------|
| `datetime` | UTC |
| `row_level` | parent / child |
| `parent_tx_hash` | для child — hash родителя |
| `tx_hash` | ссылка Sepolia Etherscan |
| `category` | Claim / Swap / LP / Deposit / Transfer / Gas / Deploy / Other |
| `direction` | In / Out / — |
| `asset` | symbol |
| `amount` | human (+ raw в tooltip или отдельно) |
| `value_usd` | цена если есть, иначе **`—`** |
| `value_eur` | иначе **`—`** |
| `value_eth` | иначе **`—`** |
| `value_btc` | иначе **`—`** |
| `counterparty` | address / label |
| `protocol` | из decode/heuristic |
| `method` | decoded |
| `wallet_role` | EOA / Safe |
| `status` | success / failed |
| `notes` | краткое описание операции |

Это **ДДС (движения)**, не отчёт о балансе. Отсутствие рыночной цены testnet-токена — норма (`—`).

Сортировка по времени parent; CSV export.

### 4.6 Источники данных (Etherscan-first)

**Принцип:** для выбранного адреса собрать **все** релевантные транзакции с Etherscan, затем обогатить (decode, logs, классификация). Ключ: `ETHERSCAN_API_KEY` в `cryptoops/.env` (агент читает локально; значение не в чат).

Минимальный набор API (Sepolia, chainid `11155111`):

| Модуль | Назначение |
|--------|------------|
| `account` → `txlist` | исходящие tx |
| `account` → `txlistinternal` | internal (для child legs) |
| `account` → `tokentx` | ERC20 transfers |
| `account` → `tokennfttx` | NFT (LP positions) |
| `proxy` → `eth_getTransactionReceipt` или logs API | события |
| `contract` → `getabi` + decode | method name (если verified) |

Дополнительно: `SEPOLIA_RPC_URL` для `balanceOf` на стр. 5.

1. **Локальный кэш** `dashboard/cache/{address}/` — сырые ответы API  
2. **Сид** `campaigns/*/deploy.json` + таблица §3.4  
3. **`dashboard/wallets.yaml`** — реестр адресов §10  
4. **`dashboard/protocol_addrs.yaml`** — заполняется агентом по мере обнаружения контрактов в tx (не требовать от пользователя)

Классификация — после сбора tx: MerkleClaim + seeds → Claim; эвристики по `to`/`method`/logs → Swap, LP, Deposit; gas отдельно.

### 4.7 Страница 5 — Балансы (MVP)

- По **тому же** выбранному адресу в sidebar.
- Сеть: **Sepolia** (`ethereum_sepolia`).
- Таблица: token contract / symbol / decimals / balance human / ссылка Etherscan.
- Источник: `tokentx` + текущие balances (RPC `eth_call` balanceOf) или Etherscan token balance если доступно.
- **Unichain Sepolia** — placeholder «скоро», не блокировать MVP.
- Не смешивать с ДДС: отдельная страница, без колонок движения за период.

### 4.8 UX / техника

- `requirements.txt`: streamlit, pandas, requests, plotly, python-dotenv  
- Читать `ETHERSCAN_API_KEY` из `cryptoops/.env`  
- **Не** хранить private key в app  
- Обработка rate limit / пустого ответа — `st.warning`  
- README в папке дашборда: `streamlit run ...`
- **Визуал:** оригинальный layout (см. §2); в Фазе E — polish CSS/метрики, без заимствования layout из других проектов пользователя

---

## 5. Порядок реализации (для агента)

**Фаза A — скелет**

- Multipage + sidebar wallet + реестр адресов  
- Стр. 1 текст  
- Стр. 2 вкладки с placeholder tables  

**Фаза B — data layer**

- Etherscan client + cache  
- Парсер → единый DataFrame ДДС  
- Классификатор категорий  

**Фаза C — наполнение**

- Подтянуть tx для всех адресов из `wallets.yaml` + кастомные; сверить claim с `deploy.json`  
- Вкладки фильтруют один DF  

**Фаза D — визуал**

- Стр. 3 Mermaid  
- Стр. 4 SLA  
- Стр. 5 балансы (базовая таблица токенов)

**Фаза E — polish**

- parent/child expand, CSV export, визуал, `—` для цен  

---

## 6. Критерии готовности MVP

- [ ] Выбор любого адреса из реестра (все EOAs из двух профилей + два Safe) меняет таблицу стр. 2  
- [ ] Под деревом каждого Safe отображены **верные** подписанты (A vs B см. §3.2)
- [ ] Claim tx 003/004 и 001/002 видны на вкладке Claim  
- [ ] Swap/LP/Deposit показывают tx, если они есть на Sepolia для адреса (или явное «нет данных»)  
- [ ] У каждой строки есть ссылка на Etherscan  
- [ ] Родительские строки + раскрытие child legs для сложных tx  
- [ ] Цены: `—` где нет котировки (без ошибок)  
- [ ] Стр. 3 — диаграмма потоков  
- [ ] Стр. 4 — SLA  
- [ ] Стр. 5 — список токенов на адресе (Sepolia)  
- [ ] Все эталонные tx §3.4 классифицируются верно  

---

## 7. Вопросы пользователю (только если блокер)

Не спрашивать про Aave/Uniswap заранее. Спросить только если: нет `.env` / `ETHERSCAN_API_KEY`, или API rate limit без обхода.

---

## 8. Ограничения

- Не менять Merkle-кампании и `Deploy.s.sol` без явной просьбы  
- Не коммитить `.env`  
- Минимальный diff в существующих README cryptoops — одна строка ссылка на dashboard  

---

## 10. Что пользователь передаёт агенту (чеклист)

### В чат — можно и нужно

| Данные | Зачем |
|--------|--------|
| Адреса **Safe** + человекочитаемые имена | ДДС, sidebar-дерево |
| Адреса **Rabby EOA** + имена (#0, #1, #2) | ДДС, подписанты |
| **Маппинг Safe → список подписантов** (кто owner в Safe App) | Иерархия в sidebar |
| Какие EOA **не** привязаны к Safe (только личные операции) | Блок «Отдельные EOA» |
| Сеть: Sepolia only / + mainnet позже | scope |
| Подтверждение: «`cryptoops/.env` есть, ключ Etherscan заполнен» | агент читает локально, значение не копировать |
| Подтверждение `.env` с `ETHERSCAN_API_KEY` | агент читает с диска |

### В чат — нельзя

| Данные | Почему |
|--------|--------|
| **`PRIVATE_KEY`** | секрет; только в `.env` на диске |
| Значения **`ETHERSCAN_API_KEY`** | секрет; достаточно «настроен в .env» |
| Seed phrase / пароль Rabby | безопасность |

### Что такое `PRIVATE_KEY` (`.env`)

- Приватный ключ **EOA deployer** (`0x6886…646f`) для **Foundry**: `forge script --broadcast`, `cast send`.
- **Не нужен** для Streamlit-дашборда (только чтение Etherscan).
- **Не спрашивать** в чате для DDS; агент проверяет наличие `.env` только если нужен on-chain write.

### Локально в `cryptoops/.env` (агент читает сам)

```env
ETHERSCAN_API_KEY=...      # обязателен для дашборда
SEPOLIA_RPC_URL=...        # желателен (балансы, decode)
PRIVATE_KEY=0x...          # для деплоя/claim, не для DDS
```

### Шаблон `dashboard/wallets.yaml` (создать при старте)

```yaml
# dashboard/wallets.yaml — пример после ввода пользователя
network: sepolia
chrome_profiles:
  profile_a_safe1:
    label: "Chrome A / Rabby A + Safe #1"
    rabby_signers_deploy_claim_001_002:
      - { label: "Rabby‑A Deployer #0", address: "0x6886654B5745EAbB1517eF9D8556c5b3dc86646f" }
      - { label: "Rabby‑A #1", address: "0x898EfFDB03Ba6623640cF9E8BE39de7ad78c6680" }
      - { label: "Rabby‑A #2", address: "0xF3364d8E63a051D6Ee5C20B95757468a10b2a97B" }

safes:
  - label: Safe #1
    address: "0x435A0e13cA88b467C3371E78418fAeaB5721a8d1"
    chrome_profile: profile_a_safe1
    signers:
      - { label: "Rabby‑A #1", address: "0x898EfFDB03Ba6623640cF9E8BE39de7ad78c6680" }
      - { label: "Rabby‑A Deployer", address: "0x6886654B5745EAbB1517eF9D8556c5b3dc86646f" }
      - { label: "Rabby‑A #2", address: "0xF3364d8E63a051D6Ee5C20B95757468a10b2a97B" }

  - label: Safe #2
    address: "0x03E400726D7744f255a160c51De83A035435dEff"
    chrome_profile: profile_b_safe2
    signers:
      - { label: "Rabby‑B #1", address: "0xFEa86eb2A7A5bf99CA1C2C2e81490A7ef13D164e" }
      - { label: "Rabby‑B #2", address: "0x1bb2961B8d2E490Bd61F89CE87eb9072d5c85730" }
      - { label: "Rabby‑B #3", address: "0x2B232f0B685F7cC8701fDF6987CC6D3769B164FA" }

standalone_eoas_for_dds:
  # ДДС по tx.from когда смотреть операции именно как EOA, не как Safe:
  profile_a_all:
    - "0x6886654B5745EAbB1517eF9D8556c5b3dc86646f"
    - "0x898EfFDB03Ba6623640cF9E8BE39de7ad78c6680"
    - "0xF3364d8E63a051D6Ee5C20B95757468a10b2a97B"
  profile_b_signers_only:
    - "0xFEa86eb2A7A5bf99CA1C2C2e81490A7ef13D164e"
    - "0x1bb2961B8d2E490Bd61F89CE87eb9072d5c85730"
    - "0x2B232f0B685F7cC8701fDF6987CC6D3769B164FA"

```

Уточнение: три EOA профиля A = owners Safe #1 **и** standalone EOA. ДДС фильтруется по **головному** адресу (Safe или EOA).

---

## 11. Первое сообщение в новом чате

Полный текст — в `.cursor/README.md` § «Дашборд ДДС — первое сообщение».  
Slash `/streamlit-dds` может не сработать — использовать **полный блок** из README, не сокращать.
