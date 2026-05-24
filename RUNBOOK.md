# Runbook — завершённые кампании (справочник)

Пошаговые инструкции для **уже подготовленных** прогонов. Новая кампания с нуля — [`README.md`](README.md) § Playbook.

Сводка всех ID: [`campaigns/README.md`](campaigns/README.md). On-chain факты — `campaigns/<id>/deploy.json`.

---

## Оглавление

| Кампания | Получатель | Раздел |
|----------|------------|--------|
| `eftihia-sepolia-001` | 3 EOA (Rabby) | [§ 001](#eftihia-sepolia-001-eoa) |
| `eftemonia-sepolia-002` | 3 EOA (Rabby) | [§ 002](#eftemonia-sepolia-002-eoa) |
| `eftihia-safe-sepolia-003` | Safe #1 | [§ 003–004 Safe](#safe-003--004-claim) |
| `eftemonia-safe-sepolia-004` | Safe #2 | [§ 003–004 Safe](#safe-003--004-claim) |

---

## eftihia-sepolia-001 (EOA)

Статус: **✅ deploy + все claim**.

| | |
|---|---|
| Реестр | [`campaigns/eftihia-sepolia-001/deploy.json`](campaigns/eftihia-sepolia-001/deploy.json) |
| Пример адресов / claim | [README.md § справочник 001](README.md#справочник-деплой-eftihia-sepolia-001-пример) |

Тот же паттерн, что § 002: `claim` через `cast` или Etherscan Write + Rabby; `proof` из `output/proof.json`.

---

## eftemonia-sepolia-002 (EOA)

Статус: **✅ deploy + все claim**. Off-chain уже сделано; ниже — справочник on-chain (повторить при аналогичной кампании).

### Что уже готово

| Шаг | Статус |
|-----|--------|
| `campaigns/eftemonia-sepolia-002/whitelist.csv` | 3 × 60, 8 decimals |
| `output/tree.json`, `output/proof.json` | Merkle root `0xfa7336…0bc6` |
| `script/Deploy.s.sol` | root + fund + Eftemonia/8 dec |
| `contracts/TestToken.sol` | имя/symbol/decimals в конструкторе |

### 1. Проверка `.env`

```env
PRIVATE_KEY=0x...          # deployer 0x6886…646f
SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
ETHERSCAN_API_KEY=...
```

На Sepolia у deployer **~0.01+ ETH** на газ.

### 2. Тесты (опционально)

```powershell
cd C:\Users\d_nik\pypro\cryptoops
forge test
```

### 3. Деплой

```powershell
forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast -vvvv
```

Из лога: `Token (TestToken):`, `MerkleClaim:` → заполнить [`deploy.json`](campaigns/eftemonia-sepolia-002/deploy.json).

### 4. Verify на Etherscan

```powershell
forge verify-contract <TOKEN_ADDRESS> contracts/TestToken.sol:TestToken --chain sepolia --constructor-args $(cast abi-encode "constructor(address,string,string,uint8)" 0x6886654B5745EAbB1517eF9D8556c5b3dc86646f "Eftemonia" "EFTEMONIA" 8)

forge verify-contract <CLAIM_ADDRESS> contracts/MerkleClaim.sol:MerkleClaim --chain sepolia --constructor-args $(cast abi-encode "constructor(address,address,bytes32)" 0x6886654B5745EAbB1517eF9D8556c5b3dc86646f <TOKEN_ADDRESS> 0xfa7336e60b0e9376ec62a579beaec2171cb29f4e716a275a13e4649286a30bc6)
```

### 5. Claim — три кошелька

Данные: [`output/proof.json`](campaigns/eftemonia-sepolia-002/output/proof.json).

`claim(uint256 amount, bytes32[] proof)` — для всех трёх: **`amount` = `6000000000`** (raw); `proof` — из `proof.json` для этого адреса.

**A — cast (кошелёк deployer):**

```powershell
Get-Content .env | ForEach-Object { if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim() } }

$claim = "<MERKLE_CLAIM_ADDRESS>"
cast send $claim "claim(uint256,bytes32[])" 6000000000 "[0x...,0x...]" --rpc-url $env:SEPOLIA_RPC_URL --private-key $env:PRIVATE_KEY
```

**B — Etherscan Write + Rabby** (остальные EOAs): Connect → `claim` с `amount` и `proof[]`.

**Rabby:** Add Custom Token = адрес **ERC20**, не MerkleClaim.

### 6. После claim

В `deploy.json`: `"claimed": true`, `"claimTx"` per recipient.

Кампания **001** не затрагивается. Вернуть npm на 001: `$env:CAMPAIGN_ID = "eftihia-sepolia-001"`.

---

## Safe 003 + 004 (claim)

Полная инструкция **claim через Safe** (не Etherscan Write + личный Rabby EOA).

### Сводка on-chain

| Кампания | Safe (получатель) | Token | MerkleClaim | amount | proof |
|----------|-------------------|-------|-------------|--------|-------|
| **003** Eftihia | [0x435A…a8d1](https://app.safe.global/home?safe=sep:0x435A0e13cA88b467C3371E78418fAeaB5721a8d1) | [0x9bA235…1722](https://sepolia.etherscan.io/address/0x9bA2351D4442ec6A028Ffef0aE5373c939f71722) | [0xfc8A1C…888a](https://sepolia.etherscan.io/address/0xfc8A1CDC055C8CcD330B94bf4C592510f9cD888a) | `5400000000000` | `[]` |
| **004** Eftemonia | [0x03E4…dEff](https://app.safe.global/home?safe=sep:0x03E400726D7744f255a160c51De83A035435dEff) | [0x7a869c…2147](https://sepolia.etherscan.io/address/0x7a869cD50504B6F1Ac033dEE2B3fc50608B32147) | [0x9D139B…f416](https://sepolia.etherscan.io/address/0x9D139B500bDDF8D35d11E9829ebD0dd32FAaf416) | `18000000000` | `[]` |

Реестр: [`eftihia-safe-sepolia-003/deploy.json`](campaigns/eftihia-safe-sepolia-003/deploy.json), [`eftemonia-safe-sepolia-004/deploy.json`](campaigns/eftemonia-safe-sepolia-004/deploy.json).

Deploy выполнен; контракты verified.

### Перед claim

1. **Sepolia ETH на Safe** — gas при Execute.
2. Safe App в **том Chrome-профиле**, где владельцы этого Safe.
3. Сеть: **Sepolia**.

### Claim через Safe App

Повторить для **003** и **004** (разные Safe, контракты, `amount`).

1. https://app.safe.global → Connect → нужный Safe → **Sepolia**.
2. **New transaction** → **Transaction Builder** → contract interaction.
3. Адрес **MerkleClaim**: `0xfc8A1CDC055C8CcD330B94bf4C592510f9cD888a` (003) или `0x9D139B500bDDF8D35d11E9829ebD0dd32FAaf416` (004).
4. Метод **`claim`**:
   - 003: `amount` = `5400000000000`, `proof` = **пустой массив**
   - 004: `amount` = `18000000000`, `proof` = **пустой массив**
5. Один лист в дереве → proof **без элементов** (не добавлять хеши).
6. Sign → Execute по порогу; токены на баланс Safe.
7. Проверка: Assets / Add token; `hasClaimed(Safe)` = true.

### Что не делать (Safe)

| Ошибка | Результат |
|--------|-----------|
| Etherscan Write + Rabby EOA | `Invalid proof` |
| `amount` в human (5400000 / 180) | `Invalid proof` |
| Claim Safe #1 на контракт 004 | неверный контракт |
| Execute без ETH на Safe | tx fail |

**Claim для Safe — только Safe App.** Etherscan Write — Read / отладка.

### Deploy 003 / 004 (справка)

```powershell
forge script script/DeployEftihiaSafe.s.sol:DeployEftihiaSafe --rpc-url sepolia --broadcast -vvvv
forge script script/DeployEftemoniaSafe.s.sol:DeployEftemoniaSafe --rpc-url sepolia --broadcast -vvvv
```

### После claim

Обновить `deploy.json`: `"claimed": true`, `"claimTx"`.

---

## Общее после любой кампании

- Сверить балансы и `hasClaimed` on-chain.
- `deploy.json` актуален (tx, links).
- Новая кампания — снова [Playbook](README.md#playbook-от-0-до-claim), не этот файл.
