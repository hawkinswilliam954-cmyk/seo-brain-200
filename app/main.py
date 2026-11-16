from __future__ import annotations

import json
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from . import db, runner
from .agents import OPERATIONAL

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "agents" / "registry.json"
STATIC_PATH = Path(__file__).parent / "static"
APP_ENV = os.getenv("APP_ENV", "development")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "dev-admin-token" if APP_ENV == "development" else "")
MAX_ACTIVE_TASKS = int(os.getenv("MAX_ACTIVE_TASKS_PER_TENANT", "3"))
MAX_PAGES_CAP = int(os.getenv("MAX_PAGES_CAP", "100"))

with REGISTRY_PATH.open("r", encoding="utf-8") as f:
    AGENTS: list[dict[str, Any]] = json.load(f)
for a in AGENTS:
    if a["id"] in OPERATIONAL or a["id"] in {"GOV_001", "TECH_020", "GOV_008", "STR_001"}:
        a["implementation_status"] = "operational"
runner.AGENT_NAMES.update({a["id"]: a["name"] for a in AGENTS})


def ensure_demo_tenant() -> None:
    if APP_ENV != "development":
        return
    if not db.one("SELECT id FROM tenants WHERE id='demo-tenant'"):
        db.execute("INSERT INTO tenants VALUES (?,?,?,?,?,?)",
                   ("demo-tenant", "Demo Agency", "sb_demo_" + secrets.token_hex(12), "pilot", "SEO BRAIN 200", db.now()))


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.conn()
    ensure_demo_tenant()
    runner.start_workers(int(os.getenv("WORKERS", "2")))
    yield


app = FastAPI(title="SEO BRAIN 200", version="0.2.0", lifespan=lifespan,
              description="Multi-tenant autonomous SEO operating system: real crawler, operational audit agents, "
                          "approval-gated execution.")


# ---------- auth ----------
def tenant(x_api_key: str = Header(default="")) -> dict:
    t = db.one("SELECT * FROM tenants WHERE api_key=?", (x_api_key,)) if x_api_key else None
    if not t:
        raise HTTPException(401, "Missing or invalid X-API-Key")
    return t


def admin(x_admin_token: str = Header(default="")) -> None:
    if not ADMIN_TOKEN or not secrets.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(403, "Admin token required")


# ---------- models ----------
class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    plan: Literal["pilot", "starter", "growth", "agency"] = "pilot"
    brand_name: str | None = Field(default=None, max_length=120)


class WebsiteCreate(BaseModel):
    url: str = Field(min_length=4, max_length=500)

    @field_validator("url")
    @classmethod
    def clean(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        p = urlparse(v)
        if not p.netloc or "." not in p.netloc or p.netloc.split(":")[0] in {"localhost", "127.0.0.1", "0.0.0.0"}:
            raise ValueError("Enter a public website URL")
        return f"{p.scheme}://{p.netloc}{p.path or '/'}"


class TaskCreate(BaseModel):
    website_id: str
    goal: str = Field(default="Full technical and on-page SEO audit", min_length=5, max_length=2000)
    max_pages: int = Field(default=25, ge=1, le=500)


class QuickAudit(WebsiteCreate):
    max_pages: int = Field(default=25, ge=1, le=500)


class Decision(BaseModel):
    decided_by: str = Field(min_length=2, max_length=200)
    note: str = Field(default="", max_length=1000)


# ---------- public ----------
@app.get("/health")
def health():
    return {"status": "ok", "service": "seo-brain-200", "version": app.version, "environment": APP_ENV,
            "timestamp": db.now()}


@app.get("/api/agents")
def list_agents(department: str | None = None, status: str | None = None):
    r = [a for a in AGENTS if (not department or a["department"] == department)
         and (not status or a["implementation_status"] == status)]
    return {"count": len(r), "operational": sum(1 for a in r if a["implementation_status"] == "operational"),
            "agents": r}


@app.get("/api/departments")
def list_departments():
    g: dict[str, int] = {}
    for a in AGENTS:
        g[a["department"]] = g.get(a["department"], 0) + 1
    return {"department_count": len(g), "departments": g}


@app.get("/v1/dev/demo-key")
def demo_key():
    if APP_ENV != "development":
        raise HTTPException(404)
    return {"api_key": db.one("SELECT api_key FROM tenants WHERE id='demo-tenant'")["api_key"]}


# ---------- admin ----------
@app.post("/v1/tenants", status_code=201, dependencies=[Depends(admin)])
def create_tenant(body: TenantCreate):
    tid, key = db.new_id("ten_"), "sb_" + secrets.token_urlsafe(24)
    db.execute("INSERT INTO tenants VALUES (?,?,?,?,?,?)", (tid, body.name, key, body.plan, body.brand_name, db.now()))
    db.audit(tid, "admin", "tenant.created", {"name": body.name})
    return {"id": tid, "name": body.name, "plan": body.plan, "api_key": key,
            "notice": "Store this API key now; it is shown once."}


# ---------- tenant-scoped ----------
@app.get("/v1/me")
def me(t: dict = Depends(tenant)):
    return {k: t[k] for k in ("id", "name", "plan", "brand_name", "created_at")}


@app.post("/v1/websites", status_code=201)
def add_website(body: WebsiteCreate, t: dict = Depends(tenant)):
    domain = urlparse(body.url).netloc.lower()
    existing = db.one("SELECT * FROM websites WHERE tenant_id=? AND domain=?", (t["id"], domain))
    if existing:
        return existing
    w = {"id": db.new_id("web_"), "tenant_id": t["id"], "url": body.url, "domain": domain, "created_at": db.now()}
    db.execute("INSERT INTO websites VALUES (?,?,?,?,?)", tuple(w.values()))
    db.audit(t["id"], "user", "website.added", {"domain": domain})
    return w


@app.get("/v1/websites")
def list_websites(t: dict = Depends(tenant)):
    return {"websites": db.query("SELECT * FROM websites WHERE tenant_id=? ORDER BY created_at DESC", (t["id"],))}


def _create_task(t: dict, website_id: str, goal: str, max_pages: int) -> dict:
    if not db.one("SELECT id FROM websites WHERE id=? AND tenant_id=?", (website_id, t["id"])):
        raise HTTPException(404, "Website not found")
    active = db.one("SELECT COUNT(*) n FROM tasks WHERE tenant_id=? AND status IN ('queued','running')", (t["id"],))
    if active["n"] >= MAX_ACTIVE_TASKS:
        raise HTTPException(429, f"At most {MAX_ACTIVE_TASKS} active tasks per tenant")
    task = {"id": db.new_id("task_"), "tenant_id": t["id"], "website_id": website_id, "goal": goal,
            "workflow": "full_site_audit", "status": "queued", "max_pages": min(max_pages, MAX_PAGES_CAP),
            "progress": "Queued", "error": None, "created_at": db.now(), "started_at": None, "finished_at": None}
    db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", tuple(task.values()))
    db.audit(t["id"], "user", "task.created", {"task_id": task["id"]})
    runner.enqueue(task["id"])
    return task


@app.post("/v1/tasks", status_code=201)
def create_task(body: TaskCreate, t: dict = Depends(tenant)):
    return _create_task(t, body.website_id, body.goal, body.max_pages)


@app.post("/v1/audit", status_code=201)
def quick_audit(body: QuickAudit, t: dict = Depends(tenant)):
    """One call: add the site (if new) and start a full audit."""
    w = add_website(WebsiteCreate(url=body.url), t)
    return _create_task(t, w["id"], "Full technical and on-page SEO audit", body.max_pages)


@app.get("/v1/tasks")
def list_tasks(t: dict = Depends(tenant)):
    rows = db.query("""SELECT tasks.*, websites.domain, reports.score FROM tasks
                       JOIN websites ON websites.id=tasks.website_id
                       LEFT JOIN reports ON reports.task_id=tasks.id
                       WHERE tasks.tenant_id=? ORDER BY tasks.created_at DESC LIMIT 100""", (t["id"],))
    return {"count": len(rows), "tasks": rows}


@app.get("/v1/tasks/{task_id}")
def get_task(task_id: str, t: dict = Depends(tenant)):
    row = db.one("SELECT * FROM tasks WHERE id=? AND tenant_id=?", (task_id, t["id"]))
    if not row:
        raise HTTPException(404, "Task not found")
    return row


@app.get("/v1/tasks/{task_id}/report")
def get_report(task_id: str, t: dict = Depends(tenant)):
    task = get_task(task_id, t)
    rep = db.one("SELECT * FROM reports WHERE task_id=? AND tenant_id=?", (task_id, t["id"]))
    if not rep:
        return {"task": task, "report": None}
    findings = db.query("""SELECT agent_id, agent_name, severity, issue, url, evidence, recommendation FROM findings
                           WHERE task_id=? AND tenant_id=? ORDER BY CASE severity WHEN 'critical' THEN 0
                           WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END""", (task_id, t["id"]))
    return {"task": task, "report": json.loads(rep["summary"]), "findings": findings}


@app.get("/v1/approvals")
def list_approvals(status: str | None = "pending", t: dict = Depends(tenant)):
    sql, params = "SELECT * FROM approvals WHERE tenant_id=?", [t["id"]]
    if status:
        sql += " AND status=?"
        params.append(status)
    return {"approvals": db.query(sql + " ORDER BY created_at DESC", tuple(params))}


def _decide(approval_id: str, decision: str, body: Decision, t: dict) -> dict:
    a = db.one("SELECT * FROM approvals WHERE id=? AND tenant_id=?", (approval_id, t["id"]))
    if not a:
        raise HTTPException(404, "Approval not found")
    if a["status"] != "pending":
        raise HTTPException(409, "Approval is no longer pending")
    db.execute("UPDATE approvals SET status=?, decided_by=?, note=?, decided_at=? WHERE id=?",
               (decision, body.decided_by, body.note, db.now(), approval_id))
    db.audit(t["id"], body.decided_by, f"approval.{decision}", {"approval_id": approval_id, "action": a["action"]})
    out = db.one("SELECT * FROM approvals WHERE id=?", (approval_id,))
    out["execution"] = ("Recorded. No site connector is configured yet, so nothing was changed on the live site."
                        if decision == "approved" else "Rejected. No change will be made.")
    return out


@app.post("/v1/approvals/{approval_id}/approve")
def approve(approval_id: str, body: Decision, t: dict = Depends(tenant)):
    return _decide(approval_id, "approved", body, t)


@app.post("/v1/approvals/{approval_id}/reject")
def reject(approval_id: str, body: Decision, t: dict = Depends(tenant)):
    return _decide(approval_id, "rejected", body, t)


@app.get("/v1/audit-log")
def audit_log(t: dict = Depends(tenant)):
    return {"events": db.query("SELECT actor, event, detail, created_at FROM audit_events WHERE tenant_id=? "
                               "ORDER BY created_at DESC LIMIT 100", (t["id"],))}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse((STATIC_PATH / "index.html").read_text(encoding="utf-8"))
