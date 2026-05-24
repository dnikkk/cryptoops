# Claim instructions for a campaign

Read `campaigns/<id>/output/proof.json` and `deploy.json`; output copy-paste claim params.

## Input

```
campaignId:
recipientAddress:   # optional — one address; else list all
```

## Output per recipient

- MerkleClaim contract from `deploy.json`
- `amount` (raw) from proof.json
- `proof` array (empty `[]` if single leaf)
- Method: **EOA** → Etherscan Write + Rabby or `cast send`; **Safe** → Safe App only (`RUNBOOK.md` § Safe)

Do not run claim txs unless user explicitly asks and provides signing method.

@RUNBOOK.md @README.md
