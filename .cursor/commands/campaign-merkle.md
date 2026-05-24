# Merkle only (off-chain)

Build tree and proofs for an **existing** `campaigns/<id>/whitelist.csv`.

## Input

```
campaignId:   # required
```

## Steps

1. Confirm `campaigns/<campaignId>/whitelist.csv` exists.
2. `$env:CAMPAIGN_ID = "<campaignId>"`
3. `npm run build-tree` then `npm run get-proof`
4. Report `merkleRoot` from console or `output/proof.json`.
5. Remind: copy root + fund sum into `script/Deploy.s.sol` before deploy (`script/README.md`).

@scripts/README.md @campaigns/README.md
