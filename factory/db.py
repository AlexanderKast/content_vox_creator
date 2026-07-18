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
    id             TEXT PRIMARY KEY,
    mode           TEXT NOT NULL,
    brand          TEXT NOT NULL,
    topic          TEXT NOT NULL,
    status         TEXT NOT NULL,
    spend_usd      REAL NOT NULL DEFAULT 0,
    created_at     REAL NOT NULL,
    updated_at     REAL NOT NULL,
    payload        TEXT,
    formula        TEXT,
    published_url  TEXT,
    published_at   REAL
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

-- One row per Metricool pull for a published piece. job_id is nullable: F3
-- (opinion cruda) pieces are filmed by Alexander, never built by this
-- factory, but still need to feed the 70/30 mix and formula-correlation
-- checks — those need every published piece, not only factory output.
CREATE TABLE IF NOT EXISTS performance (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id                 TEXT,
    formula                TEXT,
    published_url          TEXT NOT NULL,
    published_at           REAL NOT NULL,
    fetched_at             REAL NOT NULL,
    reach                  REAL,
    retention              REAL,
    comments               REAL,
    saved                  REAL,
    shares                 REAL,
    likes                  REAL,
    raw_json               TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs (id)
);
"""

# Columns added after the first release of `jobs` — SQLite has no
# `ADD COLUMN IF NOT EXISTS` on every version this might run against, so
# migrate defensively instead of relying on schema-string idempotency alone.
_JOBS_MIGRATIONS = (
    "ALTER TABLE jobs ADD COLUMN formula TEXT",
    "ALTER TABLE jobs ADD COLUMN published_url TEXT",
    "ALTER TABLE jobs ADD COLUMN published_at REAL",
)


def _migrate(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(jobs)")}
    for statement in _JOBS_MIGRATIONS:
        column = statement.split("ADD COLUMN")[1].split()[0]
        if column not in existing:
            conn.execute(statement)
    conn.commit()


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def create_job(
    conn: sqlite3.Connection, job_id: str, mode: str, brand: str, topic: str,
    formula: str | None = None,
) -> None:
    """Create a job, or reset an existing one for a retry — WITHOUT wiping
    its accumulated spend_usd. Re-running the same job_id after a mid-build
    failure (a very real scenario: a bad key, a transient 400) is normal,
    and the assets already paid for stay cached; the spend counter has to
    keep matching that ledger. The old `INSERT OR REPLACE` reset spend_usd
    to 0 on every retry, silently under-reporting real spend from that point
    on — real bug, found the hard way on the first live build."""
    now = time.time()
    conn.execute(
        """
        INSERT INTO jobs (id, mode, brand, topic, status, spend_usd, created_at, updated_at, formula)
        VALUES (?, ?, ?, ?, 'planned', 0, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            mode = excluded.mode,
            brand = excluded.brand,
            topic = excluded.topic,
            formula = excluded.formula,
            status = 'planned',
            updated_at = excluded.updated_at
        """,
        (job_id, mode, brand, topic, now, now, formula),
    )
    conn.commit()


def mark_published(conn: sqlite3.Connection, job_id: str, published_url: str, published_at: float) -> None:
    conn.execute(
        "UPDATE jobs SET published_url = ?, published_at = ?, updated_at = ? WHERE id = ?",
        (published_url, published_at, time.time(), job_id),
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
