"""
services/ga_client.py – Google Analytics Data API v1 client.

Requires:
  - GA4 Property ID (numeric, e.g. "123456789")
  - Service Account JSON credentials (full JSON string)

The service account must be added as a viewer to the GA4 property.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Optional

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy,
)
from google.oauth2 import service_account


class GA4Client:
    """Thin wrapper around Google Analytics Data API v1beta."""

    SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

    def __init__(self, property_id: str, credentials_json: str) -> None:
        self.property_id = property_id.strip()
        creds_dict = json.loads(credentials_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=self.SCOPES
        )
        self._client = BetaAnalyticsDataClient(credentials=creds)

    def _property(self) -> str:
        return f"properties/{self.property_id}"

    # ── Public methods ─────────────────────────────────────────────

    def get_kpi(self, days: int = 30) -> dict:
        """Return top-level KPIs for the last N days."""
        end = date.today()
        start = end - timedelta(days=days - 1)

        req = RunReportRequest(
            property=self._property(),
            date_ranges=[DateRange(start_date=str(start), end_date=str(end))],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="screenPageViews"),
                Metric(name="averageSessionDuration"),
                Metric(name="bounceRate"),
            ],
        )
        resp = self._client.run_report(req)
        row = resp.rows[0] if resp.rows else None
        if not row:
            return {
                "sessions": 0, "users": 0, "pageviews": 0,
                "avg_session_duration": 0.0, "bounce_rate": 0.0,
            }
        vals = [mv.value for mv in row.metric_values]
        return {
            "sessions":              int(vals[0]),
            "users":                 int(vals[1]),
            "pageviews":             int(vals[2]),
            "avg_session_duration":  round(float(vals[3]), 1),
            "bounce_rate":           round(float(vals[4]) * 100, 1),
        }

    def get_daily(self, days: int = 30) -> list[dict]:
        """Return sessions + users per day for the last N days."""
        end = date.today()
        start = end - timedelta(days=days - 1)

        req = RunReportRequest(
            property=self._property(),
            date_ranges=[DateRange(start_date=str(start), end_date=str(end))],
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
            ],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
        )
        resp = self._client.run_report(req)
        result = []
        for row in resp.rows:
            raw_date = row.dimension_values[0].value  # "20240301"
            formatted = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            result.append({
                "date":     formatted,
                "sessions": int(row.metric_values[0].value),
                "users":    int(row.metric_values[1].value),
            })
        return result

    def get_top_pages(self, days: int = 30, limit: int = 10) -> list[dict]:
        """Return top N pages by screenPageViews."""
        end = date.today()
        start = end - timedelta(days=days - 1)

        req = RunReportRequest(
            property=self._property(),
            date_ranges=[DateRange(start_date=str(start), end_date=str(end))],
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
            ],
            order_bys=[OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"),
                desc=True,
            )],
            limit=limit,
        )
        resp = self._client.run_report(req)
        return [
            {
                "page":  row.dimension_values[0].value,
                "views": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
            }
            for row in resp.rows
        ]

    def get_devices(self, days: int = 30) -> list[dict]:
        """Return session breakdown by device category."""
        end = date.today()
        start = end - timedelta(days=days - 1)

        req = RunReportRequest(
            property=self._property(),
            date_ranges=[DateRange(start_date=str(start), end_date=str(end))],
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[Metric(name="sessions")],
            order_bys=[OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="sessions"),
                desc=True,
            )],
        )
        resp = self._client.run_report(req)
        rows = [
            {
                "device":   row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
            }
            for row in resp.rows
        ]
        total = sum(r["sessions"] for r in rows) or 1
        for r in rows:
            r["percentage"] = round(r["sessions"] / total * 100, 1)
        return rows
