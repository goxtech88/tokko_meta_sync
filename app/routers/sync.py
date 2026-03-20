"""
routers/sync.py – Run sync and view history.
"""

from __future__ import annotations

import asyncio
from fastapi import APIRouter, BackgroundTasks

from app import database as db
from app.models import SyncRecord, SyncRunResponse

router = APIRouter()

# Simple in-memory flag for sync-in-progress
_sync_lock = asyncio.Lock()


async def _run_sync_task(sync_id: int) -> None:
    """Background task that runs the full sync pipeline."""
    settings = await db.get_settings()
    try:
        from app.services.tokko_client import TokkoClient
        from app.services.mapper import generate_csv_feed
        from app.services.meta_catalog import MetaCatalogManager

        # 1. Fetch properties
        client = TokkoClient(
            api_key=settings.get("tokko_api_key", ""),
            company_id=settings.get("tokko_company_id", ""),
        )
        op_type = settings.get("sync_operation_type", "sale")
        properties = client.get_properties(operation_type=op_type)

        # 2. Generate CSV
        csv_path = generate_csv_feed(
            properties,
            property_base_url=settings.get("property_base_url", ""),
        )

        # Count result rows
        with open(csv_path, encoding="utf-8") as f:
            mapped = sum(1 for _ in f) - 1
        skipped = len(properties) - mapped

        # 3. Upload to Meta
        upload_id = ""
        meta_keys = ["meta_app_id", "meta_app_secret", "meta_access_token", "meta_business_id"]
        if all(settings.get(k) for k in meta_keys):
            meta = MetaCatalogManager(
                app_id=settings["meta_app_id"],
                app_secret=settings["meta_app_secret"],
                access_token=settings["meta_access_token"],
                business_id=settings["meta_business_id"],
                catalog_id=settings.get("meta_catalog_id", ""),
            )
            info = meta.upload_feed(csv_path)
            upload_id = str(info.get("id", ""))

        await db.update_sync_record(
            sync_id,
            status="done",
            fetched=len(properties),
            mapped=mapped,
            skipped=skipped,
            upload_id=upload_id,
        )
    except Exception as exc:
        await db.update_sync_record(sync_id, status="error", error=str(exc))


@router.post("/run", response_model=SyncRunResponse)
async def run_sync(background_tasks: BackgroundTasks):
    """Trigger a new sync run (in background)."""
    if _sync_lock.locked():
        return SyncRunResponse(message="Sync ya en ejecución", sync_id=0)

    sync_id = await db.create_sync_record()
    background_tasks.add_task(_run_sync_task, sync_id)
    return SyncRunResponse(message="Sync iniciado", sync_id=sync_id)


@router.get("/history")
async def sync_history():
    """Return recent sync runs."""
    rows = await db.get_sync_history(limit=20)
    return {"history": rows}


@router.get("/status")
async def sync_status():
    """Check if a sync is currently running."""
    rows = await db.get_sync_history(limit=1)
    if rows and rows[0].get("status") == "running":
        return {"running": True, "current": rows[0]}
    return {"running": False}
