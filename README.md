# SEO BRAIN 200 — Development Starter Package

## v0.2 — working MVP (built 2026-11-15)

What now actually runs:
- **Real crawler**: robots.txt-aware, same-domain, rate-limited, up to 100 pages per audit.
- **16 operational agents** from the registry (status flips to `operational` in `/api/agents`): Master AI orchestrator, Crawl analyzer, Technical SEO auditor, Indexation monitor, Broken-link detector, Title and meta writer, Content optimizer, Schema generator, Mobile SEO auditor, Canonical manager, Image optimization, Core Web Vitals analyst (server-side signals), Duplicate content detector, QA validator, Policy compliance agent, SEO strategist.
- **Health score + grade** and a prioritised fix list for every audit, every finding backed by evidence.
- **Persistent storage** (SQLite; Postgres schema still in `database/`).
- **Multi-tenant API keys** with server-side tenant isolation (tested), admin-only tenant creation.
- **Approval queue**: every proposed live-site change waits for a human; decisions go to the audit log.
- **Background workers**, per-tenant task limits, and a live Command Center dashboard.
- **Tests**: `python -m pytest -q` (auth, full audit flow, approvals, tenant isolation, URL validation).

Run on Replit: import the folder and press Run (`.replit` included). Locally: see Quick start.

Key endpoints: `POST /v1/audit {"url": "example.com", "max_pages": 25}` · `GET /v1/tasks` · `GET /v1/tasks/{id}/report` · `GET /v1/approvals` · `POST /v1/approvals/{id}/approve` · `POST /v1/tenants` (header `X-Admin-Token`). All `/v1` calls need header `X-API-Key`.

Not built yet: Google Search Console/Analytics OAuth, LLM-written content, WordPress write connector, billing, white-label domains. Approving an action records it but changes nothing until a connector exists.

---

**Purpose:** A proprietary, multi-tenant autonomous SEO SaaS platform for businesses and agencies, with direct subscriptions and white-label resale.

This package is a real starter repository: a runnable FastAPI backend, a lightweight web dashboard, an initial PostgreSQL schema, a 200-role agent registry, and implementation documentation.

> This is not a finished production platform. It does not contain 200 independently trained AI models, live integrations, production billing, or a deployed cloud service. It provides the architecture and starter code from which those capabilities can be implemented and tested.

## Product decisions

- Business model: direct SaaS + white-label agency platform.
- Customers: businesses + SEO/marketing agencies.
- Autonomy: automatic routine work; approval gates for high-risk actions.
- Build strategy: proprietary platform built from the ground up.
- Hosting: cloud-hosted SaaS is the recommended first deployment.
- Launch strategy: MVP, controlled customer pilot, then expand.

## Quick start (local development)

Requirements: Python 3.11+.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\\Scripts\\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:
- Dashboard: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- Agent registry: http://127.0.0.1:8000/api/agents

In development mode a demo tenant is created automatically and the dashboard picks up its key. Set APP_ENV=production and a strong ADMIN_TOKEN before going public.

## Repository map

```text
seo_brain_200/
├── app/
│   ├── main.py                 # FastAPI starter API + dashboard
│   └── static/
│       └── index.html          # Lightweight dashboard
├── agents/
│   └── registry.json           # 200 defined agent roles
├── database/
│   └── schema.sql              # PostgreSQL foundation schema
├── docs/
│   ├── MASTER_BLUEPRINT.md     # Product, architecture, agent & operating blueprint
│   ├── IMPLEMENTATION_PLAN.md  # Build sequence and acceptance criteria
│   ├── SCALABILITY.md          # Scale and reliability plan
│   ├── SECURITY.md             # Security and autonomy guardrails
│   └── API_CONTRACTS.md        # Initial API contracts
├── scripts/
│   └── validate_registry.py    # Checks that registry contains 200 roles
├── .env.example
├── requirements.txt
└── README.md
```

## First development steps

1. Install Python 3.11+.
2. Run the quick-start commands.
3. Inspect `/api/agents` and confirm the 200 role definitions load.
4. Read `docs/MASTER_BLUEPRINT.md`.
5. Create a Git repository and commit this starter.
6. Add PostgreSQL and migrations before storing persistent customer data.
7. Implement authentication and tenant isolation before exposing the app publicly.
8. Connect Google Search Console and Analytics using official OAuth flows.
9. Add a crawler, then technical diagnosis and content workflows.
10. Add controlled execution, approvals, staging, verification, and rollback.
11. Pilot with test websites and explicit customer permission.
12. Add billing and white-label capabilities after core value is proven.

## Important limitations

- The demo dashboard numbers are illustrative, not live SEO results.
- Audits are real, but nothing is written to a customer site; there is no LLM call yet.
- The agent registry defines roles and contracts; it does not imply that all 200 agents are running.
- Never put API keys in source code. Use a secrets manager in production.
- Do not deploy the demo with debug settings or public access to unauthenticated endpoints.
