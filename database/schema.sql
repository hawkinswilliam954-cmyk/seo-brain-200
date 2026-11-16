-- PostgreSQL foundation schema. Review and harden before production.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  organization_type TEXT NOT NULL CHECK (organization_type IN ('agency','business')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  display_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
  organization_id UUID NOT NULL REFERENCES organizations(id),
  user_id UUID NOT NULL REFERENCES users(id),
  role TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tenant_settings (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(id),
  settings JSONB NOT NULL DEFAULT '{}',
  autonomy_policy JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE white_label_configs (
  tenant_id UUID PRIMARY KEY REFERENCES tenants(id),
  brand_name TEXT,
  logo_object_key TEXT,
  primary_color TEXT,
  custom_domain TEXT UNIQUE,
  report_branding JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE websites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  domain TEXT NOT NULL,
  platform TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, domain)
);

CREATE TABLE integrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID REFERENCES websites(id),
  provider TEXT NOT NULL,
  connection_status TEXT NOT NULL DEFAULT 'pending',
  secret_reference TEXT NOT NULL,
  scopes JSONB NOT NULL DEFAULT '[]',
  last_sync_at TIMESTAMPTZ
);

CREATE TABLE agents (
  id TEXT PRIMARY KEY,
  department TEXT NOT NULL,
  name TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  enabled BOOLEAN NOT NULL DEFAULT true,
  configuration JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID REFERENCES websites(id),
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  definition JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID REFERENCES websites(id),
  workflow_id UUID REFERENCES workflows(id),
  agent_id TEXT REFERENCES agents(id),
  task_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  priority SMALLINT NOT NULL DEFAULT 5,
  input JSONB NOT NULL DEFAULT '{}',
  output JSONB NOT NULL DEFAULT '{}',
  error JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

CREATE TABLE task_dependencies (
  task_id UUID NOT NULL REFERENCES tasks(id),
  depends_on_task_id UUID NOT NULL REFERENCES tasks(id),
  PRIMARY KEY (task_id, depends_on_task_id),
  CHECK (task_id <> depends_on_task_id)
);

CREATE TABLE approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  task_id UUID NOT NULL REFERENCES tasks(id),
  action JSONB NOT NULL,
  risk_level TEXT NOT NULL CHECK (risk_level IN ('low','medium','high','critical')),
  status TEXT NOT NULL DEFAULT 'pending',
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_by UUID REFERENCES users(id),
  decided_at TIMESTAMPTZ,
  decision_note TEXT
);

CREATE TABLE execution_changes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID NOT NULL REFERENCES websites(id),
  task_id UUID REFERENCES tasks(id),
  change_type TEXT NOT NULL,
  before_state JSONB,
  proposed_state JSONB NOT NULL,
  after_state JSONB,
  status TEXT NOT NULL DEFAULT 'proposed',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE deployments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID NOT NULL REFERENCES websites(id),
  task_id UUID REFERENCES tasks(id),
  environment TEXT NOT NULL,
  status TEXT NOT NULL,
  version TEXT,
  rollback_reference TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  agent_id TEXT REFERENCES agents(id),
  memory_type TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE seo_pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID NOT NULL REFERENCES websites(id),
  url TEXT NOT NULL,
  canonical_url TEXT,
  title TEXT,
  status_code INTEGER,
  last_crawled_at TIMESTAMPTZ,
  UNIQUE (website_id, url)
);

CREATE TABLE keywords (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID NOT NULL REFERENCES websites(id),
  query TEXT NOT NULL,
  intent TEXT,
  country_code TEXT,
  language_code TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ranking_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID NOT NULL REFERENCES websites(id),
  keyword_id UUID NOT NULL REFERENCES keywords(id),
  measured_at TIMESTAMPTZ NOT NULL,
  position NUMERIC,
  impressions BIGINT,
  clicks BIGINT
);

CREATE TABLE content_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID NOT NULL REFERENCES websites(id),
  url TEXT,
  title TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  content_body TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crm_contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  external_id TEXT,
  email TEXT,
  name TEXT,
  attributes JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  contact_id UUID REFERENCES crm_contacts(id),
  source TEXT,
  stage TEXT NOT NULL DEFAULT 'new',
  score NUMERIC,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE metric_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  website_id UUID REFERENCES websites(id),
  metric_name TEXT NOT NULL,
  metric_value NUMERIC,
  dimensions JSONB NOT NULL DEFAULT '{}',
  measured_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  provider_customer_id TEXT,
  provider_subscription_id TEXT,
  plan_code TEXT NOT NULL,
  status TEXT NOT NULL,
  current_period_end TIMESTAMPTZ
);

CREATE TABLE usage_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  meter TEXT NOT NULL,
  quantity NUMERIC NOT NULL,
  unit_cost NUMERIC,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  actor_type TEXT NOT NULL,
  actor_id TEXT,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  details JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_websites_tenant ON websites(tenant_id);
CREATE INDEX idx_tasks_tenant_status ON tasks(tenant_id, status);
CREATE INDEX idx_tasks_created ON tasks(created_at);
CREATE INDEX idx_memories_tenant ON memories(tenant_id);
CREATE INDEX idx_pages_site ON seo_pages(website_id);
CREATE INDEX idx_rankings_keyword_time ON ranking_snapshots(keyword_id, measured_at DESC);
CREATE INDEX idx_audit_tenant_time ON audit_events(tenant_id, created_at DESC);

-- Production requirement:
-- Enable and test Row Level Security on every tenant-owned table.
-- Derive tenant identity from authenticated server-side claims, never from
-- an untrusted client-supplied tenant_id alone.
