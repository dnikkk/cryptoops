import { StandardMerkleTree } from "@openzeppelin/merkle-tree";
import fs from "fs";
import { getCampaignPaths, ensureCampaignDirs } from "./paths.mjs";

const paths = getCampaignPaths();

function parseWhitelist(csvText) {
  const lines = csvText.trim().split(/\r?\n/);
  const header = lines[0].split(",").map((h) => h.trim());
  const rows = lines.slice(1).filter((line) => line.trim().length > 0);

  return rows.map((line, index) => {
    const cols = line.split(",").map((c) => c.trim());
    const record = Object.fromEntries(header.map((key, i) => [key, cols[i]]));

    const address = record.address;
    const humanAmount = BigInt(record.amount);
    const decimals = Number(record.decimals);
    if (!address?.startsWith("0x")) {
      throw new Error(`Row ${index + 2}: invalid address`);
    }
    if (!Number.isInteger(decimals) || decimals < 0) {
      throw new Error(`Row ${index + 2}: invalid decimals`);
    }

    const amount = humanAmount * 10n ** BigInt(decimals);
    return [address, amount.toString()];
  });
}

if (!fs.existsSync(paths.csvPath)) {
  console.error(`Missing: ${paths.csvPath}`);
  console.error(`Copy from campaigns/_template/whitelist.example.csv`);
  process.exit(1);
}

ensureCampaignDirs(paths);

const csv = fs.readFileSync(paths.csvPath, "utf8");
const values = parseWhitelist(csv);
const tree = StandardMerkleTree.of(values, ["address", "uint256"]);

fs.writeFileSync(paths.treePath, JSON.stringify(tree.dump()));

console.log(`Campaign: ${paths.campaignId}`);
console.log("Network: Sepolia");
console.log("Whitelist entries:", values.length);
console.log("");
values.forEach(([address, amount], i) => {
  console.log(`  [${i}] ${address} => ${amount}`);
});
console.log("");
console.log("Merkle Root (update script/Deploy.s.sol before deploy):");
console.log(tree.root);
console.log("");
console.log(`Saved: ${paths.treePath}`);
console.log("Next: npm run get-proof");
