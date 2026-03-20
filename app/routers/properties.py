"""
routers/properties.py – List properties from Tokko Broker.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app import database as db
from app.models import TestResult

router = APIRouter()


@router.get("")
async def list_properties(
    limit: int = Query(50, ge=1, le=200),
    operation: str = Query(None, description="sale | rent | all"),
):
    """Fetch properties from Tokko Broker API."""
    api_key = await db.get_setting("tokko_api_key")
    if not api_key:
        return {"error": "Tokko API Key no configurada", "properties": []}

    try:
        from app.services.tokko_client import TokkoClient

        client = TokkoClient(api_key=api_key)
        op = operation or await db.get_setting("sync_operation_type", "sale")
        props = client.get_properties(operation_type=op, limit=limit)

        # Simplify each property for the frontend
        simplified = []
        for p in props:
            ops = p.get("operations") or []
            price_str = ""
            currency = ""
            if ops:
                prices = ops[0].get("prices") or []
                if prices:
                    price_str = str(prices[0].get("price", ""))
                    currency = prices[0].get("currency", "")

            ptype = ""
            type_obj = p.get("type") or p.get("property_type")
            if isinstance(type_obj, dict):
                ptype = type_obj.get("name", "")
            elif isinstance(type_obj, str):
                ptype = type_obj

            photos = p.get("photos") or []
            loc = p.get("location") or {}
            thumb = photos[0].get("thumb", photos[0].get("image", "")) if photos else ""

            simplified.append({
                "id": p.get("id"),
                "title": p.get("publication_title") or p.get("address", "—"),
                "type": ptype,
                "price": price_str,
                "currency": currency,
                "address": loc.get("full_location", p.get("address", "")),
                "thumbnail": thumb,
                "photos_count": len(photos),
                "bedrooms": p.get("suite_amount"),
                "bathrooms": p.get("bathroom_amount"),
                "surface": p.get("roofed_surface") or p.get("total_surface"),
            })

        return {"count": len(simplified), "properties": simplified}

    except Exception as exc:
        return {"error": str(exc), "properties": []}
