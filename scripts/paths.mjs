import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.join(__dirname, "..");
const CAMPAIGNS_DIR = path.join(PROJECT_ROOT, "campaigns");
const ACTIVE_FILE = path.join(CAMPAIGNS_DIR, "active.json");

export const DEFAULT_CAMPAIGN_ID = "eftihia-sepolia-001";

function readActiveCampaignId() {
  if (!fs.existsSync(ACTIVE_FILE)) return DEFAULT_CAMPAIGN_ID;
  try {
    const active = JSON.parse(fs.readFileSync(ACTIVE_FILE, "utf8"));
    return active.campaignId?.trim() || DEFAULT_CAMPAIGN_ID;
  } catch {
    return DEFAULT_CAMPAIGN_ID;
  }
}

/**
 * All campaign data lives under campaigns/{id}/:
 *   whitelist.csv, output/tree.json, output/proof.json, deploy.json
 */
export function getCampaignPaths() {
  const campaignId = process.env.CAMPAIGN_ID?.trim() || readActiveCampaignId();
  const base = path.join(CAMPAIGNS_DIR, campaignId);

  return {
    campaignId,
    base,
    csvPath: path.join(base, "whitelist.csv"),
    outDir: path.join(base, "output"),
    treePath: path.join(base, "output", "tree.json"),
    proofPath: path.join(base, "output", "proof.json"),
    deployPath: path.join(base, "deploy.json"),
  };
}

export function ensureCampaignDirs(paths) {
  fs.mkdirSync(paths.outDir, { recursive: true });
  fs.mkdirSync(paths.base, { recursive: true });
}
