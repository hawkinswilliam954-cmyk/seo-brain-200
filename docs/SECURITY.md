# Security, Privacy and Autonomous Execution Guardrails

## Threat model
The platform handles customer website access, search analytics, business information, CRM data, generated content, and possibly deployment credentials. Treat all of these as sensitive business data.

## Identity and access
- Use a mature OIDC/OAuth identity provider.
- Enforce MFA for privileged users.
- Use RBAC plus tenant membership checks.
- Derive tenant access from authenticated server-side identity.
- Never trust a tenant ID supplied by the browser as proof of access.
- Require reauthentication for sensitive account changes.

## Tenant isolation
- PostgreSQL Row Level Security on tenant-owned tables.
- Tenant-scoped object storage paths and authorization.
- Tenant-scoped vector retrieval.
- Integration credentials scoped to a tenant and website.
- Automated cross-tenant access tests on every release.

## Secrets
- Store OAuth tokens and API secrets in a secrets manager.
- Encrypt sensitive fields and rotate credentials.
- Do not log tokens, passwords, or authorization headers.
- Do not put secrets into prompts, vector memory, task output, or source control.

## Untrusted content and prompt injection
Website text, HTML, documents, user-generated content, and third-party tool output are untrusted data, not instructions.
- Keep system policy separate from retrieved content.
- Sanitize and label external content.
- Use tool allowlists.
- Do not let page content change agent permissions.
- Require policy checks before every external write.

## Approval policy
- Low-risk read-only work may run automatically.
- Medium-risk bounded edits may run automatically only under explicit tenant rules and tested limits.
- High-risk publishing, redirects, bulk edits, and production code changes require approval by default.
- Critical destructive, security, or access changes require explicit approval and stronger verification.

Approval records must bind to the exact proposed action, target, diff, and version. A changed proposal requires a new approval.

## Deployment safety
- Back up before write operations.
- Prefer staging.
- Run tests and diff review.
- Deploy in small batches.
- Verify live state after deployment.
- Roll back or escalate on failed verification.
- Preserve audit evidence.

## SEO policy
Do not automate manipulative link schemes, spam outreach, fake reviews, hidden text, keyword stuffing, or scaled low-value content. Prefer useful original content, relevant editorial relationships, and technically sound websites.

## Privacy and retention
- Collect only data required for the feature.
- Document processing purposes and retention.
- Support customer export and deletion.
- Respect connector revocation.
- Restrict employee access and log privileged access.
- Review applicable privacy and data protection obligations with qualified counsel.

## Production release gate
No production launch before:
- Independent security review.
- Tenant isolation testing.
- Secrets management.
- Backup and restore rehearsal.
- Incident response plan.
- Rate limits and abuse controls.
- Logging redaction.
- Data deletion workflow.
