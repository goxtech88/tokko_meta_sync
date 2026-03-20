"""
models.py – Pydantic schemas for API request/response bodies.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List


# ── Settings ──────────────────────────────────────────────────

class SettingsPayload(BaseModel):
    tokko_api_key: str = Field("", description="Tokko Broker API Key")
    tokko_company_id: str = Field("", description="Tokko Broker Company ID")
    meta_app_id: str = Field("", description="Meta App ID")
    meta_app_secret: str = Field("", description="Meta App Secret")
    meta_access_token: str = Field("", description="Meta Access Token")
    meta_business_id: str = Field("", description="Meta Business Manager ID")
    meta_catalog_id: str = Field("", description="Existing catalog ID (optional)")
    property_base_url: str = Field("", description="Base URL for property pages")
    sync_operation_type: str = Field("sale", description="sale | rent | all")
    # Google Analytics 4
    ga4_property_id: str = Field("", description="GA4 Property ID (numeric)")
    ga4_credentials_json: str = Field("", description="GA4 Service Account JSON (full JSON string)")
    # License Admin Server
    license_server_url: str = Field("", description="URL del servidor de licencias (ej: http://localhost:8001)")


class SettingsResponse(BaseModel):
    tokko_api_key: str = ""
    tokko_company_id: str = ""
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_access_token: str = ""
    meta_business_id: str = ""
    meta_catalog_id: str = ""
    property_base_url: str = ""
    sync_operation_type: str = "sale"
    tokko_configured: bool = False
    meta_configured: bool = False
    # Google Analytics 4
    ga4_property_id: str = ""
    ga4_credentials_json: str = ""
    ga4_configured: bool = False
    # License Admin Server
    license_server_url: str = ""


# ── Sync ──────────────────────────────────────────────────────

class SyncRecord(BaseModel):
    id: int
    started_at: str
    finished_at: Optional[str] = None
    status: str = "running"
    fetched: int = 0
    mapped: int = 0
    skipped: int = 0
    upload_id: str = ""
    error: Optional[str] = None


class SyncRunResponse(BaseModel):
    message: str
    sync_id: int


# ── License ───────────────────────────────────────────────────

class LicenseActivateRequest(BaseModel):
    key: str


class LicenseStatus(BaseModel):
    active: bool = False
    activated: Optional[str] = None
    expires: Optional[str] = None
    expired: bool = False
    client_name: Optional[str] = None


# ── Analytics ─────────────────────────────────────────────────

class AnalyticsKPI(BaseModel):
    sessions: int = 0
    users: int = 0
    pageviews: int = 0
    avg_session_duration: float = 0.0
    bounce_rate: float = 0.0


class AnalyticsDailyPoint(BaseModel):
    date: str
    sessions: int
    users: int


class AnalyticsTopPage(BaseModel):
    page: str
    views: int
    users: int


class AnalyticsDeviceRow(BaseModel):
    device: str
    sessions: int
    percentage: float


class AnalyticsReport(BaseModel):
    period_days: int = 30
    kpi: AnalyticsKPI
    daily: List[AnalyticsDailyPoint] = []
    top_pages: List[AnalyticsTopPage] = []
    devices: List[AnalyticsDeviceRow] = []
    configured: bool = False
    error: Optional[str] = None


# ── Connection test ───────────────────────────────────────────

class TestResult(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None
