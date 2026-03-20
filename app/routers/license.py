"""
routers/license.py – License key activation and status.

Validation strategy:
  1. Check local SQLite (always first — fast, works offline).
  2. If a license_server_url is configured, also validate online against
     the license-admin server and refresh local status.
  3. Cache online validation result for 24 h so the app keeps working
     even if the license server is temporarily unreachable.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from fastapi import APIRouter

from app import database as db
from app.models import LicenseActivateRequest, LicenseStatus

router = APIRouter()

# UUID-v4 pattern
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_ONLINE_CACHE_HOURS = 24


async def _validate_online(key: str) -> dict | None:
    """
    Hit the license-admin validation endpoint.
    Returns the parsed JSON response or None on failure.
    """
    server_url = await db.get_setting("license_server_url")
    if not server_url:
        return None

    try:
        import httpx
        url = server_url.rstrip("/") + f"/api/validate/{key}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


@router.get("/status", response_model=LicenseStatus)
async def license_status():
    """Check current license status (local + optional online refresh)."""
    info = await db.check_license()

    if not info.get("active"):
        return LicenseStatus(active=False)

    # Attempt online refresh if cache is stale
    last_online = await db.get_setting("license_last_online_check")
    should_check = True
    if last_online:
        try:
            last_dt = datetime.fromisoformat(last_online)
            if datetime.now() - last_dt < timedelta(hours=_ONLINE_CACHE_HOURS):
                should_check = False
        except ValueError:
            pass

    client_name = await db.get_setting("license_client_name")

    if should_check:
        stored_key = await db.get_setting("license_raw_key")
        if stored_key:
            result = await _validate_online(stored_key)
            if result is not None:
                if not result.get("valid"):
                    # Revoked or expired remotely — deactivate locally
                    await db.save_settings({"license_active": "0"})
                    return LicenseStatus(active=False)
                # Refresh metadata from server
                client_name = result.get("client_name", client_name)
                await db.save_settings({
                    "license_last_online_check": datetime.now().isoformat(),
                    "license_client_name": client_name or "",
                })

    return LicenseStatus(
        active=info.get("active", False),
        activated=info.get("activated"),
        expires=info.get("expires"),
        expired=info.get("expired", False),
        client_name=client_name or None,
    )


@router.post("/activate")
async def activate(body: LicenseActivateRequest):
    """
    Activate a license key.
    1. Validates UUID format.
    2. Checks against online admin server if configured.
    3. Stores locally on success.
    """
    key = body.key.strip()
    if not _UUID_RE.match(key):
        return {"success": False, "message": "Formato inválido. La clave debe ser un UUID."}

    # Try online validation first
    result = await _validate_online(key)
    if result is not None:
        if not result.get("valid"):
            reason = result.get("reason", "Licencia no válida")
            return {"success": False, "message": reason}
        # Valid online — store with expiry from server
        client_name = result.get("client_name", "")
        expires_at = result.get("expires_at")
        ok = await db.activate_license(key, expires=expires_at)
        if ok:
            await db.save_settings({
                "license_raw_key": key,
                "license_client_name": client_name,
                "license_last_online_check": datetime.now().isoformat(),
                "license_active": "1",
            })
            return {"success": True, "message": f"Licencia activada — {client_name}" if client_name else "Licencia activada correctamente"}
        return {"success": False, "message": "Error al guardar la licencia"}

    # No license server configured — accept any valid UUID (offline mode)
    ok = await db.activate_license(key)
    if ok:
        await db.save_settings({"license_raw_key": key})
        return {"success": True, "message": "Licencia activada correctamente (modo offline)"}
    return {"success": False, "message": "Error al activar la licencia"}
