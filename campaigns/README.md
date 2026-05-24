# Campaigns

Каждый airdrop — **одна папка**. Дубликатов в корне проекта нет.

Полный путь **0 → claim**: [`../README.md`](../README.md) § Playbook.  
Merkle (шаг 2): [`../scripts/README.md`](../scripts/README.md).  
Деплой токена + MerkleClaim (шаги 3–5): [`../script/README.md`](../script/README.md) — в этом README деплоя нет.

## Кампании

В папках кампаний **нет** отдельных `README.md` — только данные (`whitelist.csv`, `output/`, `deploy.json`).  
Сводка здесь; on-chain детали → `deploy.json`; пошаговые прогоны → [`RUNBOOK.md`](../RUNBOOK.md) в корне (один файл на все кампании).

| ID | Токен | Статус | On-chain реестр | Runbook |
|----|-------|--------|-----------------|---------|
| `eftihia-sepolia-001` | Eftihia, 6 dec | ✅ все claim | [`deploy.json`](eftihia-sepolia-001/deploy.json) | [RUNBOOK.md § 001](../RUNBOOK.md#eftihia-sepolia-001-eoa) |
| `eftemonia-sepolia-002` | Eftemonia, 8 dec, 3×60 | ✅ все claim | [`deploy.json`](eftemonia-sepolia-002/deploy.json) | [RUNBOOK.md § 002](../RUNBOOK.md#eftemonia-sepolia-002-eoa) |
| `eftihia-safe-sepolia-003` | Safe #1, 5.4M EFTIHIA | ✅ claimed | [`deploy.json`](eftihia-safe-sepolia-003/deploy.json) | [RUNBOOK.md § Safe](../RUNBOOK.md#safe-003--004-claim) |
| `eftemonia-safe-sepolia-004` | Safe #2, 180 EFTEMONIA | ✅ claimed | [`deploy.json`](eftemonia-safe-sepolia-004/deploy.json) | [RUNBOOK.md § Safe](../RUNBOOK.md#safe-003--004-claim) |

## Активная кампания

`active.json` → по умолчанию `eftihia-sepolia-001`.

Переопределение:

```powershell
$env:CAMPAIGN_ID = "eftihia-sepolia-002"
npm run build-tree
```

## Структура одной кампании

```
campaigns/<id>/
  whitelist.csv
  output/
    tree.json
    proof.json
  deploy.json          ← единственный «паспорт» кампании on-chain (без README в папке)
```

## Новая кампания

```powershell
mkdir campaigns\eftihia-sepolia-002
copy campaigns\_template\whitelist.example.csv campaigns\eftihia-sepolia-002\whitelist.csv
copy campaigns\_template\deploy.example.json campaigns\eftihia-sepolia-002\deploy.json
# edit whitelist.csv

$env:CAMPAIGN_ID = "eftihia-sepolia-002"
# optional: set campaigns/active.json campaignId to 002

npm run build-tree
npm run get-proof
# дальше: ../script/README.md → Deploy.s.sol → forge script → fill deploy.json
```

Шаблоны: `_template/`.  
После on-chain: обновить `deploy.json` (адреса Token, MerkleClaim, tx).
