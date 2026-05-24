# Cursor — CryptoOps

Правила и slash-команды для агента в этом репозитории.

## Правила (автоматически)

| Файл | Когда |
|------|--------|
| `rules/cryptoops-core.mdc` | всегда в `cryptoops/` |
| `rules/cryptoops-campaigns.mdc` | файлы в `campaigns/**` |

## Команды (в чате: `/`)

| Команда | Назначение |
|---------|------------|
| `/new-campaign` | новая кампания: папка, CSV, Merkle, правка `Deploy.s.sol` |
| `/campaign-merkle` | только off-chain: `build-tree` + `get-proof` |
| `/campaign-deploy` | on-chain: `forge script --broadcast` + `deploy.json` |
| `/campaign-claim-hint` | параметры claim (EOA / Safe) из `proof.json` |
| `/streamlit-dds` | краткая отсылка; **лучше блок ниже** |

**Handoff-промпты:**

| Файл | Когда |
|------|--------|
| [`prompts/streamlit-dds-dashboard.md`](prompts/streamlit-dds-dashboard.md) | дашборд ДДС — **главная спецификация** |
| [`prompts/agent-prompt-cookbook.md`](prompts/agent-prompt-cookbook.md) | как писать промпты агенту |

Секреты только в `cryptoops/.env` — **не** вставлять `PRIVATE_KEY` / `ETHERSCAN_API_KEY` в чат.

---

## Дашборд ДДС — первое сообщение (скопировать целиком)

> Slash-команда может не подхватиться — вставьте **весь** блок как первое сообщение в новом чате.  
> Workspace: `C:\Users\d_nik\pypro\cryptoops`

```
Реализуй Streamlit DDS dashboard строго по спецификации:

C:\Users\d_nik\pypro\cryptoops\.cursor\prompts\streamlit-dds-dashboard.md

Прочитай этот файл целиком перед кодом. Также: campaigns/*/deploy.json, cryptoops/README.md, RUNBOOK.md.

Старт: Фаза A+B. Только Sepolia testnet. Свой оригинальный UI (не копировать чужие проекты).

Данные: Etherscan API — ключ в cryptoops/.env (ETHERSCAN_API_KEY), читай локально. Собери все tx по адресу, затем классифицируй и обогати. DeFi-протоколы определяй из tx, не из устных подсказок.

Реестр кошельков (создай dashboard/wallets.yaml):

Safe #1: 0x435A0e13cA88b467C3371E78418fAeaB5721a8d1
  signers: 0x898EfFDB03Ba6623640cF9E8BE39de7ad78c6680, 0x6886654B5745EAbB1517eF9D8556c5b3dc86646f, 0xF3364d8E63a051D6Ee5C20B95757468a10b2a97B

Safe #2: 0x03E400726D7744f255a160c51De83A035435dEff
  signers: 0xFEa86eb2A7A5bf99CA1C2C2e81490A7ef13D164e, 0x1bb2961B8d2E490Bd61F89CE87eb9072d5c85730, 0x2B232f0B685F7cC8701fDF6987CC6D3769B164FA

Те же три EOA профиля A — и owners Safe #1, и отдельные EOA для ДДС.

Sidebar стр. 2: дерево Safe → подписанты; выбор Safe = ДДС по tx.from Safe.

ДДС: parent row = глобальная tx; expand → child legs. Цены: прочерк — если нет котировки.

5 страниц: О проекте | ДДС (5 вкладок) | Карта потоков | SLA | Балансы (токены на адресе Sepolia).

Не создавай новые Merkle-кампании. Не коммить .env.
```

---

## Примеры: кампании

### `/new-campaign` — EOA, без деплоя

```
/new-campaign

campaignId: eftihia-sepolia-005
tokenName: Eftihia
tokenSymbol: EFTIHIA
tokenDecimals: 6
recipientType: EOA
recipients:
  - address: 0x1111111111111111111111111111111111111111
    amount: 1800000
    decimals: 6
deployNow: no
```

### `/campaign-deploy`

```
/campaign-deploy

campaignId: eftihia-sepolia-005
confirmBroadcast: yes
```

Документация: [`../README.md`](../README.md) § Playbook.
