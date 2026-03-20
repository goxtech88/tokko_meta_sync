"""
services/meta_catalog.py – Meta Ads Home Listing catalog manager.
Uses the facebook-business Python SDK.
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests as http_requests
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.productcatalog import ProductCatalog
from facebook_business.adobjects.productfeed import ProductFeed
from facebook_business.api import FacebookAdsApi

logger = logging.getLogger(__name__)


class MetaCatalogManager:

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        access_token: str,
        business_id: str,
        catalog_id: str = "",
    ):
        self.business_id = business_id
        self.catalog_id = catalog_id
        FacebookAdsApi.init(app_id, app_secret, access_token)

    def get_or_create_catalog(self, name: str = "Propiedades en Venta") -> str:
        if self.catalog_id:
            return self.catalog_id

        business = Business(self.business_id)
        existing = business.get_owned_product_catalogs(fields=["id", "name", "vertical"])
        for cat in existing:
            if cat.get("name") == name and cat.get("vertical") == "home_listings":
                self.catalog_id = cat["id"]
                return self.catalog_id

        catalog = business.create_owned_product_catalog(
            params={"name": name, "vertical": "home_listings"}
        )
        self.catalog_id = catalog["id"]
        return self.catalog_id

    def _get_or_create_feed(self, feed_name: str = "tokko_sync_feed") -> ProductFeed:
        catalog = ProductCatalog(self.catalog_id)
        feeds = catalog.get_product_feeds(fields=["id", "name"])
        for f in feeds:
            if f.get("name") == feed_name:
                return f
        feed = catalog.create_product_feed(params={"name": feed_name, "encoding": "UTF8"})
        return feed

    def upload_feed(self, csv_path: Path) -> dict:
        if not csv_path.exists():
            raise FileNotFoundError(f"Feed CSV not found: {csv_path}")

        self.get_or_create_catalog()
        feed = self._get_or_create_feed()
        feed_id = feed["id"]

        # Direct Graph API multipart upload (SDK doesn't handle files well)
        api = FacebookAdsApi.get_default_api()
        access_token = api._session.access_token
        url = f"https://graph.facebook.com/v25.0/{feed_id}/uploads"

        with open(csv_path, "rb") as f:
            resp = http_requests.post(
                url,
                params={"access_token": access_token, "update_only": "false"},
                files={"file": (csv_path.name, f, "text/csv")},
                timeout=120,
            )
        resp.raise_for_status()
        return resp.json()

    def get_catalog_items(self, limit: int = 50) -> list[dict]:
        if not self.catalog_id:
            self.get_or_create_catalog()
        catalog = ProductCatalog(self.catalog_id)
        items = catalog.get_products(
            fields=["id", "name", "price", "availability", "url", "image_url"],
            params={"limit": limit},
        )
        return [dict(item) for item in items]
