"""SQLite job state.

In-memory state means a restart loses everything. When paid API calls are in the
pipeline, that is not an inconvenience — it is money on the floor.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id           TEXT PRIMARY KEY,
    mode         TEXT NOT NULL,
    brand        TEXT NOT NULL,
    topic        TEXT NOT NULL,
    status       TEXT NOT NULL,
    spend_usd    REAL NOT NULL DEFAULT 0,
    created_at   REAL NOT NULL,
    updated_at   REAL NOT NULL,
    payload      TEXT
);

CREATE TABLE IF NOT EXISTS assets (
    hash         TEXT PRIMARY KEY,
    job_id       TEXT NOT NULL,
    tier         TEXT NOT NULL,
    model        TEXT NOT NULL,
    path         TEXT NOT NULL,
    cost_usd     REAL NOT NULL,
    created_at   REAL NOT NULL
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def create_job(conn: sqlite3.Connection, job_id: str, mode: str, brand: str, topic: str) -> None:
    now = time.time()
    conn.execute(
        "INSERT OR REPLACE INTO jobs (id, mode, brand, topic, status, spend_usd, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, 'planned', 0, ?, ?)",
        (job_id, mode, brand, topic, now, now),
    )
    conn.commit()


def set_status(conn: sqlite3.Connection, job_id: str, status: str, payload: Any = None) -> None:
    conn.execute(
        "UPDATE jobs SET status = ?, updated_at = ?, payload = ? WHERE id = ?",
        (status, time.time(), json.dumps(payload, ensure_ascii=False) if payload else None, job_id),
    )
    conn.commit()


def record_asset(
    conn: sqlite3.Connection,
    asset_hash: str,
    job_id: str,
    tier: str,
    model: str,
    path: str,
    cost_usd: float,
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO assets (hash, job_id, tier, model, path, cost_usd, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (asset_hash, job_id, tier, model, path, cost_usd, time.time()),
    )
    conn.execute(
        "UPDATE jobs SET spend_usd = spend_usd + ?, updated_at = ? WHERE id = ?",
        (cost_usd, time.time(), job_id),
    )
    conn.commit()


def job_spend(conn: sqlite3.Connection, job_id: str) -> float:
    row = conn.execute("SELECT spend_usd FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return float(row["spend_usd"]) if row else 0.0
