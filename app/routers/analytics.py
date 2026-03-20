"""
routers/analytics.py – Google Analytics 4 Data API endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import database as db
from app.models import AnalyticsReport, AnalyticsKPI, AnalyticsDailyPoint, AnalyticsTopPage, AnalyticsDeviceRow

router = APIRouter()


@router.get("", response_model=AnalyticsReport)
async def get_analytics(days: int = 30):
    """
    Return GA4 metrics for the last N days.
    Requires ga4_property_id and ga4_credentials_json to be configured in settings.
    """
    settings = await db.get_settings()
    property_id = settings.get("ga4_property_id", "").strip()
    credentials_json = settings.get("ga4_credentials_json", "").strip()

    if not property_id or not credentials_json:
        return AnalyticsReport(
            period_days=days,
            kpi=AnalyticsKPI(),
            configured=False,
            error="GA4 no configurado. Ingresá el Property ID y credenciales en Configuración.",
        )

    try:
        from app.services.ga_client import GA4Client
        client = GA4Client(property_id=property_id, credentials_json=credentials_json)

        kpi_raw  = client.get_kpi(days=days)
        daily_raw = client.get_daily(days=days)
        pages_raw = client.get_top_pages(days=days, limit=10)
        devs_raw  = client.get_devices(days=days)

        return AnalyticsReport(
            period_days=days,
            configured=True,
            kpi=AnalyticsKPI(**kpi_raw),
            daily=[AnalyticsDailyPoint(**d) for d in daily_raw],
            top_pages=[AnalyticsTopPage(**p) for p in pages_raw],
            devices=[AnalyticsDeviceRow(**d) for d in devs_raw],
        )

    except Exception as exc:
        return AnalyticsReport(
            period_days=days,
            kpi=AnalyticsKPI(),
            configured=True,
            error=str(exc),
        )


@router.post("/test", response_model=dict)
async def test_ga4():
    """Test GA4 connection using saved credentials."""
    settings = await db.get_settings()
    property_id = settings.get("ga4_property_id", "").strip()
    credentials_json = settings.get("ga4_credentials_json", "").strip()

    if not property_id or not credentials_json:
        return {"success": False, "message": "GA4 no configurado: falta Property ID o credenciales"}

    try:
        from app.services.ga_client import GA4Client
        client = GA4Client(property_id=property_id, credentials_json=credentials_json)
        kpi = client.get_kpi(days=7)
        return {
            "success": True,
            "message": f"Conexión exitosa — {kpi['sessions']} sesiones en los últimos 7 días",
            "details": kpi,
        }
    except Exception as exc:
        return {"success": False, "message": f"Error: {exc}"}
