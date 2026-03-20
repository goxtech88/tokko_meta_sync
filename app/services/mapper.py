"""
services/mapper.py – Transform Tokko Broker properties → Meta Home Listing CSV feed.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "output"
FEED_CSV_PATH = OUTPUT_DIR / "feed.csv"

META_COLUMNS = [
    "home_listing_id", "name", "availability", "price",
    "image[0].url", "url",
    "address.addr1", "address.city", "address.region", "address.country",
    "latitude", "longitude",
    "property_type", "listing_type",
]

_PROPERTY_TYPE_MAP: dict[str, str] = {
    "Casa": "house", "Departamento": "apartment", "PH": "apartment",
    "Terreno": "land", "Lote": "land", "Local": "other", "Oficina": "other",
    "Galpón": "other", "Galpon": "other", "Campo": "land", "Cochera": "other",
    "Depósito": "other", "Deposito": "other", "Fondo de Comercio": "other",
    "Hotel": "other", "Consultorio": "other",
}


def _extract_price(prop: dict) -> tuple[str, str]:
    for op in (prop.get("operations") or []):
        prices = op.get("prices") or []
        if prices:
            return str(prices[0].get("price", "")), str(prices[0].get("currency", "USD"))
    return "", "USD"


def _extract_images(prop: dict, max_images: int = 5) -> list[str]:
    urls: list[str] = []
    for photo in (prop.get("photos") or [])[:max_images]:
        url = photo.get("image") or photo.get("original") or photo.get("url") or ""
        if url:
            urls.append(url)
    return urls


def _extract_location(prop: dict) -> dict[str, str]:
    loc = prop.get("location") or {}
    full = loc.get("full_location", "") or ""
    parts = [p.strip() for p in full.split(",")]
    return {
        "address": parts[0] if parts else loc.get("address", ""),
        "city": parts[-3] if len(parts) >= 3 else (parts[1] if len(parts) > 1 else ""),
        "region": parts[-2] if len(parts) >= 2 else "",
        "country": parts[-1] if parts else "AR",
    }


def _extract_property_type(prop: dict) -> str:
    type_obj = prop.get("type") or prop.get("property_type")
    pt = type_obj.get("name", "") if isinstance(type_obj, dict) else (type_obj or "")
    return _PROPERTY_TYPE_MAP.get(pt, "other")


def _format_price(price: str, currency: str) -> str:
    """Format price as Meta expects: '150000.00 USD'."""
    if not price:
        return ""
    try:
        num = float(str(price).replace(",", ""))
        return f"{num:.2f} {currency}"
    except (ValueError, TypeError):
        return f"{price} {currency}"


def map_tokko_to_meta(prop: dict, property_base_url: str = "") -> dict[str, str]:
    price, currency = _extract_price(prop)
    images = _extract_images(prop, max_images=1)
    location = _extract_location(prop)
    prop_id = str(prop.get("id", ""))
    base = property_base_url.rstrip("/")

    return {
        "home_listing_id": prop_id,
        "name": prop.get("publication_title", "") or prop.get("address", ""),
        "availability": "for_sale",
        "price": _format_price(price, currency),
        "image[0].url": images[0] if images else "",
        "url": f"{base}/{prop_id}" if base else "",
        "address.addr1": location["address"],
        "address.city": location["city"],
        "address.region": location["region"],
        "address.country": location["country"],
        "latitude": str(prop.get("geo_lat", "") or ""),
        "longitude": str(prop.get("geo_long", "") or ""),
        "property_type": _extract_property_type(prop),
        "listing_type": "for_sale_by_agent",
    }


def generate_csv_feed(
    properties: list[dict],
    property_base_url: str = "",
    output_path: Path | None = None,
) -> Path:
    out = output_path or FEED_CSV_PATH
    out.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    skipped = 0
    for prop in properties:
        try:
            row = map_tokko_to_meta(prop, property_base_url)
            if not row["price"] or not row["image[0].url"]:
                skipped += 1
                continue
            rows.append(row)
        except Exception:
            logger.exception("Error mapping property id=%s", prop.get("id"))
            skipped += 1

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=META_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("CSV → %s  (%d ok, %d skipped)", out, len(rows), skipped)
    return out
