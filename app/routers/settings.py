"""
routers/settings.py – CRUD for API credentials.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import database as db
from app.models import SettingsPayload, SettingsResponse, TestResult

router = APIRouter()

_FIELDS = [
    "tokko_api_key", "tokko_company_id", "meta_app_id", "meta_app_secret",
    "meta_access_token", "meta_business_id", "meta_catalog_id",
    "property_base_url", "sync_operation_type",
    "ga4_property_id", "ga4_credentials_json",
    "license_server_url",
]

# Fields that are NOT masked (plain text display)
_PLAIN_FIELDS = {"tokko_company_id", "meta_catalog_id", "property_base_url",
                 "sync_operation_type", "ga4_property_id", "license_server_url"}


def _mask(value: str) -> str:
    """Show only last 4 chars of sensitive values."""
    if len(value) <= 4:
        return "****"
    return "•" * min(len(value) - 4, 20) + value[-4:]


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Return current settings (sensitive values masked)."""
    raw = await db.get_settings()

    def _safe(key: str) -> str:
        val = raw.get(key, "")
        if not val:
            return ""
        if key in _PLAIN_FIELDS:
            return val
        return _mask(val)

    resp = SettingsResponse(
        tokko_api_key=_safe("tokko_api_key"),
        tokko_company_id=raw.get("tokko_company_id", ""),
        meta_app_id=_safe("meta_app_id"),
        meta_app_secret=_safe("meta_app_secret"),
        meta_access_token=_safe("meta_access_token"),
        meta_business_id=raw.get("meta_business_id", ""),
        meta_catalog_id=raw.get("meta_catalog_id", ""),
        property_base_url=raw.get("property_base_url", ""),
        sync_operation_type=raw.get("sync_operation_type", "sale"),
        tokko_configured=bool(raw.get("tokko_api_key")),
        meta_configured=bool(raw.get("meta_app_id") and raw.get("meta_access_token")),
        ga4_property_id=raw.get("ga4_property_id", ""),
        ga4_credentials_json="••••••" if raw.get("ga4_credentials_json") else "",
        ga4_configured=bool(raw.get("ga4_property_id") and raw.get("ga4_credentials_json")),
        license_server_url=raw.get("license_server_url", ""),
    )
    return resp


@router.put("")
async def save_settings(payload: SettingsPayload):
    """Save / update API credentials."""
    data = {}
    for field in _FIELDS:
        val = getattr(payload, field, "")
        if not val:
            continue
        # Don't overwrite masked values
        if val.startswith("•") or val == "••••••":
            continue
        data[field] = val
    await db.save_settings(data)
    return {"message": "Settings saved", "count": len(data)}


@router.post("/test-tokko", response_model=TestResult)
async def test_tokko():
    """Test Tokko Broker API connection."""
    from app.services.tokko_client import TokkoClient

    api_key = await db.get_setting("tokko_api_key")
    company_id = await db.get_setting("tokko_company_id")
    if not api_key:
        return TestResult(success=False, message="Tokko API Key no configurada")

    try:
        client = TokkoClient(api_key=api_key, company_id=company_id)
        data = client._get("/property/", {"limit": 1})
        total = data.get("meta", {}).get("total_count", len(data.get("objects", [])))
        sample = (data.get("objects") or [None])[0]
        return TestResult(
            success=True,
            message=f"Conexión exitosa — {total} propiedad(es) disponible(s)",
            details={"sample_id": sample.get("id") if sample else None},
        )
    except Exception as e:
        return TestResult(success=False, message=f"Error: {e}")


@router.post("/test-meta", response_model=TestResult)
async def test_meta():
    """Test Meta Ads API connection."""
    settings = await db.get_settings()
    required = ["meta_app_id", "meta_app_secret", "meta_access_token", "meta_business_id"]
    missing = [k for k in required if not settings.get(k)]
    if missing:
        return TestResult(success=False, message=f"Faltan credenciales: {', '.join(missing)}")

    try:
        from app.services.meta_catalog import MetaCatalogManager
        meta = MetaCatalogManager(
            app_id=settings["meta_app_id"],
            app_secret=settings["meta_app_secret"],
            access_token=settings["meta_access_token"],
            business_id=settings["meta_business_id"],
            catalog_id=settings.get("meta_catalog_id", ""),
        )
        catalog_id = meta.get_or_create_catalog()
        return TestResult(
            success=True,
            message=f"Conexión exitosa — Catalog ID: {catalog_id}",
            details={"catalog_id": catalog_id},
        )
    except Exception as e:
        return TestResult(success=False, message=f"Error: {e}")


@router.post("/test-ga4", response_model=TestResult)
async def test_ga4():
    """Test Google Analytics 4 Data API connection."""
    settings = await db.get_settings()
    property_id = settings.get("ga4_property_id", "").strip()
    credentials_json = settings.get("ga4_credentials_json", "").strip()

    if not property_id or not credentials_json:
        return TestResult(success=False, message="GA4 Property ID o credenciales no configuradas")

    try:
        from app.services.ga_client import GA4Client
        client = GA4Client(property_id=property_id, credentials_json=credentials_json)
        kpi = client.get_kpi(days=7)
        return TestResult(
            success=True,
            message=f"Conexión exitosa — {kpi['sessions']} sesiones en los últimos 7 días",
            details=kpi,
        )
    except Exception as e:
        return TestResult(success=False, message=f"Error: {e}")
