"""
config.py – Loads credentials and settings from .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Try to load from working directory
    load_dotenv()


def _require(var_name: str) -> str:
    """Return an env var or exit with a clear error."""
    value = os.getenv(var_name, "").strip()
    if not value:
        print(f"[ERROR] Missing required environment variable: {var_name}")
        print(f"        Copy .env.example → .env and fill in your credentials.")
        sys.exit(1)
    return value


# ── Tokko Broker ──────────────────────────────────────────────
TOKKO_API_KEY: str = _require("TOKKO_API_KEY")
TOKKO_BASE_URL: str = "https://www.tokkobroker.com/api/v1"

# ── Meta / Facebook ──────────────────────────────────────────
META_APP_ID: str = _require("META_APP_ID")
META_APP_SECRET: str = _require("META_APP_SECRET")
META_ACCESS_TOKEN: str = _require("META_ACCESS_TOKEN")
META_BUSINESS_ID: str = _require("META_BUSINESS_ID")
META_CATALOG_ID: str = os.getenv("META_CATALOG_ID", "").strip()

# ── Site ─────────────────────────────────────────────────────
PROPERTY_BASE_URL: str = os.getenv("PROPERTY_BASE_URL", "").strip()

# ── Sync options ─────────────────────────────────────────────
SYNC_OPERATION_TYPE: str = os.getenv("SYNC_OPERATION_TYPE", "sale").strip().lower()

# ── Paths ────────────────────────────────────────────────────
OUTPUT_DIR: Path = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
FEED_CSV_PATH: Path = OUTPUT_DIR / "feed.csv"
