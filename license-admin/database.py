"""
license-admin/database.py – SQLite persistence for the license admin panel.
"""

from __future__ import annotations

import aiosqlite
import uuid
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "data" / "licenses.db"


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS licenses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                key          TEXT NOT NULL UNIQUE,
                client_name  TEXT NOT NULL,
                client_email TEXT NOT NULL DEFAULT '',
                notes        TEXT DEFAULT '',
                status       TEXT NOT NULL DEFAULT 'active',
                created_at   TEXT NOT NULL,
                expires_at   TEXT,
                last_seen    TEXT
            );
        """)
        await db.commit()
    finally:
        await db.close()


# ── CRUD ──────────────────────────────────────────────────────

async def create_license(client_name: str, client_email: str, notes: str, expires_at: str | None) -> dict:
    key = str(uuid.uuid4())
    now = datetime.now().isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO licenses (key, client_name, client_email, notes, status, created_at, expires_at)
               VALUES (?, ?, ?, ?, 'active', ?, ?)""",
            (key, client_name, client_email, notes, now, expires_at),
        )
        await db.commit()
        row_id = cursor.lastrowid
        cursor2 = await db.execute("SELECT * FROM licenses WHERE id = ?", (row_id,))
        row = await cursor2.fetchone()
        return dict(row)
    finally:
        await db.close()


async def list_licenses() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM licenses ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_license_by_id(license_id: int) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM licenses WHERE id = ?", (license_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def get_license_by_key(key: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM licenses WHERE key = ?", (key,))
        row = await cursor.fetchone()
        if row:
            # Update last_seen
            await db.execute("UPDATE licenses SET last_seen = ? WHERE key = ?",
                             (datetime.now().isoformat(), key))
            await db.commit()
        return dict(row) if row else None
    finally:
        await db.close()


async def revoke_license(license_id: int) -> bool:
    db = await get_db()
    try:
        await db.execute("UPDATE licenses SET status = 'revoked' WHERE id = ?", (license_id,))
        await db.commit()
        return True
    finally:
        await db.close()


async def restore_license(license_id: int) -> bool:
    db = await get_db()
    try:
        await db.execute("UPDATE licenses SET status = 'active' WHERE id = ?", (license_id,))
        await db.commit()
        return True
    finally:
        await db.close()


async def update_license(license_id: int, client_name: str, client_email: str,
                          notes: str, expires_at: str | None) -> bool:
    db = await get_db()
    try:
        await db.execute(
            """UPDATE licenses SET client_name=?, client_email=?, notes=?, expires_at=?
               WHERE id=?""",
            (client_name, client_email, notes, expires_at, license_id),
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def delete_license(license_id: int) -> bool:
    db = await get_db()
    try:
        await db.execute("DELETE FROM licenses WHERE id = ?", (license_id,))
        await db.commit()
        return True
    finally:
        await db.close()
