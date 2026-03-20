"""
services/tokko_client.py – Tokko Broker REST API client.
Refactored from CLI version to accept credentials as constructor args.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

_OP_MAP = {"sale": 1, "rent": 2}
_BASE_URL = "https://www.tokkobroker.com/api/v1"


class TokkoClient:
    """Lightweight wrapper around the Tokko Broker public API."""

    def __init__(self, api_key: str, company_id: str = "", base_url: str = _BASE_URL):
        self.api_key = api_key
        self.company_id = company_id
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _params(self, extra: dict | None = None) -> dict:
        params: dict[str, Any] = {
            "key": self.api_key,
            "format": "json",
            "lang": "es_ar",
        }
        if self.company_id:
            params["company_id"] = self.company_id
        if extra:
            params.update(extra)
        return params

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        merged = self._params(params)
        for attempt in range(3):
            resp = self.session.get(url, params=merged, timeout=30)
            if resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning("Rate-limited, retrying in %ds …", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        resp.raise_for_status()
        return {}

    def get_properties(
        self,
        operation_type: str = "sale",
        limit: int = 50,
    ) -> list[dict]:
        offset = 0
        all_properties: list[dict] = []

        while True:
            extra: dict[str, Any] = {"limit": limit, "offset": offset}

            if operation_type and operation_type != "all":
                op_code = _OP_MAP.get(operation_type)
                if op_code is None:
                    raise ValueError(f"Unknown operation_type '{operation_type}'")
                # Tokko search requires a JSON-encoded 'data' parameter
                search_data = {
                    "operation_types": [op_code],
                    "property_types": [],
                    "price_from": 0,
                    "price_to": 999999999,
                    "currency": "USD",
                    "filters": [],
                    "with_tags": [],
                    "without_tags": [],
                    "with_custom_tags": [],
                    "without_custom_tags": [],
                    "current_localization_type": "country",
                    "current_localization_id": [1],
                }
                extra["data"] = json.dumps(search_data)
                path = "/property/search"
            else:
                path = "/property/"

            data = self._get(path, extra)
            objects = data.get("objects", data.get("results", []))
            if not objects:
                break

            all_properties.extend(objects)
            logger.info("Fetched %d (total %d)", len(objects), len(all_properties))

            meta = data.get("meta", {})
            if not meta.get("next"):
                break
            offset += limit

        return all_properties

    def get_property(self, property_id: int) -> dict:
        return self._get(f"/property/{property_id}/")
