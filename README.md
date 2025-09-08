# Kyros – Agent Console & Orchestrator

Monorepo for the Kyros Agent Console (Next.js), Orchestrator (FastAPI), and local Terminal Daemon (node-pty).

## 0) Goals & Non‑Negotiables

**What “v1” must ship:**

* **Collab API** with **ETag + atomic writes**, **lease-based execution**, and **append‑only events** exposed via SSE/long‑poll tail.
* **Jobs vertical slice** (auth → create job → stub variant → accept → export → list).
* **Console UI**: pages for **Agents**, **Tasks (Kanban)**, **Leases**, **Events (live tail)**, plus **Jobs / Studio / Scheduler / Settings** wired to APIs.
* **Worker**: Celery+Redis with at least one safe executor (e.g., lint/format) that **acquires leases**, **emits events**, handles **retry/backoff**.
* **Quality gates**: pre‑commit, unit tests (FE/BE), Playwright E2E, secret scan, `.env.example`, basic rate limits and JWT, `/readyz` deep checks.&#x20;

**Stretch (nice‑to‑have):**

* **Omnichannel** “Command Center” surfaces (WebSocket/Email/API/Slack/Webhook) + Remote Control UI.
* **LangGraph** runner mounted in worker for structured agent flows.
* Fast UI skin using **TeleportHQ/Plasmic** if design time is tight.

---

## 1) Architecture Blueprint

**Monorepo** (ports FE:3001, BE:8000):

```
frontend/            React 18 + Vite + TS + Tailwind (dark-first)
backend/             FastAPI + SQLAlchemy + Alembic + Celery + Redis + Postgres
collaboration/       state/*.json (tasks|locks|agents), events/events.jsonl, logs/log.md
mcp/                 kyros_collab_server stub (stdio JSON-RPC)
scripts/             start/run/seed/test scripts
docs/                ARCHITECTURE, DEPLOYMENT, TESTING, RUNBOOKS, ADRs, BUILD_NOTES
```

* **Collab store** is the source of truth for agent workflow objects; **ETag** encodes file digest + version; writes are **atomic replace** guarded by `If‑Match`.
* **Events** are append‑only `JSONL` with SSE tail for live UI.
* **Leases not locks**: entries with `ttl_seconds` + `heartbeat_at`; stale reclaim emits events.
* **Jobs** persisted in Postgres; variants editable/acceptable and exportable via API.&#x20;

**Optional:** LangGraph runner inside Celery process; orchestrates tool calls but still acquires **leases** and emits **events** for observability.

---

## 2) Milestones & Work Breakdown (in order)

### Phase 0 — Repo Scaffolding & Context Hygiene

* Fork your **Full‑Stack FastAPI Template** baseline (or equivalent).
* Create monorepo folders + **ports** + **env files**.
* Add **pre‑commit**, linters/formatters (black/isort/ruff, eslint/biome), secret scan.
* Seed `collaboration/state/*.json` and `events.jsonl`.
* Add **scripts**: `start-frontend.sh`, `start-backend.sh`, `run-tests.sh`, `seed-dev.sh`.
* CI skeleton: build, backend tests, frontend tests, e2e, security scan, PR checks summary.&#x20;

### Phase 1 — Collab API (ETag + Atomic) & Events Tail

**Backend routes** (FastAPI):

* `GET /collab/state/{kind}` → `{data|text, etag}`.
* `POST /collab/tasks` (create) / `PATCH /collab/tasks/{id}` with `If‑Match` ETag.
* Transitions: `POST /collab/tasks/{id}/transition`.
* Leases: `POST /collab/leases/acquire` / `POST /collab/leases/{lock_id}/release`.
* Events: `POST /collab/events` (append JSONL), `GET /collab/events/tail` (SSE).
* Health: `/healthz`, `/readyz` (DB/Redis/queue checks).
  **Tests:** ETag mismatch, atomic write rollback, stale lease reclaim, SSE tail.
  **Observability:** structured logs, Sentry hooks (env‑driven).&#x20;

### Phase 2 — Console (Collab Pages)

**Frontend pages** with TanStack Query + SSE:

* **Agents** (role/skills/status/last\_seen; toggle availability).
* **Tasks** Kanban: `queued → claimed → in_progress → review → approved → merging → done`, dependency badges & DoD checklist; transitions via Collab API.
* **Leases** (TTL countdown, reclaim stale).
* **Events**: live tail + filters + “Generate human log”.
* UX: toasts, skeletons, `data-testid`.
  **Feature flags**: `config/flags.json` demoMode on/off.&#x20;

### Phase 3 — Jobs Vertical Slice

**API:**

* `POST/GET /jobs`, `GET /jobs/{id}`, `GET/PUT /variants/{id}`, `POST /export/{variant_id}`, `POST/GET /schedule`.
  **Models & Alembic:** User, Preset, Job, Variant, Schedule, Tool, AuditEvent.
  **Auth:** JWT (access/refresh), rate limits, input validation.
  **FE:** Jobs list → Job detail → Variant accept → Export flow.&#x20;

### Phase 4 — Runner & Safe Executor (+ Optional LangGraph)

* Celery worker acquires **lease**, runs **safe executor** (e.g., format Markdown, run linter), emits events, retries with backoff, releases lease.
* Optional: mount **LangGraph** agent flow inside worker for structured tools; surface run status via events.&#x20;

### Phase 5 — Omnichannel Command Center (MVP)

* **Unified Communication Hub** (WS/Email/API/Slack/Webhook) + channel adapters.
* **Remote Control UI**: Real‑time, Scheduled, Triggers; interactive terminal; activity feed.
* **Email Commander** (IMAP/SMTP) to parse commands (pattern/JSON/NL) and reply.
* **Slack**: slash commands + status links.
* **Security**: per‑channel rate limits + API‑key/JWT checks + audit trail.

> Scope this as a demo‑grade layer in v1; wire through the **Jobs** and **Collab** APIs so commands translate into task/job mutations.

### Phase 6 — E2E & CI Hardening

* **Playwright** happy‑path: Studio → Generate → Accept → Export; Collab flows; collect traces/video artifacts.
* GitHub Actions: `build-verification`, `frontend-tests`, `backend-tests`, `e2e-tests`, `security-scan`, `pr-checks-summary`; branch protection contexts.&#x20;

### Phase 7 — Docs & Runbooks

* `ARCHITECTURE.md`, `DEPLOYMENT.md`, `TESTING.md`, `RUNBOOKS.md`, `ADRS/adr-0001-template.md`, `DEVIATIONS.md`, `BUILD_NOTES.md`.
* **Commit/PR protocol** and **Context Reset** mini‑brief for sub‑tasks.&#x20;

---

## 3) Backlog with IDs (seed immediately)

Create these tasks in `collaboration/state/tasks.json` (you can reuse IDs):

* **T‑100**: Collab API with ETag + SSE (backend)
* **T‑101**: Console pages (Agents/Tasks/Leases/Events)
* **T‑102**: Celery runner + safe executor (backend)
* **T‑103**: Jobs vertical slice (auth→job→variant→accept→export)
* **T‑104**: Playwright flows (Collab + Jobs) + `data-testid`
* **T‑105**: Docs & Runbooks + ADR template
  Each task carries a DoD per Section 8 (**tests, pre‑commit, docs, critic review, events emitted**).&#x20;

Add Omnichannel tasks:

* **T‑200**: Omnichannel hub (WS/Email/API/Slack/Webhook) + audit log.
* **T‑201**: Remote Control UI tabs (Real‑Time/Scheduled/Triggers) + activity feed.
* **T‑202**: Email Commander + parsing + response loop.
* **T‑203**: Slack slash commands + deep link to tasks/jobs.
* **T‑204**: Channel rate limiting + API‑key validation middleware.

---

## 4) API Contracts (key details)

**Collab API**

* `GET /collab/state/{kind}` → `{data|text, etag}`
* `POST /collab/tasks` → `{id}`
* `PATCH /collab/tasks/{id}` with `If‑Match: <etag>` → `{ok, etag}`
* `POST /collab/tasks/{id}/transition` → `{old_status, new_status}`
* `POST /collab/leases/acquire` / `.../{lock_id}/release` → `{lock_id}` / `{ok}`
* `POST /collab/events` → `{ok}`
* `GET /collab/events/tail?since=<ts>` → SSE stream (newline‑delimited JSON).&#x20;

**Jobs API**

* `POST /jobs` → `{id, status:"queued"}`; `GET /jobs` and `/jobs/{id}`
* `GET/PUT /variants/{id}`
* `POST /export/{variant_id}` (download or JSON)
* `POST/GET /schedule` (cron or ISO schedule).&#x20;

**Auth/Security**

* JWT (access/refresh), basic **rate limits**, **input validation**, and **audit events**.&#x20;

---

## 5) Concurrency & Data Integrity

**ETag**

* Compute ETag as strong hash of canonicalized JSON + monotonic version.
* **PATCH** requires `If‑Match`; server verifies ETag and writes via **atomic replace** (temp file + fsync + rename).
* On mismatch → `412 Precondition Failed`; client retries with jitter and latest ETag.
  **Events**
* Always append `{ts, event, actor, target, details}` to `events.jsonl`; never mutate historical lines.
* SSE tail: keep‑alive + `Last-Event-ID` support to resume.
  **Leases**
* Structure: `{lock_id, resource, holder, acquired_at, ttl_seconds, heartbeat_at}`.
* Reclaim if `now > heartbeat_at + ttl`; emit `lease_reclaimed`.&#x20;

---

## 6) Worker & Executors

* Celery app connects to Redis; tasks acquire **lease**, run safe executor(s):

  * `docs/format` (Prettier/MD formatter), `lint` (ruff/flake8), or `docs/changelog` generator.
* Emit events: `task_claimed`, `executor_started`, `executor_succeeded|failed`, `lease_released`.
* **Backoff**: exponential with jitter on transient errors.
* **Optional LangGraph**: define a small graph (fetch → transform → write) to showcase structured flows and tool calls; still report via events.&#x20;

---

## 7) Frontend Details

* **Data layer**: TanStack Query; mutation invalidation + optimistic updates for Kanban moves.
* **Events page**: SSE tail with filters (by task/agent/event type) + “Generate human log” (server summarizes selected events).
* **Leases page**: TTL countdown per lease; “Reclaim stale” action.
* **Jobs**: list/detail/variant/accept/export; toasts on success/error.
* **Studio**: minimal shell to kick off a Job or Variant from a preset.
* **Settings**: presets CRUD.
* **Omnichannel UI**:

  * Channel overview cards (status, metrics).
  * **Remote Control**: tabs (Real‑Time / Scheduled / Triggers), terminal area, response pane.
  * **Channels** page: per‑channel controls & live command flow visualization.
* **Feature flags**: `demoMode` + `schedulerEnabled` in `config/flags.json`.&#x20;

> If you want a polished shell quickly, generate a layout with **TeleportHQ/Plasmic** and drop into `frontend/`, then wire the components to our hooks.

---

## 8) CI, Testing, and DoD

**Unit**

* Backend: ETag/atomic write tests; leases; events tail; Jobs CRUD.
* Frontend: components/hooks with Vitest; MSW fixtures for demo mode.

**E2E**

* Playwright flows:

  1. Studio → Generate Job → Variant Accept → Export (artifact check).
  2. Collab: create task → claim (lease) → transition → events visible.

  * Upload traces/video artifacts on failure.

**Pipelines**

* Actions: build‑verification, frontend-tests, backend-tests, e2e-tests, security-scan, pr-checks-summary; branch protection.

**Definition of Done (per task)**

* Tests updated, pre‑commit passing (format/lint/type/secrets), docs updated, **critic review**, events emitted where relevant.&#x20;

---

## 9) Security & Ops

* **JWT** auth + refresh; **API key** for channel webhooks; per‑channel **rate limiting**.
* **/readyz** deep check: DB migration status, Redis ping, Celery queue roundtrip.
* **Sentry** optional via env; structured JSON logs; audit events into DB and/or events stream.
* `.env.example` at repo root; never commit real secrets.&#x20;

---

## 10) Data Model (Jobs slice)

**Tables (SQLAlchemy + Alembic):**

* `users`, `presets`, `jobs (id, status, created_by, created_at)`,
* `variants (id, job_id, status, payload, accepted_at)`,
* `schedules (id, cron|iso, next_run, active)`,
* `tools (id, name, config)`,
* `audit_events (id, ts, actor, action, payload)`.&#x20;

---

## 11) Dev UX & PR Protocol

* Branch naming: `feat/<task-id>-slug`.
* Commit template with rationale, touched files, tests, risks/mitigations.
* PR body: scope, acceptance criteria verified, failing tests (if any) explain why, and UI screenshots.
* **Context Reset** mini‑brief between subtasks to keep agents focused.&#x20;

---

## 12) “Day‑1” Commands & Files to Create

**Repo**

```bash
# backend
uv venv && source .venv/bin/activate || python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] pydantic-settings sqlalchemy alembic psycopg2-binary \
            celery[redis] redis python-jose[cryptography] passlib[bcrypt] httpx sse-starlette

# frontend
npm create vite@latest frontend -- --template react-ts
cd frontend && npm i @tanstack/react-query axios react-router-dom tailwindcss @radix-ui/react-* \
                   @uiw/react-md-editor reactflow recharts
```

**Backbone files**

* `backend/main.py`: app + routers for `/collab/*`, `/jobs/*`, `/auth/*`, `/healthz`, `/readyz`.
* `backend/collab/` module: ETag utils, atomic write, SSE tail, lease manager.
* `backend/jobs/` module: models, CRUD, export service.
* `frontend/src/pages/` for Agents, Tasks, Leases, Events, Jobs, Studio, Scheduler, Settings, Auth.
* `collaboration/state/tasks.json|locks.json|agents.json`, `collaboration/events/events.jsonl`, `collaboration/logs/log.md`.
* `scripts/*.sh` and `.env.example`.&#x20;

---

## 13) Risk Register (with mitigations)

* **Race conditions on ETag** → server‑side atomic replace + `412` handling; client retry w/ jitter.
* **SSE scale** → fall back to long‑poll; server keep‑alives; filter at source.
* **Email polling latency** → cron‑like poll + idempotency keys; promote to webhook where possible.
* **Slack/Channel rate limits** → per‑channel throttling + backoff; capture 429s in audit.
* **Secrets sprawl** → `.env.example`, sealed secrets in CI, secret scan in pre‑commit and pipeline.&#x20;

---

## 14) Deliverables Checklist (what reviewers should see)

* **Backend:** endpoints live + OpenAPI `/docs`; JWT login in dev.
* **Frontend:** 8 pages wired; demoMode on; live Events tail; “reclaim stale lease” button works.
* **Worker:** Celery task demonstrates lease lifecycle & event emissions.
* **DB:** Alembic migrations applied; Jobs flow green.
* **CI:** all workflows green; Playwright artifacts on failure.
* **Docs:** architecture, deployment, testing, runbooks, ADR template, deviations, build notes.
* **SUMMARY.md** with endpoints/pages implemented + next steps.&#x20;

---

## 15) Immediate Next Steps (actionable)

1. **Initialize monorepo** scaffold + ports + `.env.example` + scripts.
2. **Implement Collab API** with ETag/atomic write + SSE tail; seed `T‑100`‑`T‑105`.
3. **Build UI**: Agents/Tasks/Leases/Events with real calls and SSE tail.
4. **Jobs slice**: models → routes → FE flows → export.
5. **Celery worker**: safe executor + lease lifecycle + events.
6. **Wire CI**: unit + E2E + security scans; enable branch protection.
7. **(Optional)** Add Omnichannel hub + Remote Control Center; mount LangGraph in worker.


