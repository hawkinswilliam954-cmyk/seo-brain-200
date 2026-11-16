# Initial API Contracts

The FastAPI starter currently exposes:
- `GET /health`
- `GET /api/agents`
- `GET /api/departments`
- `POST /api/tasks`
- `GET /api/tasks`
- `POST /api/approvals/{approval_id}/decision`

These are demo endpoints. Production endpoints must add authentication, authorization, validation, pagination, idempotency, rate limits, and persistent storage.

## Proposed production API groups

### Identity and organizations
- `POST /v1/organizations`
- `GET /v1/organizations/{organization_id}`
- `POST /v1/organizations/{organization_id}/members`
- `GET /v1/me`

### Tenants and websites
- `POST /v1/tenants`
- `GET /v1/tenants`
- `POST /v1/tenants/{tenant_id}/websites`
- `GET /v1/websites/{website_id}`

### Integrations
- `POST /v1/websites/{website_id}/integrations/{provider}/authorize`
- `GET /v1/websites/{website_id}/integrations`
- `POST /v1/integrations/{integration_id}/sync`
- `DELETE /v1/integrations/{integration_id}`

### Agents and workflows
- `GET /v1/agents`
- `GET /v1/agents/{agent_id}`
- `POST /v1/workflows`
- `POST /v1/workflows/{workflow_id}/run`
- `GET /v1/tasks`
- `GET /v1/tasks/{task_id}`

### Approvals and execution
- `GET /v1/approvals`
- `POST /v1/approvals/{approval_id}/approve`
- `POST /v1/approvals/{approval_id}/reject`
- `GET /v1/deployments/{deployment_id}`
- `POST /v1/deployments/{deployment_id}/rollback`

### Analytics and billing
- `GET /v1/websites/{website_id}/performance`
- `GET /v1/tenants/{tenant_id}/reports`
- `GET /v1/billing/subscription`
- `GET /v1/billing/usage`

## Example task request

```json
{
  "website_id": "site_123",
  "goal": "Find technical SEO problems and prioritize fixes",
  "scope": {
    "include_crawl": true,
    "include_search_console": true
  },
  "execution_mode": "recommend_only"
}
```

## Example task response

```json
{
  "task_id": "uuid",
  "status": "queued",
  "tenant_id": "server-derived-tenant",
  "created_at": "ISO-8601 timestamp"
}
```

## API design requirements
- Use OpenAPI and versioned endpoints.
- Use server-derived tenant context.
- Use idempotency keys for create/execute endpoints.
- Return stable error codes.
- Paginate list endpoints.
- Include request/trace IDs.
- Avoid returning secrets.
- Validate webhook signatures.
