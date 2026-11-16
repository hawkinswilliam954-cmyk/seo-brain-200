"""SQLite persistence for the MVP. Swap for PostgreSQL (database/schema.sql) in production."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("SEO_BRAIN_DB", Path(__file__).resolve().parents[1] / "data" / "seo_brain.db"))
_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, api_key TEXT UNIQUE NOT NULL,
  plan TEXT NOT NULL DEFAULT 'pilot', brand_name TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS websites (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id),
  url TEXT NOT NULL, domain TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, website_id TEXT NOT NULL,
  goal TEXT NOT NULL, workflow TEXT NOT NULL, status TEXT NOT NULL,
  max_pages INTEGER NOT NULL, progress TEXT, error TEXT,
  created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT);
CREATE TABLE IF NOT EXISTS pages (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
  url TEXT NOT NULL, status_code INTEGER, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS findings (
  id TEXT PRIMARY KEY, task_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
  agent_id TEXT NOT NULL, agent_name TEXT NOT NULL, severity TEXT NOT NULL,
  issue TEXT NOT NULL, url TEXT, evidence TEXT, recommendation TEXT);
CREATE TABLE IF NOT EXISTS reports (
  task_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, score INTEGER, summary TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, task_id TEXT NOT NULL,
  action TEXT NOT NULL, risk TEXT NOT NULL, payload TEXT, status TEXT NOT NULL,
  decided_by TEXT, note TEXT, created_at TEXT NOT NULL, decided_at TEXT);
CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY, tenant_id TEXT, actor TEXT, event TEXT NOT NULL,
  detail TEXT, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_findings_task ON findings(task_id);
CREATE INDEX IF NOT EXISTS ix_pages_task ON pages(task_id);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:16]}"


_conn: sqlite3.Connection | None = None


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.executescript(SCHEMA)
    return _conn


def reset(path: Path) -> None:
    """Point the module at a fresh database (used by tests)."""
    global _conn, DB_PATH
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None
        DB_PATH = path


def execute(sql: str, params: tuple = ()) -> None:
    with _lock:
        c = conn()
        c.execute(sql, params)
        c.commit()


def executemany(sql: str, rows: list[tuple]) -> None:
    with _lock:
        c = conn()
        c.executemany(sql, rows)
        c.commit()


def query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with _lock:
        return [dict(r) for r in conn().execute(sql, params).fetchall()]


def one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def audit(tenant_id: str | None, actor: str, event: str, detail: dict | None = None) -> None:
    execute(
        "INSERT INTO audit_events VALUES (?,?,?,?,?,?)",
        (new_id("evt_"), tenant_id, actor, event, json.dumps(detail or {}), now()),
    )
