# SEO BRAIN 200 — Master Platform Blueprint

## 1. Vision

SEO BRAIN 200 is a proprietary autonomous SEO operating system: a coordinated AI workforce that researches, diagnoses, plans, executes permitted changes, measures outcomes, and continuously reprioritizes work for businesses and agencies.

The commercial model has two channels:
1. Direct SaaS subscriptions for businesses.
2. White-label SaaS licensing for agencies that manage and resell services to their own clients.

The platform supports multiple tenants, brands, websites, users, integrations, workflows, and subscriptions.

## 2. Product capabilities

- Website onboarding and technical crawling.
- Search performance ingestion.
- Keyword and intent research.
- Competitor and content-gap analysis.
- Content briefs, optimization, versioning, and publishing.
- Technical SEO diagnosis and controlled fixes.
- Ethical authority research and outreach assistance.
- Local SEO monitoring.
- CRM and lead lifecycle integration.
- AI-search visibility research.
- Deployment, QA, and rollback.
- Daily/weekly/monthly reporting.
- Usage metering, subscriptions, and white-label branding.

The platform must not promise ranking outcomes. It should report measurable work and outcomes, distinguish correlation from causation, and comply with search-engine policies.

## 3. 10 departments / 200 agent roles

Each department contains 20 registered roles. The complete names are in `../agents/registry.json`.

1. SEO Intelligence & Strategy.
2. Technical SEO & Engineering.
3. Content Intelligence & Creation.
4. Authority & Link Development.
5. Local & Multi-Channel Visibility.
6. CRM & Revenue Operations.
7. AI Search & Emerging Visibility.
8. Analytics & Continuous Optimization.
9. Deployment & Automation.
10. Business Intelligence & Governance.

A role is a specification, not a separately trained model or permanently running process. Agent runtime workers can execute many roles. The orchestrator chooses the role, model, tools, budget, context, and permissions for each task.

## 4. Master brain

The master brain is composed of five services:

- Planner: converts customer objectives into measurable work plans.
- Dispatcher: assigns tasks to appropriate agent roles and execution queues.
- Memory service: retrieves tenant-scoped history, site facts, and approved preferences.
- Supervisor: checks evidence, output schemas, permissions, budgets, and policy.
- Evaluator: verifies work and uses measured results to reprioritize future work.

The master brain must not directly bypass execution services. All external writes go through the policy engine and connector layer.

## 5. Standard agent contract

Every agent definition includes:
- Stable agent ID and version.
- Department and role.
- Objective and supported task types.
- Required input schema.
- Output schema.
- Tools and connector scopes.
- Tenant-scoped memory policy.
- Dependencies.
- Risk classification.
- Quality evaluation criteria.
- Timeout, retry, and budget limits.
- Escalation conditions.

Expected output fields:
`agent_id`, `task_id`, `status`, `findings`, `recommended_actions`, `evidence`, `confidence`, `quality_check`, `next_steps`.

Agents must cite the evidence used for factual SEO findings. Confidence is a model estimate, not a guarantee.

## 6. Workflow lifecycle

1. Receive a customer goal or scheduled trigger.
2. Resolve tenant, website, permissions, and relevant context.
3. Collect current data from authorized integrations.
4. Diagnose and identify opportunities.
5. Score opportunities by impact, confidence, effort, risk, and cost.
6. Generate a dependency-aware plan.
7. Assign tasks to specialist roles.
8. Run policy checks.
9. Execute permitted low-risk work.
10. Route approval-required changes to the customer.
11. Execute approved changes in staging or a controlled environment.
12. Run automated quality checks.
13. Deploy only after required checks pass.
14. Verify the live result.
15. Roll back or escalate if verification fails.
16. Record immutable audit events.
17. Measure outcomes and update priorities.

## 7. Risk tiers

- Low: read-only research, reporting, audits. May run automatically.
- Medium: bounded metadata and internal-link changes. May run automatically only within explicit customer-configured rules and tested safeguards.
- High: publishing, redirects, bulk content updates, production code changes. Approval required by default.
- Critical: destructive page removals, permission changes, account/security changes, major production operations. Explicit approval and additional controls required.

An approval must be bound to an exact proposed action and version. If the proposal changes, approval becomes invalid.

## 8. Core user journeys

### Direct business customer
Sign up → create organization → add website → connect integrations → baseline audit → review strategy → configure autonomy policy → run tasks → monitor performance → manage subscription.

### Agency / white-label customer
Create agency organization → configure brand → set custom domain → create client tenant → add client website → connect client-authorized integrations → configure client permissions → monitor portfolio → issue branded reports → manage wholesale plan and usage.

### Operator / platform administrator
Review service health → monitor queue and cost → inspect failures → review abuse/security alerts → manage agent versions → deploy releases → audit tenant isolation.

## 9. Initial product modules

- Identity and organizations.
- Tenant and website management.
- Integration connections.
- Agent registry.
- Task and workflow engine.
- Crawl and SEO data ingestion.
- Strategy and recommendation engine.
- Approval and execution engine.
- Reporting.
- CRM sync.
- Billing and usage metering.
- White-label settings.
- Audit and security controls.

## 10. Recommended initial architecture

- Frontend: Next.js + TypeScript.
- API: FastAPI.
- Relational database: PostgreSQL.
- Semantic retrieval: pgvector.
- Agent graph/state: LangGraph or equivalent.
- Durable workflow orchestration: Temporal or equivalent.
- Queue/cache: Redis.
- Object storage: S3-compatible.
- Analytics/event store: begin with PostgreSQL; add ClickHouse when volume warrants it.
- Containers: Docker.
- Observability: OpenTelemetry with metrics, traces, and structured logs.

Start as a modular monolith plus isolated worker processes. Split into independently deployed services only when scaling, reliability, or team boundaries justify it.

## 11. Integrations

Priority order:
1. Google Search Console.
2. Google Analytics 4.
3. Website crawler and sitemap ingestion.
4. WordPress.
5. Shopify and Webflow.
6. CRM such as HubSpot and Salesforce.
7. Google Business Profile where eligible and authorized.
8. Email and outreach providers.
9. Rank and backlink data providers under licensed API terms.
10. Git/deployment systems for customers who explicitly authorize code workflows.

Use official APIs and documented OAuth scopes. Respect provider terms, quotas, and user revocation.

## 12. Product success measures

SEO outcome measures:
- Organic clicks and impressions.
- Query/page visibility.
- Index coverage and crawl health.
- Conversions and qualified leads.
- Organic-attributed revenue where measurement supports it.

Platform measures:
- Verified task success rate.
- Time to verified completion.
- Cost per successful task.
- Agent evaluation pass rate.
- Approval wait time.
- Deployment failure and rollback rates.
- Integration health.
- Tenant isolation test pass rate.
- Gross margin, retention, and expansion revenue.

Do not optimize for raw agent count, generated word count, or backlink count. Optimize for verified customer value and safe execution.
