"""
database.py – SQLite database for settings, sync history, and license.
Uses raw aiosqlite for simplicity (no ORM needed for this scale).
"""

from __future__ import annotations

import aiosqlite
import json
import hashlib
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db() -> None:
    """Create tables if they don't exist."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sync_history (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at    TEXT NOT NULL,
                finished_at   TEXT,
                status        TEXT NOT NULL DEFAULT 'running',
                fetched       INTEGER DEFAULT 0,
                mapped        INTEGER DEFAULT 0,
                skipped       INTEGER DEFAULT 0,
                upload_id     TEXT,
                error         TEXT
            );

            CREATE TABLE IF NOT EXISTS license (
                id         INTEGER PRIMARY KEY CHECK (id = 1),
                key_hash   TEXT NOT NULL,
                activated  TEXT NOT NULL,
                expires    TEXT
            );
        """)
        await db.commit()
    finally:
        await db.close()


# ── Settings helpers ──────────────────────────────────────────

async def get_settings() -> dict[str, str]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {row["key"]: row["value"] for row in rows}
    finally:
        await db.close()


async def save_settings(data: dict[str, str]) -> None:
    db = await get_db()
    try:
        for k, v in data.items():
            await db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (k, v),
            )
        await db.commit()
    finally:
        await db.close()


async def get_setting(key: str, default: str = "") -> str:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else default
    finally:
        await db.close()


# ── Sync history helpers ──────────────────────────────────────

async def create_sync_record() -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO sync_history (started_at, status) VALUES (?, 'running')",
            (datetime.now().isoformat(),),
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def update_sync_record(
    record_id: int,
    status: str = "done",
    fetched: int = 0,
    mapped: int = 0,
    skipped: int = 0,
    upload_id: str = "",
    error: str | None = None,
) -> None:
    db = await get_db()
    try:
        await db.execute(
            """UPDATE sync_history
               SET finished_at = ?, status = ?, fetched = ?, mapped = ?,
                   skipped = ?, upload_id = ?, error = ?
               WHERE id = ?""",
            (
                datetime.now().isoformat(), status, fetched, mapped,
                skipped, upload_id, error, record_id,
            ),
        )
        await db.commit()
    finally:
        await db.close()


async def get_sync_history(limit: int = 20) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM sync_history ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


# ── License helpers ───────────────────────────────────────────

def _hash_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode()).hexdigest()


async def activate_license(key: str, expires: str | None = None) -> bool:
    """Store license key hash. Returns True on success."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO license (id, key_hash, activated, expires) VALUES (1, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET key_hash = excluded.key_hash, "
            "activated = excluded.activated, expires = excluded.expires",
            (_hash_key(key), datetime.now().isoformat(), expires),
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def check_license() -> dict:
    """Return license status."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM license WHERE id = 1")
        row = await cursor.fetchone()
        if not row:
            return {"active": False}
        result = {"active": True, "activated": row["activated"]}
        if row["expires"]:
            exp = datetime.fromisoformat(row["expires"])
            result["expires"] = row["expires"]
            result["expired"] = datetime.now() > exp
            if result["expired"]:
                result["active"] = False
        return result
    finally:
        await db.close()
