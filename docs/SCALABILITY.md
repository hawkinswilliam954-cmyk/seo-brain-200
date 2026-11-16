# Scalability, Reliability and Cost Plan

## 1. Scale by workload, not by agent count

The 200 entries are role definitions. They should not all run continuously. Use a shared worker pool that loads the correct role configuration for each job.

## 2. Recommended progression

### Stage A: Pilot (1–25 customers)
- Modular monolith API.
- One PostgreSQL cluster.
- Redis-backed job queue.
- Separate worker process.
- Object storage for reports and crawl artifacts.
- Basic tracing, logs, alerts, and daily backups.

### Stage B: Early growth (25–250 customers)
- Multiple worker pools by workload: crawl, content, integrations, reporting.
- Durable workflow engine.
- Read replicas if read load requires them.
- Partition high-volume event tables by time/tenant.
- Centralized metrics and tracing.
- Per-tenant rate and spend limits.

### Stage C: Scale (250–2,500 customers)
- Horizontally scaled stateless API containers.
- Autoscaled workers based on queue depth and service-level objectives.
- Separate analytics/event store when PostgreSQL is no longer efficient.
- Dedicated crawl scheduling and politeness controls.
- Tenant-aware caching.
- Regional object storage and disaster recovery.
- Formal on-call and incident response.

### Stage D: Enterprise scale
- Optional dedicated tenant data plane for contractual needs.
- Regional data residency where required.
- Private networking and customer-managed keys where feasible.
- Enterprise SSO and audit exports.
- Capacity reservations and service-level agreements.
- Tested multi-region recovery.

These are planning bands, not guarantees. Actual capacity must be load-tested against realistic crawl sizes, model calls, integrations, and customer concurrency.

## 3. Queue design

Use separate queues:
- `crawl`
- `seo_analysis`
- `content`
- `integration_sync`
- `write_execution`
- `reporting`
- `billing`
- `security_events`

Every job needs:
- Tenant ID.
- Website ID when applicable.
- Idempotency key.
- Priority.
- Deadline/expiry.
- Retry policy.
- Timeout.
- Cost budget.
- Trace ID.
- Permission context.

Prevent one noisy tenant from starving others with per-tenant concurrency caps and fair scheduling.

## 4. Cost controls

- Route simple classification and extraction to lower-cost models.
- Reserve stronger models for planning, difficult reasoning, and review.
- Cache stable research with expiry and source timestamps.
- Batch embeddings and data ingestion.
- Limit context size and tool calls.
- Track model tokens and provider cost per task.
- Set tenant budgets and alert thresholds.
- Stop runaway loops and duplicate agent delegation.
- Require expected-value scoring before expensive workflows.

Core metric:

Cost per verified successful task = total execution cost / number of verified successful tasks.

## 5. Reliability patterns

- Durable workflow state.
- Idempotent connector operations.
- Exponential backoff with jitter.
- Dead-letter queues.
- Circuit breakers for failing providers.
- Timeouts and cancellation.
- Versioned task and agent contracts.
- Staging and canary deployments.
- Automated health checks.
- Backup restore drills.
- Rollback and compensating actions.

## 6. Data scaling

Keep transactional records in PostgreSQL. Keep large raw crawl artifacts and exports in object storage. Add a columnar analytics database only when query volume and retention justify it. Apply retention rules and data minimization.

## 7. Service-level objectives to begin measuring

Initial internal targets to validate:
- API availability.
- Queue age by priority.
- Workflow completion time.
- Integration sync freshness.
- Agent output validation pass rate.
- Deployment success rate.
- Tenant isolation test pass rate.
- Recovery time and recovery point.

Do not publish an SLA until the system has production measurements and operational coverage.
