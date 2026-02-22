# Mailsystem

Production-ready, modular mail system built with FastAPI, PostgreSQL, Redis, and Celery.
Includes a React frontend console for send/bulk/lookup/analytics actions.

## Architecture

- API layer (`app/api`) handles validation, idempotency, rate limiting, and enqueueing.
- Worker layer (`app/queue`, `app/services`) processes send/bulk jobs with retries and dead-lettering.
- Provider adapters (`app/providers`) abstract delivery transports (SMTP + Mock included).
- Template renderer (`app/templates`) supports Jinja2 with strict variables and text fallback.
- Persistence layer (`app/domain`, `app/db`) stores templates, emails, lifecycle events, webhook events, and DLQ records.

## Components

### API Endpoints

- `POST /send`
- `POST /send/bulk`
- `POST /webhooks/{provider}`
- `GET /emails/{email_id}?tenant_id=...`
- `GET /analytics?tenant_id=...&from=...&to=...&group_by=day|hour&template_id=...`
- `GET /health/live`
- `GET /health/ready`

### Queue and Workers

- Celery queues:
  - `mail.send`
  - `mail.scheduled`
  - `mail.bulk`
  - `mail.dlq`
- Retry policy:
  - max attempts: `MAX_RETRIES` (default 5)
  - exponential backoff with jitter (`app/queue/retry_policy.py`)
  - failed terminal sends are persisted into `dead_letters`

### Idempotency and Duplicate Prevention

- API dedupes by DB unique constraint `(tenant_id, idempotency_key)`.
- Same key returns `202` with existing `email_id` and `idempotency_reused=true`.
- Webhook dedupe via unique `(provider, provider_event_id)` in `provider_webhook_events`.

### Status Tracking

Statuses include:
- `queued`
- `scheduled`
- `processing`
- `sent`
- `delivered`
- `opened`
- `failed`

Lifecycle events are appended to `email_events`.

## Data Model

Schema migration SQL: `app/db/migrations/001_init.sql`

Main tables:
- `tenants`
- `templates`
- `emails`
- `email_events`
- `provider_webhook_events`
- `bulk_jobs`
- `dead_letters`

## Configuration

See `.env.example`.

Key env vars:
- `DATABASE_URL`
- `REDIS_URL`
- `DEFAULT_PROVIDER`
- `SMTP_*`
- `MAX_RETRIES`, `RETRY_BASE_SECONDS`, `RETRY_MAX_SECONDS`
- `RATE_LIMIT_*`
- `WEBHOOK_SECRET_SMTP`, `WEBHOOK_SECRET_MOCK`

## Local Setup

1. Create Conda environment:

```bash
conda env create -f environment.yml
conda activate mailsystem
```

2. Install project packages in editable mode:

```bash
./scripts/bootstrap.sh
```

`bootstrap.sh` installs the local package in editable mode without downloading dependencies (Conda env handles them).

3. Apply schema:

```bash
psql "$DATABASE_URL" -f app/db/migrations/001_init.sql
```

4. Start API:

```bash
uvicorn app.main:app --reload
```

5. Start worker:

```bash
celery -A app.queue.celery_app.celery_app worker -Q mail.send,mail.scheduled,mail.bulk --loglevel=INFO
```

6. Start React frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

Optional API base override:

```bash
VITE_API_BASE=http://localhost:8000 npm run dev
```

## Docker

```bash
cd docker
docker compose up --build
```

## Example Usage

### Create a template and tenant (sample SQL)

```sql
INSERT INTO tenants(id, name, status) VALUES ('tenant-1', 'Tenant 1', 'active');
INSERT INTO templates(id, tenant_id, name, version, subject_template, html_template, text_template, is_active)
VALUES ('tpl-1', 'tenant-1', 'welcome', 1, 'Welcome {{name}}', '<h1>Hello {{name}}</h1>', NULL, true);
```

### Send transactional email

```bash
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id":"tenant-1",
    "recipient":{"email":"alice@example.com","name":"Alice"},
    "template_id":"tpl-1",
    "variables":{"name":"Alice"},
    "metadata":{"source":"api"},
    "idempotency_key":"mail-001"
  }'
```

### Send bulk

```bash
curl -X POST http://localhost:8000/send/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id":"tenant-1",
    "template_id":"tpl-1",
    "recipients":[{"email":"a@example.com"},{"email":"b@example.com"}],
    "shared_variables":{"name":"friend"},
    "idempotency_key":"bulk-001"
  }'
```

## Scaling Strategy

- Run stateless API replicas behind a load balancer.
- Scale Celery workers independently by queue and workload type.
- Keep Redis for broker/rate-limit state and PostgreSQL for durable source-of-truth state.
- Add partitioning for `email_events` in high-volume deployments.
- Use read replicas for analytics-heavy workloads.

## Failure Handling

- Transient provider failures are retried with exponential backoff + jitter.
- Permanent failures mark email as `failed` and create dead-letter records.
- Webhook processing is idempotent and replay-safe via signature + unique provider event IDs.

## Extension Points

- Add new providers by implementing `ProviderAdapter` and registering in `app/providers/registry.py`.
- Extend template strategy in `app/templates/renderer.py`.
- Add sinks/metrics subscribers by consuming `email_events`.

## Tests

- Unit: renderer, retry policy, provider behavior, signature validation.
- Integration: `/send` idempotency flow.
- E2E: signed webhook ingestion path.

Run:

```bash
pytest
```
