"""
mapper.py – Transform Tokko Broker property data → Meta Home Listing CSV feed
"""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger(__name__)

# ─── Meta Home Listing CSV columns (required + recommended) ─
META_COLUMNS = [
    "home_listing_id",
    "name",
    "description",
    "availability",
    "price",
    "currency",
    "url",
    "image[0].url",
    "image[0].tag",
    "image[1].url",
    "image[2].url",
    "image[3].url",
    "image[4].url",
    "address",
    "city",
    "region",
    "country",
    "latitude",
    "longitude",
    "num_beds",
    "num_baths",
    "num_rooms",
    "area_size",
    "area_unit",
    "property_type",
    "listing_type",
    "year_built",
]


# ─── Property type mapping ───────────────────────────────────
_PROPERTY_TYPE_MAP: dict[str, str] = {
    "Casa": "house",
    "Departamento": "apartment",
    "PH": "apartment",
    "Terreno": "land",
    "Lote": "land",
    "Local": "other",
    "Oficina": "other",
    "Galpón": "other",
    "Galpon": "other",
    "Campo": "land",
    "Cochera": "other",
    "Depósito": "other",
    "Deposito": "other",
    "Fondo de Comercio": "other",
    "Hotel": "other",
    "Consultorio": "other",
}


def _safe_get(obj: dict, *keys: str, default: Any = "") -> Any:
    """Safely traverse nested dicts/lists."""
    current: Any = obj
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k)
        elif isinstance(current, list):
            try:
                current = current[int(k)]
            except (IndexError, ValueError):
                return default
        else:
            return default
        if current is None:
            return default
    return current


def _extract_price(prop: dict) -> tuple[str, str]:
    """Extract the first sale-operation price and currency."""
    operations = prop.get("operations") or []
    for op in operations:
        prices = op.get("prices") or []
        if prices:
            price = prices[0].get("price", "")
            currency = prices[0].get("currency", "USD")
            return str(price), str(currency)
    return "", "USD"


def _extract_images(prop: dict, max_images: int = 5) -> list[str]:
    """Return up to *max_images* photo URLs from the property."""
    photos = prop.get("photos") or []
    urls: list[str] = []
    for photo in photos[:max_images]:
        url = photo.get("image") or photo.get("original") or photo.get("url") or ""
        if url:
            urls.append(url)
    return urls


def _extract_location(prop: dict) -> dict[str, str]:
    """Extract address parts from Tokko's nested location object."""
    loc = prop.get("location") or {}
    full = loc.get("full_location", "") or ""

    # Tokko usually returns: "Street, Neighborhood, City, Province, Country"
    parts = [p.strip() for p in full.split(",")]

    address = parts[0] if len(parts) > 0 else ""
    city = parts[-3] if len(parts) >= 3 else (parts[1] if len(parts) > 1 else "")
    region = parts[-2] if len(parts) >= 2 else ""
    country = parts[-1] if len(parts) >= 1 else "AR"

    return {
        "address": address or loc.get("address", ""),
        "city": city,
        "region": region,
        "country": country if country else "AR",
    }


def _extract_property_type(prop: dict) -> str:
    """Map Tokko property type to Meta's enum."""
    pt = ""
    type_obj = prop.get("type") or prop.get("property_type")
    if isinstance(type_obj, dict):
        pt = type_obj.get("name", "")
    elif isinstance(type_obj, str):
        pt = type_obj
    return _PROPERTY_TYPE_MAP.get(pt, "other")


def map_tokko_to_meta(prop: dict) -> dict[str, str]:
    """
    Convert a single Tokko Broker property dict into a flat dict
    matching Meta Home Listing CSV columns.
    """
    price, currency = _extract_price(prop)
    images = _extract_images(prop)
    location = _extract_location(prop)
    prop_id = str(prop.get("id", ""))

    # Build property URL
    base_url = config.PROPERTY_BASE_URL.rstrip("/")
    prop_url = f"{base_url}/{prop_id}" if base_url else ""

    # Surface – prefer roofed, fallback to total
    area = prop.get("roofed_surface") or prop.get("total_surface") or ""

    row: dict[str, str] = {
        "home_listing_id": prop_id,
        "name": prop.get("publication_title", "") or prop.get("address", ""),
        "description": (prop.get("description") or "")[:5000],
        "availability": "for_sale",
        "price": price,
        "currency": currency,
        "url": prop_url,
        "image[0].url": images[0] if len(images) > 0 else "",
        "image[0].tag": prop.get("publication_title", "")[:100],
        "image[1].url": images[1] if len(images) > 1 else "",
        "image[2].url": images[2] if len(images) > 2 else "",
        "image[3].url": images[3] if len(images) > 3 else "",
        "image[4].url": images[4] if len(images) > 4 else "",
        "address": location["address"],
        "city": location["city"],
        "region": location["region"],
        "country": location["country"],
        "latitude": str(prop.get("geo_lat", "") or ""),
        "longitude": str(prop.get("geo_long", "") or ""),
        "num_beds": str(prop.get("suite_amount", "") or ""),
        "num_baths": str(prop.get("bathroom_amount", "") or ""),
        "num_rooms": str(prop.get("room_amount", "") or ""),
        "area_size": str(area),
        "area_unit": "sq_m" if area else "",
        "property_type": _extract_property_type(prop),
        "listing_type": "for_sale_by_agent",
        "year_built": str(prop.get("age", "") or ""),
    }
    return row


def generate_csv_feed(
    properties: list[dict],
    output_path: Path | None = None,
) -> Path:
    """
    Map a list of Tokko properties and write them as a Meta-compatible CSV feed.
    Returns the path to the generated file.
    """
    out = output_path or config.FEED_CSV_PATH
    out.parent.mkdir(parents=True, exist_ok=True)

    mapped_rows: list[dict[str, str]] = []
    skipped = 0

    for prop in properties:
        try:
            row = map_tokko_to_meta(prop)
            # Skip rows without a price or images (Meta will reject them)
            if not row["price"] or not row["image[0].url"]:
                logger.warning(
                    "Skipping property %s – missing price or image", row["home_listing_id"]
                )
                skipped += 1
                continue
            mapped_rows.append(row)
        except Exception:
            logger.exception("Error mapping property id=%s", prop.get("id"))
            skipped += 1

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=META_COLUMNS)
        writer.writeheader()
        writer.writerows(mapped_rows)

    logger.info(
        "CSV feed written → %s  (%d properties, %d skipped)", out, len(mapped_rows), skipped
    )
    return out
