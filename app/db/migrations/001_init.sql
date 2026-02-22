CREATE TABLE IF NOT EXISTS tenants (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS templates (
  id VARCHAR(64) PRIMARY KEY,
  tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
  name VARCHAR(128) NOT NULL,
  version INT NOT NULL,
  subject_template TEXT NOT NULL,
  html_template TEXT NOT NULL,
  text_template TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_template_tenant_name_version UNIQUE (tenant_id, name, version)
);

CREATE TABLE IF NOT EXISTS emails (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
  idempotency_key VARCHAR(128) NOT NULL,
  recipient_email VARCHAR(320) NOT NULL,
  recipient_name VARCHAR(255),
  template_id VARCHAR(64) NOT NULL REFERENCES templates(id),
  variables_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  provider_name VARCHAR(64) NOT NULL,
  provider_message_id VARCHAR(255),
  status VARCHAR(32) NOT NULL,
  scheduled_at TIMESTAMP,
  sent_at TIMESTAMP,
  delivered_at TIMESTAMP,
  opened_at TIMESTAMP,
  failed_at TIMESTAMP,
  failure_reason TEXT,
  attempt_count INT NOT NULL DEFAULT 0,
  next_retry_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_email_tenant_idempotency UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);
CREATE INDEX IF NOT EXISTS idx_emails_scheduled_at ON emails(scheduled_at);

CREATE TABLE IF NOT EXISTS email_events (
  id BIGSERIAL PRIMARY KEY,
  email_id VARCHAR(36) NOT NULL REFERENCES emails(id),
  tenant_id VARCHAR(64) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  event_time TIMESTAMP NOT NULL DEFAULT NOW(),
  provider VARCHAR(64),
  provider_event_id VARCHAR(255),
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_events_tenant_event_time ON email_events(tenant_id, event_time);
CREATE INDEX IF NOT EXISTS idx_email_events_email_event_type ON email_events(email_id, event_type);

CREATE TABLE IF NOT EXISTS provider_webhook_events (
  id BIGSERIAL PRIMARY KEY,
  provider VARCHAR(64) NOT NULL,
  provider_event_id VARCHAR(255) NOT NULL,
  tenant_id VARCHAR(64),
  signature_valid BOOLEAN NOT NULL,
  received_at TIMESTAMP NOT NULL DEFAULT NOW(),
  payload_hash VARCHAR(64) NOT NULL,
  CONSTRAINT uq_provider_event UNIQUE(provider, provider_event_id)
);

CREATE TABLE IF NOT EXISTS bulk_jobs (
  id VARCHAR(36) PRIMARY KEY,
  tenant_id VARCHAR(64) NOT NULL,
  template_id VARCHAR(64) NOT NULL,
  total_count INT NOT NULL,
  queued_count INT NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dead_letters (
  id BIGSERIAL PRIMARY KEY,
  email_id VARCHAR(36) NOT NULL,
  tenant_id VARCHAR(64) NOT NULL,
  last_error TEXT NOT NULL,
  attempt_count INT NOT NULL,
  moved_at TIMESTAMP NOT NULL DEFAULT NOW(),
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb
);
