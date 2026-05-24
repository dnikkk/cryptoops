# Foundry — Sepolia deploy & claim

Полный playbook (шаг 0, 4–5, verify, claim): [`README.md`](README.md) § Playbook. Константы деплоя: [`script/README.md`](script/README.md).

## Prerequisites

- Foundry (`forge`, `cast`) — installed via Git Bash: `foundryup`
- Sepolia ETH on deployer wallet
- `.env` from `.env.example`

## 1. Install Solidity deps

In **Git Bash** (or terminal where `forge` is in PATH):

```bash
cd /c/Users/d_nik/pypro/cryptoops
forge install foundry-rs/forge-std --no-commit
forge install OpenZeppelin/openzeppelin-contracts --no-commit
```

## 2. Compile

```bash
forge build
```

## 3. Deploy (Sepolia)

```bash
source .env   # or export PRIVATE_KEY and SEPOLIA_RPC_URL
forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast -vvvv
```

Save printed `TestToken` and `MerkleClaim` addresses.

If you change `whitelist.csv`, rerun `npm run build-tree && npm run get-proof`, update `MERKLE_ROOT` in `script/Deploy.s.sol`, and deploy again.

## 4. Claim from Rabby

1. Network: **Sepolia**
2. Contract: `MerkleClaim` address
3. Function: `claim(uint256 amount, bytes32[] proof)`
4. Args from `campaigns/eftihia-sepolia-001/output/proof.json` → `claims["0x<your address lowercase>"]`:
   - `amount`: e.g. `1800000000000`
   - `proof`: array of hex strings

## 5. Useful cast commands

```bash
# Read root (immutable)
cast call <MERKLE_CLAIM> "merkleRoot()(bytes32)" --rpc-url $SEPOLIA_RPC_URL

# Check if address claimed
cast call <MERKLE_CLAIM> "hasClaimed(address)(bool)" <YOUR_ADDRESS> --rpc-url $SEPOLIA_RPC_URL
```

## Project layout

```
cryptoops/
  contracts/     TestToken.sol, MerkleClaim.sol
  script/        Deploy.s.sol
  lib/           forge-std, openzeppelin (after forge install)
  scripts/       Node Merkle builders
  campaigns/{id}/output/   tree.json, proof.json
```
