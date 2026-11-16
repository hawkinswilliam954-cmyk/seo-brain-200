import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app import crawler, db

SITE = {
    "https://shop.test/robots.txt": (200, "text/plain", "User-agent: *\nDisallow: /private\n"),
    "https://shop.test/": (200, "text/html", """<html><head><title>Shop</title></head><body>
        <h1>Welcome</h1><a href="/about">About</a><a href="/missing">Gone</a><a href="/private/x">P</a>
        <img src="a.png"></body></html>"""),
    "https://shop.test/about": (200, "text/html", """<html lang="en"><head><title>About our handmade shop in Utica NY</title>
        <meta name="description" content="We make things."><meta name="viewport" content="width=device-width">
        <link rel="canonical" href="https://shop.test/about"></head><body><h1>About</h1>""" + "word " * 300 + "</body></html>"),
}


def handler(request: httpx.Request) -> httpx.Response:
    hit = SITE.get(str(request.url))
    if not hit:
        return httpx.Response(404, headers={"content-type": "text/html"}, text="nope")
    code, ctype, body = hit
    return httpx.Response(code, headers={"content-type": ctype}, text=body)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db.reset(tmp_path / "t.db")
    real = crawler.crawl

    def fake_crawl(url, **kw):
        kw.pop("client", None)
        c = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
        return real(url, client=c, delay=0, **kw)

    monkeypatch.setattr("app.runner.crawl", fake_crawl)
    from app.main import app
    with TestClient(app) as c:
        yield c


def key(c):
    return c.get("/v1/dev/demo-key").json()["api_key"]


def wait(c, h, tid):
    for _ in range(100):
        t = c.get(f"/v1/tasks/{tid}", headers=h).json()
        if t["status"] in ("completed", "failed"):
            return t
        time.sleep(0.05)
    raise AssertionError("task did not finish")


def test_registry_and_health(client):
    assert client.get("/health").json()["status"] == "ok"
    a = client.get("/api/agents").json()
    assert a["count"] == 200 and a["operational"] >= 15


def test_auth_required(client):
    assert client.get("/v1/tasks").status_code == 401
    assert client.get("/v1/tasks", headers={"X-API-Key": "bad"}).status_code == 401


def test_full_audit_flow(client):
    h = {"X-API-Key": key(client)}
    task = client.post("/v1/audit", json={"url": "shop.test", "max_pages": 10}, headers=h).json()
    t = wait(client, h, task["id"])
    assert t["status"] == "completed", t
    r = client.get(f"/v1/tasks/{task['id']}/report", headers=h).json()
    issues = {f["issue"] for f in r["findings"]}
    assert "Broken internal link" in issues
    assert "Missing meta description" in issues
    assert "Blocked by robots.txt" in issues
    assert 0 <= r["report"]["score"] <= 100
    aps = client.get("/v1/approvals", headers=h).json()["approvals"]
    assert aps, "write actions must be approval-gated"
    d = client.post(f"/v1/approvals/{aps[0]['id']}/approve", json={"decided_by": "William"}, headers=h)
    assert d.status_code == 200 and "nothing was changed" in d.json()["execution"]
    assert client.post(f"/v1/approvals/{aps[0]['id']}/approve", json={"decided_by": "William"}, headers=h).status_code == 409


def test_tenant_isolation(client):
    h1 = {"X-API-Key": key(client)}
    task = client.post("/v1/audit", json={"url": "shop.test", "max_pages": 3}, headers=h1).json()
    wait(client, h1, task["id"])
    other = client.post("/v1/tenants", json={"name": "Other Agency"}, headers={"X-Admin-Token": "dev-admin-token"}).json()
    h2 = {"X-API-Key": other["api_key"]}
    assert client.get(f"/v1/tasks/{task['id']}", headers=h2).status_code == 404
    assert client.get(f"/v1/tasks/{task['id']}/report", headers=h2).status_code == 404
    assert client.get("/v1/tasks", headers=h2).json()["count"] == 0
    assert client.get("/v1/approvals", headers=h2).json()["approvals"] == []
    w = client.get("/v1/websites", headers=h1).json()["websites"][0]
    assert client.post("/v1/tasks", json={"website_id": w["id"]}, headers=h2).status_code == 404


def test_admin_required_and_url_validation(client):
    assert client.post("/v1/tenants", json={"name": "X"}).status_code == 403
    h = {"X-API-Key": key(client)}
    assert client.post("/v1/audit", json={"url": "localhost"}, headers=h).status_code == 422
