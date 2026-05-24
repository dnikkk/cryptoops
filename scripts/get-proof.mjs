import { StandardMerkleTree } from "@openzeppelin/merkle-tree";
import fs from "fs";
import { getCampaignPaths } from "./paths.mjs";

const paths = getCampaignPaths();

if (!fs.existsSync(paths.treePath)) {
  console.error(`Missing: ${paths.treePath}`);
  console.error("Run: npm run build-tree");
  process.exit(1);
}

const tree = StandardMerkleTree.load(JSON.parse(fs.readFileSync(paths.treePath, "utf8")));
const claims = {};

for (const [i, entry] of tree.entries()) {
  const key = entry[0].toLowerCase();
  claims[key] = {
    address: entry[0],
    amount: entry[1],
    leafIndex: i,
    proof: tree.getProof(i),
  };
}

const payload = {
  campaignId: paths.campaignId,
  network: "sepolia",
  merkleRoot: tree.root,
  claims,
};

fs.writeFileSync(paths.proofPath, JSON.stringify(payload, null, 2));

console.log(`Campaign: ${paths.campaignId}`);
console.log(`Merkle root: ${tree.root}`);
console.log(`Saved: ${paths.proofPath}`);
console.log("");
for (const c of Object.values(claims)) {
  console.log(`  ${c.address} (index ${c.leafIndex})`);
}
