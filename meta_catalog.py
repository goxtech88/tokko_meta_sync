"""
meta_catalog.py – Meta Ads Home Listing catalog manager
Uses the ``facebook-business`` Python SDK.
"""

from __future__ import annotations

import logging
from pathlib import Path

from facebook_business.adobjects.business import Business
from facebook_business.adobjects.productcatalog import ProductCatalog
from facebook_business.adobjects.productfeed import ProductFeed
from facebook_business.adobjects.productfeedupload import ProductFeedUpload
from facebook_business.api import FacebookAdsApi

import config

logger = logging.getLogger(__name__)


class MetaCatalogManager:
    """Create / manage a Meta Ads Home Listing catalog and upload CSV feeds."""

    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        access_token: str | None = None,
        business_id: str | None = None,
        catalog_id: str | None = None,
    ):
        self.app_id = app_id or config.META_APP_ID
        self.app_secret = app_secret or config.META_APP_SECRET
        self.access_token = access_token or config.META_ACCESS_TOKEN
        self.business_id = business_id or config.META_BUSINESS_ID
        self.catalog_id = catalog_id or config.META_CATALOG_ID

        # Initialize the SDK
        FacebookAdsApi.init(self.app_id, self.app_secret, self.access_token)
        logger.info("Meta Ads API initialized for business %s", self.business_id)

    # ── catalog ───────────────────────────────────────────────

    def get_or_create_catalog(self, name: str = "Propiedades en Venta") -> str:
        """
        Return existing catalog ID or create a new ``home_listings`` catalog
        under the configured Business Manager.
        """
        if self.catalog_id:
            logger.info("Using existing catalog ID: %s", self.catalog_id)
            return self.catalog_id

        business = Business(self.business_id)

        # Check if a catalog with this name already exists
        existing = business.get_owned_product_catalogs(
            fields=["id", "name", "vertical"]
        )
        for cat in existing:
            if cat.get("name") == name and cat.get("vertical") == "home_listings":
                self.catalog_id = cat["id"]
                logger.info("Found existing catalog '%s' → %s", name, self.catalog_id)
                return self.catalog_id

        # Create new catalog
        catalog = business.create_owned_product_catalog(
            params={
                "name": name,
                "vertical": "home_listings",
            }
        )
        self.catalog_id = catalog["id"]
        logger.info("Created new catalog '%s' → %s", name, self.catalog_id)
        return self.catalog_id

    # ── feed management ───────────────────────────────────────

    def _get_or_create_feed(self, feed_name: str = "tokko_sync_feed") -> ProductFeed:
        """Return or create a product feed inside the catalog."""
        catalog = ProductCatalog(self.catalog_id)

        # Look for existing feed
        feeds = catalog.get_product_feeds(fields=["id", "name"])
        for f in feeds:
            if f.get("name") == feed_name:
                logger.info("Reusing existing feed '%s' → %s", feed_name, f["id"])
                return f

        # Create new feed
        feed = catalog.create_product_feed(
            params={
                "name": feed_name,
                "encoding": "UTF_8",
            }
        )
        logger.info("Created new feed '%s' → %s", feed_name, feed["id"])
        return feed

    def upload_feed(self, csv_path: Path | None = None) -> dict:
        """
        Upload a local CSV file to the catalog's product feed.
        Returns upload status info.
        """
        csv_file = csv_path or config.FEED_CSV_PATH

        if not csv_file.exists():
            raise FileNotFoundError(f"Feed CSV not found: {csv_file}")

        self.get_or_create_catalog()
        feed = self._get_or_create_feed()

        # Upload the file
        upload = feed.create_upload(
            params={
                "update_only": False,
            },
            files={
                "file": (csv_file.name, open(csv_file, "rb"), "text/csv"),
            },
        )

        logger.info("Feed upload initiated → %s", upload.get("id"))
        return dict(upload)

    # ── listing info ─────────────────────────────────────────

    def get_catalog_items(self, limit: int = 50) -> list[dict]:
        """List current items in the catalog."""
        if not self.catalog_id:
            self.get_or_create_catalog()

        catalog = ProductCatalog(self.catalog_id)
        items = catalog.get_products(
            fields=["id", "name", "price", "availability", "url", "image_url"],
            params={"limit": limit},
        )
        return [dict(item) for item in items]
