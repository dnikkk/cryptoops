from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent.parent
CRYPTOOPS_ROOT = DASHBOARD_DIR.parent
ENV_FILE = CRYPTOOPS_ROOT / ".env"
CACHE_DIR = DASHBOARD_DIR / "cache"
WALLETS_FILE = DASHBOARD_DIR / "wallets.yaml"
PROTOCOL_FILE = DASHBOARD_DIR / "protocol_addrs.yaml"
CAMPAIGNS_DIR = CRYPTOOPS_ROOT / "campaigns"

CHAIN_ID = 11155111
EXPLORER_BASE = "https://sepolia.etherscan.io"
ETHERSCAN_API = "https://api.etherscan.io/v2/api"

GITHUB_REPO = "https://github.com/dnikkk/cryptoops"
GITHUB_BRANCH = "master"


def github_doc(path: str) -> str:
    """Ссылка на файл в репозитории GitHub."""
    return f"{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path.lstrip('/')}"

DDS_COLUMNS = [
    "datetime",
    "row_level",
    "parent_tx_hash",
    "child_index",
    "leg_type",
    "tx_hash",
    "category",
    "direction",
    "asset",
    "amount",
    "legs_summary",
    "data_warning",
    "value_usd",
    "value_eur",
    "value_eth",
    "value_btc",
    "counterparty",
    "protocol",
    "method",
    "wallet_role",
    "status",
    "notes",
]

NO_PRICE = "—"
