"""
main.py – FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routers import settings, sync, properties, license, analytics


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Tokko → Meta Sync",
    description="Sincroniza propiedades de Tokko Broker con Meta Ads Catalog",
    version="2.0.0",
    lifespan=lifespan,
)

# ── API routers ───────────────────────────────────────────────
app.include_router(settings.router,   prefix="/api/settings",   tags=["settings"])
app.include_router(sync.router,       prefix="/api/sync",       tags=["sync"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(license.router,    prefix="/api/license",    tags=["license"])
app.include_router(analytics.router,  prefix="/api/analytics",  tags=["analytics"])

# ── Static files (frontend) ──────────────────────────────────
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the SPA index.html."""
    return FileResponse(str(STATIC_DIR / "index.html"))
