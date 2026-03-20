"""
tokko_client.py – Tokko Broker REST API client
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

import config

logger = logging.getLogger(__name__)

# ─── Tokko operation type codes ──────────────────────────────
_OP_MAP = {
    "sale": 1,
    "rent": 2,
}


class TokkoClient:
    """Lightweight wrapper around the Tokko Broker public API."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or config.TOKKO_API_KEY
        self.base_url = (base_url or config.TOKKO_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ── helpers ───────────────────────────────────────────────

    def _params(self, extra: dict | None = None) -> dict:
        """Common query-string parameters."""
        params: dict[str, Any] = {
            "key": self.api_key,
            "format": "json",
            "lang": "es_ar",
        }
        if extra:
            params.update(extra)
        return params

    def _get(self, path: str, params: dict | None = None) -> dict:
        """Issue a GET and return parsed JSON, with retry on 429."""
        url = f"{self.base_url}{path}"
        merged = self._params(params)
        for attempt in range(3):
            resp = self.session.get(url, params=merged, timeout=30)
            if resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning("Rate-limited by Tokko API, retrying in %ds …", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        resp.raise_for_status()
        return {}  # unreachable

    # ── public API ────────────────────────────────────────────

    def get_properties(
        self,
        operation_type: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Fetch all published properties, optionally filtered by operation type
        (``sale`` / ``rent`` / ``all``).  Handles pagination automatically.
        """
        offset = 0
        all_properties: list[dict] = []

        op_type = operation_type or config.SYNC_OPERATION_TYPE

        while True:
            extra: dict[str, Any] = {"limit": limit, "offset": offset}

            # Use the search endpoint when filtering by operation
            if op_type and op_type != "all":
                op_code = _OP_MAP.get(op_type)
                if op_code is None:
                    raise ValueError(
                        f"Unknown operation_type '{op_type}'. Use: sale, rent, all"
                    )
                extra["operation_types"] = f"[{op_code}]"
                path = "/property/search"
            else:
                path = "/property/"

            data = self._get(path, extra)
            objects = data.get("objects", data.get("results", []))

            if not objects:
                break

            all_properties.extend(objects)
            logger.info(
                "Fetched %d properties (total so far: %d)",
                len(objects),
                len(all_properties),
            )

            # Check if there are more pages
            meta = data.get("meta", {})
            next_url = meta.get("next")
            if not next_url:
                break

            offset += limit

        logger.info("Total properties fetched: %d", len(all_properties))
        return all_properties

    def get_property(self, property_id: int) -> dict:
        """Fetch a single property by its Tokko ID."""
        return self._get(f"/property/{property_id}/")
