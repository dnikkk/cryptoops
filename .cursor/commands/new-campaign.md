# New Merkle airdrop campaign (CryptoOps)

Execute the full **off-chain + prepare on-chain** flow for a new campaign. Ask only for missing inputs below.

## User must provide (fill or ask)

```
campaignId:
tokenName:
tokenSymbol:
tokenDecimals:
recipientType: EOA | Safe
recipients:
  - address:
    amount:          # human units
    decimals:        # usually same as tokenDecimals
deployNow: yes | no   # run forge --broadcast only if yes and .env exists
```

Optional: `setActiveJson: yes` → update `campaigns/active.json` to this id.

## You must do

1. Read `README.md` Playbook and `campaigns/README.md` if unsure.
2. Create `campaigns/<campaignId>/` from `_template/` (no README in that folder).
3. Write `whitelist.csv` from user recipients.
4. Run (PowerShell, from `cryptoops/`):
   - `$env:CAMPAIGN_ID = "<campaignId>"`
   - `npm run build-tree`
   - `npm run get-proof`
5. Print `merkleRoot` and verify `proof.json` has every address.
6. Update `script/Deploy.s.sol` constants: `MERKLE_ROOT`, `FUND_CLAIM_CONTRACT`, `TOKEN_NAME`, `TOKEN_SYMBOL`, `TOKEN_DECIMALS`.
7. If `recipientType` is Safe and multiple Safes: ensure whitelist has all Safe addresses; note single-leaf vs multi-leaf for proof at claim time.
8. Run `forge build` and `forge test` if deploy requested.
9. If `deployNow: yes`: run `forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast -vvvv` (never print PRIVATE_KEY).
10. Fill `campaigns/<campaignId>/deploy.json` from forge logs.
11. Add one row to `campaigns/README.md` table (status: prepared / deployed).
12. Tell user next steps: verify Etherscan, claim (EOA → README claim section; Safe → `RUNBOOK.md` § Safe).

## Do not

- Commit `.env` or ask user to paste private keys in chat.
- Create `campaigns/<id>/README.md`.
- Overwrite another campaign's `output/` (always set `CAMPAIGN_ID`).

## Reference

@README.md @campaigns/README.md @scripts/README.md @script/README.md
