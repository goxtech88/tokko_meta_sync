"""
license-admin/app.py – Admin panel for managing TokkoSync licenses.

Endpoints:
  POST /api/auth/login          → JWT token (admin password)
  GET  /api/licenses            → list all (requires auth)
  POST /api/licenses            → create new (requires auth)
  GET  /api/licenses/{id}       → detail (requires auth)
  PUT  /api/licenses/{id}       → update (requires auth)
  POST /api/licenses/{id}/revoke   → revoke (requires auth)
  POST /api/licenses/{id}/restore  → restore (requires auth)
  DELETE /api/licenses/{id}     → delete permanently (requires auth)
  GET  /api/validate/{key}      → validate key (PUBLIC — for client instances)

Auth: Bearer JWT, signed with ADMIN_SECRET env var.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

import database as db

# ── Config ────────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")  # Change in production!
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production-super-secret-key-tokko-admin")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


# ── Auth helpers ──────────────────────────────────────────────

def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


def get_current_admin(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Token requerido")
    return verify_token(creds.credentials)


# ── Pydantic models ───────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str


class CreateLicenseRequest(BaseModel):
    client_name: str
    client_email: str = ""
    notes: str = ""
    expires_at: Optional[str] = None  # ISO date string or None for no expiry


class UpdateLicenseRequest(BaseModel):
    client_name: str
    client_email: str = ""
    notes: str = ""
    expires_at: Optional[str] = None


# ── App ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(
    title="TokkoSync License Admin",
    description="Panel de administración de licencias para TokkoSync",
    version="1.0.0",
    lifespan=lifespan,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


# ── Auth ──────────────────────────────────────────────────────

@app.post("/api/auth/login")
async def login(body: LoginRequest):
    """Authenticate admin and return JWT."""
    if body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    token = create_token({"sub": "admin"})
    return {"token": token, "expires_in": TOKEN_EXPIRE_HOURS * 3600}


# ── License CRUD ──────────────────────────────────────────────

@app.get("/api/licenses")
async def list_licenses(_: dict = Depends(get_current_admin)):
    """List all licenses."""
    licenses = await db.list_licenses()
    # Enrich with computed status
    now = datetime.now()
    for lic in licenses:
        if lic["status"] == "active" and lic.get("expires_at"):
            exp = datetime.fromisoformat(lic["expires_at"])
            if now > exp:
                lic["computed_status"] = "expired"
            else:
                lic["computed_status"] = "active"
        else:
            lic["computed_status"] = lic["status"]
    return {"licenses": licenses, "total": len(licenses)}


@app.post("/api/licenses", status_code=201)
async def create_license(body: CreateLicenseRequest, _: dict = Depends(get_current_admin)):
    """Create a new license key."""
    license_record = await db.create_license(
        client_name=body.client_name,
        client_email=body.client_email,
        notes=body.notes,
        expires_at=body.expires_at,
    )
    return license_record


@app.get("/api/licenses/{license_id}")
async def get_license(license_id: int, _: dict = Depends(get_current_admin)):
    """Get a specific license."""
    lic = await db.get_license_by_id(license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    return lic


@app.put("/api/licenses/{license_id}")
async def update_license(license_id: int, body: UpdateLicenseRequest, _: dict = Depends(get_current_admin)):
    """Update license metadata."""
    lic = await db.get_license_by_id(license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    await db.update_license(license_id, body.client_name, body.client_email,
                             body.notes, body.expires_at)
    return {"message": "Licencia actualizada"}


@app.post("/api/licenses/{license_id}/revoke")
async def revoke_license(license_id: int, _: dict = Depends(get_current_admin)):
    """Revoke a license (blocks access immediately)."""
    lic = await db.get_license_by_id(license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    await db.revoke_license(license_id)
    return {"message": "Licencia revocada"}


@app.post("/api/licenses/{license_id}/restore")
async def restore_license(license_id: int, _: dict = Depends(get_current_admin)):
    """Restore a revoked license."""
    lic = await db.get_license_by_id(license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    await db.restore_license(license_id)
    return {"message": "Licencia reactivada"}


@app.delete("/api/licenses/{license_id}")
async def delete_license(license_id: int, _: dict = Depends(get_current_admin)):
    """Permanently delete a license."""
    lic = await db.get_license_by_id(license_id)
    if not lic:
        raise HTTPException(status_code=404, detail="Licencia no encontrada")
    await db.delete_license(license_id)
    return {"message": "Licencia eliminada"}


# ── PUBLIC: validation endpoint (called by client instances) ──

@app.get("/api/validate/{key}")
async def validate_license(key: str):
    """
    PUBLIC endpoint — called by TokkoSync instances to validate their license.
    Returns: { valid: bool, client_name?, expires_at?, reason? }
    """
    lic = await db.get_license_by_key(key.strip())
    if not lic:
        return {"valid": False, "reason": "Licencia no encontrada"}

    if lic["status"] == "revoked":
        return {"valid": False, "reason": "Licencia revocada"}

    if lic.get("expires_at"):
        exp = datetime.fromisoformat(lic["expires_at"])
        if datetime.now() > exp:
            return {"valid": False, "reason": "Licencia vencida", "expired_at": lic["expires_at"]}

    return {
        "valid": True,
        "client_name": lic["client_name"],
        "expires_at": lic.get("expires_at"),
    }


# ── Stats endpoint ─────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats(_: dict = Depends(get_current_admin)):
    """Dashboard stats."""
    licenses = await db.list_licenses()
    now = datetime.now()
    total = len(licenses)
    active = 0
    revoked = 0
    expired = 0
    for lic in licenses:
        if lic["status"] == "revoked":
            revoked += 1
        elif lic.get("expires_at") and now > datetime.fromisoformat(lic["expires_at"]):
            expired += 1
        else:
            active += 1
    return {"total": total, "active": active, "revoked": revoked, "expired": expired}


# ── Static SPA ────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
