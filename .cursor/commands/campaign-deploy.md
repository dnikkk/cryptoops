# Deploy campaign on Sepolia (on-chain)

Deploy **TestToken + MerkleClaim + mint** for a campaign that already has `output/proof.json`.

## Input

```
campaignId:     # required — must match proof.json
confirmBroadcast: yes   # required to send txs
```

## Preconditions

- `campaigns/<campaignId>/output/proof.json` exists with `merkleRoot`
- `script/Deploy.s.sol` (or agreed `Deploy*.s.sol`) has matching `MERKLE_ROOT`, `FUND_CLAIM_CONTRACT`, token constants
- `.env` has `PRIVATE_KEY` and RPC (do not read key into chat)

## Steps

1. Verify root in `proof.json` matches `MERKLE_ROOT` in deploy script.
2. `forge build` && `forge test -vv`
3. If `confirmBroadcast: yes`: `forge script script/Deploy.s.sol:Deploy --rpc-url sepolia --broadcast -vvvv`
4. Update `campaigns/<campaignId>/deploy.json` with token + claim addresses and tx hashes.
5. Summarize Etherscan links; suggest verify + claim next steps.

@script/README.md @README.md
