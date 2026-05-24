# Deploy script (`Deploy.s.sol`)

Playbook целиком: [`../README.md`](../README.md) § Playbook (шаги 3–5 — этот файл; шаг 2 Merkle — [`../scripts/README.md`](../scripts/README.md); папка кампании — [`../campaigns/README.md`](../campaigns/README.md)).

## Универсальный ли скрипт?

**Каркас — да**, **числа — нет.**

| Часть | Поведение |
|-------|-----------|
| Логика | Всегда: `TestToken` → `MerkleClaim` → `mint` на claim-контракт |
| `MERKLE_ROOT` | **Вручную** из `campaigns/<id>/output/proof.json` → `merkleRoot` |
| `FUND_CLAIM_CONTRACT` | **Вручную** = сумма всех выплат из `whitelist.csv` (raw, 6 decimals) |
| Имя токена | Константы `TOKEN_NAME` / `TOKEN_SYMBOL` / `TOKEN_DECIMALS` в `Deploy.s.sol` |

Перед **новой кампанией** (002, 003…):

1. `npm run build-tree` и `npm run get-proof` для этого `CAMPAIGN_ID`.
2. Открыть `script/Deploy.s.sol` и обновить **обе константы**.
3. `forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast -vvvv`
4. Записать адреса в `campaigns/<id>/deploy.json`.

Каждый деплой = **новые** адреса `TestToken` и `MerkleClaim`. Старые кампании не перезаписываются.

## Пример fund

3 адреса × 1_800_000 (6 decimals):

```solidity
uint256 constant FUND_CLAIM_CONTRACT = 5_400_000 * 1e6;
```

2 адреса × 2_000_000:

```solidity
uint256 constant FUND_CLAIM_CONTRACT = 4_000_000 * 1e6;
```

## Команда

```powershell
forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast -vvvv
```

См. также: [FOUNDRY.md](../FOUNDRY.md), [README.md](../README.md) (раздел деплоя).
