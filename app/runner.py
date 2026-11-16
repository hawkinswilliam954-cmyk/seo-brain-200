"""Master orchestrator (GOV_001): runs a task through crawl -> specialist agents ->
QA validator (TECH_020) -> policy compliance (GOV_008) -> strategist (STR_001)."""
from __future__ import annotations

import json
import queue
import threading
import traceback
from collections import Counter

from . import db
from .agents import SEV_WEIGHT, as_dict, run_all, score
from .crawler import crawl

AGENT_NAMES: dict[str, str] = {}
_jobs: "queue.Queue[str]" = queue.Queue()
_started = False

# Actions that would change a live site always need a human (SECURITY.md approval gates).
WRITE_ACTIONS = {
    "CONT_006": ("Rewrite titles and meta descriptions on the live site", "high"),
    "TECH_003": ("Change indexing (noindex / robots.txt) on the live site", "critical"),
    "TECH_006": ("Inject structured data into site templates", "high"),
    "TECH_004": ("Create 301 redirects for broken URLs", "high"),
}


def set_progress(task_id: str, msg: str) -> None:
    db.execute("UPDATE tasks SET progress=? WHERE id=?", (msg, task_id))


def qa_validate(findings: list[dict]) -> list[dict]:
    """TECH_020: drop duplicates and anything without evidence."""
    seen, out = set(), []
    for f in findings:
        key = (f["agent_id"], f["issue"], f["url"])
        if key in seen or not f["evidence"]:
            continue
        seen.add(key)
        out.append(f)
    return out


def strategist(findings: list[dict], pages: int, site_score: int) -> dict:
    """STR_001: turn findings into a prioritised plan."""
    groups: dict[str, list[dict]] = {}
    for f in findings:
        groups.setdefault(f["issue"], []).append(f)
    ranked = sorted(groups.items(), key=lambda kv: (-max(SEV_WEIGHT[f["severity"]] for f in kv[1]), -len(kv[1])))
    top = []
    for issue, fs in ranked[:8]:
        worst = max(fs, key=lambda f: SEV_WEIGHT[f["severity"]])
        top.append({"issue": issue, "severity": worst["severity"], "pages_affected": len({f["url"] for f in fs}),
                    "recommendation": worst["recommendation"]})
    sev = Counter(f["severity"] for f in findings)
    grade = "A" if site_score >= 90 else "B" if site_score >= 75 else "C" if site_score >= 60 else "D" if site_score >= 40 else "F"
    return {"score": site_score, "grade": grade, "pages_crawled": pages, "total_findings": len(findings),
            "by_severity": dict(sev), "priorities": top}


def execute_task(task_id: str) -> None:
    t = db.one("SELECT * FROM tasks WHERE id=?", (task_id,))
    if not t or t["status"] != "queued":
        return
    site = db.one("SELECT * FROM websites WHERE id=? AND tenant_id=?", (t["website_id"], t["tenant_id"]))
    db.execute("UPDATE tasks SET status='running', started_at=? WHERE id=?", (db.now(), task_id))
    db.audit(t["tenant_id"], "GOV_001", "task.started", {"task_id": task_id})
    try:
        result = crawl(site["url"], max_pages=t["max_pages"], progress=lambda m: set_progress(task_id, m))
        if not result.pages or result.pages[0].status_code is None:
            raise RuntimeError(f"Couldn't reach {site['url']} ({result.pages[0].error if result.pages else 'blocked by robots.txt'})")
        db.executemany("INSERT INTO pages VALUES (?,?,?,?,?,?)", [
            (db.new_id("pg_"), task_id, t["tenant_id"], p.url, p.status_code,
             json.dumps({k: v for k, v in p.__dict__.items() if k != "internal_links"}))
            for p in result.pages])
        set_progress(task_id, "Specialist agents analysing pages")
        findings = qa_validate([as_dict(f) for f in run_all(result)])
        db.executemany("INSERT INTO findings VALUES (?,?,?,?,?,?,?,?,?,?)", [
            (db.new_id("fd_"), task_id, t["tenant_id"], f["agent_id"], AGENT_NAMES.get(f["agent_id"], f["agent_id"]),
             f["severity"], f["issue"], f["url"], f["evidence"], f["recommendation"]) for f in findings])
        html_count = sum(1 for p in result.pages if p.status_code and "html" in p.content_type.lower())
        site_score = score([f["severity"] for f in findings], html_count) if findings else (100 if html_count else 0)
        summary = strategist(findings, len(result.pages), site_score)
        db.execute("INSERT OR REPLACE INTO reports VALUES (?,?,?,?)",
                   (task_id, t["tenant_id"], site_score, json.dumps(summary)))
        # GOV_008 policy compliance: every proposed site change becomes a pending approval.
        agents_hit = {f["agent_id"] for f in findings}
        for aid, (action, risk) in WRITE_ACTIONS.items():
            if aid in agents_hit:
                n = sum(1 for f in findings if f["agent_id"] == aid)
                db.execute("INSERT INTO approvals VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                           (db.new_id("apr_"), t["tenant_id"], task_id, action, risk,
                            json.dumps({"agent_id": aid, "findings": n}), "pending", None, None, db.now(), None))
        db.execute("UPDATE tasks SET status='completed', finished_at=?, progress=? WHERE id=?",
                   (db.now(), f"Done: {len(result.pages)} pages, {len(findings)} findings", task_id))
        db.audit(t["tenant_id"], "GOV_001", "task.completed", {"task_id": task_id, "score": site_score})
    except Exception as e:  # fail safely, keep the error for the dashboard
        db.execute("UPDATE tasks SET status='failed', error=?, finished_at=? WHERE id=?",
                   (f"{type(e).__name__}: {e}", db.now(), task_id))
        db.audit(t["tenant_id"], "GOV_001", "task.failed", {"task_id": task_id, "trace": traceback.format_exc()[-800:]})


def _worker() -> None:
    while True:
        task_id = _jobs.get()
        try:
            execute_task(task_id)
        finally:
            _jobs.task_done()


def start_workers(n: int = 2) -> None:
    global _started
    if _started:
        return
    _started = True
    for _ in range(n):
        threading.Thread(target=_worker, daemon=True).start()
    for t in db.query("SELECT id FROM tasks WHERE status IN ('queued','running')"):
        db.execute("UPDATE tasks SET status='queued' WHERE id=?", (t["id"],))
        _jobs.put(t["id"])


def enqueue(task_id: str) -> None:
    _jobs.put(task_id)
