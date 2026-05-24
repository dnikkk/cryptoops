# Node scripts (`cryptoops/scripts/`)

Не путать с **`cryptoops/script/`** (Solidity, Foundry, `Deploy.s.sol`).

Playbook целиком: [`../README.md`](../README.md) § Playbook (шаг 2 — здесь; шаги 3–5 деплоя — [`../script/README.md`](../script/README.md)).

## Универсальные ли эти скрипты?

**Да — полностью**, для любой кампании в `campaigns/<id>/`.

| Файл | Назначение |
|------|------------|
| `paths.mjs` | Куда писать: `campaigns/{id}/whitelist.csv`, `output/`, `deploy.json` |
| `build-tree.mjs` | CSV → `tree.json` + Merkle root в консоль |
| `get-proof.mjs` | `tree.json` → `proof.json` (root + proof на каждый адрес) |

В скриптах **нет** зашитого root, адресов или сумм — только формат CSV: `address,amount,decimals`.

## Как выбирается кампания

Приоритет:

1. `$env:CAMPAIGN_ID = "eftihia-sepolia-002"` (PowerShell)
2. иначе `campaigns/active.json` → поле `campaignId`
3. иначе fallback `eftihia-sepolia-001`

```powershell
npm run build-tree   # пишет в campaigns/<id>/output/tree.json
npm run get-proof    # пишет в campaigns/<id>/output/proof.json
```

Кампания **001 не перезаписывается**, если `CAMPAIGN_ID` указывает на **002**.

## Новая кампания (только scripts)

```powershell
mkdir campaigns\eftihia-sepolia-002
copy campaigns\_template\whitelist.example.csv campaigns\eftihia-sepolia-002\whitelist.csv
# edit addresses/amounts

$env:CAMPAIGN_ID = "eftihia-sepolia-002"
npm run build-tree
npm run get-proof
```

Дальше — вручную обновить константы в `script/Deploy.s.sol` и деплой (см. [`script/README.md`](../script/README.md)).

## Что перезаписывается

| Команда | Файл | Поведение |
|---------|------|-----------|
| `build-tree` | `output/tree.json` | перезапись в папке **текущей** кампании |
| `get-proof` | `output/proof.json` | перезапись в папке **текущей** кампании |

Старые кампании в других папках **не трогаются**.

## Зависимости

- Node.js, `npm install` в корне `cryptoops`
- Пакет `@openzeppelin/merkle-tree` (`file:./merkle-tree` в `package.json`)

## Сравнение с `script/Deploy.s.sol`

| | `scripts/` (Node) | `script/` (Solidity) |
|---|-------------------|----------------------|
| Универсальность | ✅ полная | ⚠️ константы вручную |
| Сеть | только файлы на диске | Sepolia tx |
| Менять при новой кампании | только CSV + `CAMPAIGN_ID` | + `MERKLE_ROOT`, `FUND` в `.sol` |

См. также: [`campaigns/README.md`](../campaigns/README.md), [`README.md`](../README.md).
