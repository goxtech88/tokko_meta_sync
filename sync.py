"""
sync.py – Orchestrates the full Tokko Broker → Meta Ads catalog sync
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from tokko_client import TokkoClient
from mapper import generate_csv_feed
from meta_catalog import MetaCatalogManager
import config

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Holds summary stats for one sync run."""

    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    tokko_fetched: int = 0
    mapped_ok: int = 0
    skipped: int = 0
    meta_upload_id: str = ""
    error: str | None = None

    @property
    def duration_seconds(self) -> float:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return 0.0


def run_sync(
    operation_type: str | None = None,
    dry_run: bool = False,
) -> SyncResult:
    """
    Execute a full sync cycle:
      1. Fetch properties from Tokko Broker
      2. Map to Meta Home Listing format
      3. Generate CSV feed
      4. Upload to Meta catalog (unless dry_run)
    """
    result = SyncResult()
    op = operation_type or config.SYNC_OPERATION_TYPE

    try:
        # ── Step 1: Fetch from Tokko ─────────────────────────
        logger.info("Step 1/4 – Fetching properties from Tokko Broker (%s) …", op)
        tokko = TokkoClient()
        properties = tokko.get_properties(operation_type=op)
        result.tokko_fetched = len(properties)
        logger.info("  → %d properties fetched", result.tokko_fetched)

        if not properties:
            logger.warning("No properties found. Nothing to sync.")
            result.finished_at = datetime.now()
            return result

        # ── Step 2 & 3: Map + Generate CSV ───────────────────
        logger.info("Step 2/4 – Mapping properties to Meta format …")
        csv_path = generate_csv_feed(properties)
        # Count rows written (header excluded)
        with open(csv_path, encoding="utf-8") as f:
            result.mapped_ok = sum(1 for _ in f) - 1
        result.skipped = result.tokko_fetched - result.mapped_ok
        logger.info(
            "  → CSV feed ready: %d mapped, %d skipped → %s",
            result.mapped_ok,
            result.skipped,
            csv_path,
        )

        # ── Step 4: Upload to Meta ───────────────────────────
        if dry_run:
            logger.info("Step 3/4 – DRY RUN: Skipping Meta upload.")
        else:
            logger.info("Step 3/4 – Uploading feed to Meta Ads catalog …")
            meta = MetaCatalogManager()
            upload_info = meta.upload_feed(csv_path)
            result.meta_upload_id = str(upload_info.get("id", ""))
            logger.info("  → Upload started: %s", result.meta_upload_id)

    except Exception as exc:
        result.error = str(exc)
        logger.exception("Sync failed: %s", exc)

    result.finished_at = datetime.now()
    return result
