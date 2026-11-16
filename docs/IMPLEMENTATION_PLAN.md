# Implementation Plan and Build Instructions

## Phase 0 — Product and engineering setup (Week 1)
Deliverables:
- Confirm product name, domain, target segments, and initial pricing hypotheses.
- Create Git repository and branch protections.
- Define development, staging, and production environments.
- Establish threat model and data classification.
- Define MVP acceptance tests.

Exit criteria:
- Reproducible local setup.
- CI runs linting, tests, dependency scanning, and build.
- Secrets are excluded from repository.

## Phase 1 — SaaS foundation (Weeks 1–3)
Build:
- Authentication and account recovery.
- Organizations, memberships, roles, tenants, websites.
- Tenant-scoped API authorization.
- PostgreSQL migrations.
- Audit event service.
- Initial dashboard and onboarding.

Exit criteria:
- Automated tests prove one tenant cannot read another tenant's records.
- User roles and permissions are enforced server-side.
- Database backups and restore test exist.

## Phase 2 — Master brain and agent runtime (Weeks 3–5)
Build:
- Versioned agent registry.
- Task schema and state machine.
- Workflow graph and dependencies.
- Agent execution worker.
- Model-provider abstraction.
- Structured output validation.
- Retry, timeout, cancellation, idempotency.
- Per-tenant and per-task budgets.

Exit criteria:
- 20 initial agent roles can execute test tasks through a controlled mock tool.
- Invalid outputs fail safely.
- Duplicate job delivery does not create duplicate external actions.

## Phase 3 — SEO data foundation (Weeks 5–8)
Build:
- Robots/sitemap-aware crawler.
- URL canonicalization and crawl deduplication.
- Page metadata and technical signals.
- Search Console OAuth and ingestion.
- Analytics connection and ingestion.
- Keyword and page/query data model.
- Evidence-backed issue reports.

Exit criteria:
- Crawl limits, robots rules, rate limits, and domain ownership checks work.
- Data freshness and source timestamps are visible.
- Findings can be reproduced from stored evidence.

## Phase 4 — Content and recommendations (Weeks 8–10)
Build:
- Keyword clustering and intent labels.
- Content gap and brief generation.
- Existing-page optimization suggestions.
- Human-readable change diffs.
- Content quality, originality, and usefulness review.
- Content version history.

Exit criteria:
- Content suggestions include sources, target audience, intent, and quality checks.
- No automatic mass publishing.
- Customer can accept, edit, or reject recommendations.

## Phase 5 — Controlled execution (Weeks 10–12)
Build:
- Connector framework.
- WordPress sandbox/staging integration first.
- Approval queue.
- Exact-action approval binding.
- Backups and rollback references.
- Post-deployment verification.
- Audit logging.

Exit criteria:
- Unauthorized write requests are blocked.
- High/critical risk actions require approval.
- Failed verification triggers rollback or incident escalation.
- All changes are traceable.

## Phase 6 — CRM, agency and billing (Weeks 12–14)
Build:
- CRM contact and lead sync.
- Agency portfolio.
- White-label brand configuration.
- Custom domain support.
- Subscription provider integration.
- Usage meters and plan entitlements.
- Customer and agency reports.

Exit criteria:
- Agency users cannot access client tenants outside their grants.
- Usage is attributable to tenant and plan.
- Subscription state gates paid features reliably.

## Phase 7 — Pilot and production readiness (Weeks 15–16+)
Build:
- Load and soak tests.
- Security review and penetration test.
- Disaster recovery rehearsal.
- Agent evaluation suite.
- Customer onboarding and support process.
- Incident response playbooks.
- Billing and cancellation tests.
- Limited paid pilot.

Exit criteria:
- No unresolved critical security findings.
- Restore and rollback rehearsals pass.
- Customer data export and deletion workflows work.
- Support and incident ownership is assigned.

## First 20 roles to operationalize

Start with:
- Master AI orchestrator.
- SEO strategist.
- Keyword research.
- Search intent analyst.
- Competitor intelligence.
- Technical SEO auditor.
- Crawl analyzer.
- Indexation monitor.
- Broken-link detector.
- Schema generator.
- Core Web Vitals analyst.
- SEO content strategist.
- Article researcher.
- SEO editor.
- Content optimizer.
- Content brief generator.
- Search Console analyst.
- Analytics analyst.
- QA validator.
- Policy compliance agent.

The full 200-role registry is already included, but these first roles should be the initial execution cohort.

## Definition of done for a feature

A feature is not done merely because the UI exists. It needs:
- API contract.
- Database migration where required.
- Authentication and authorization.
- Tenant isolation tests.
- Error and retry handling.
- Observability.
- User-facing status.
- Documentation.
- Automated tests.
- Security review appropriate to risk.
