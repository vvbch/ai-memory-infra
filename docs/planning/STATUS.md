# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-16 (Phase 9 Grafana deploy doc).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract **green** —
acceptance probe **3/3 PASS** with 249 ADR facts loaded (`chandrav` @
`memory.chandrav.dev`).

**Build track:** Phases **6–8 core code** landed. **Public/private boundary** scrubbed
(ADR 038). **Phase 5 bulk load** — **249 ADR facts live** in bank. **Phase 9 polish**
— eval CI gate ✅; README refresh ✅; Grafana deploy doc + compose profile ✅.

## Current phase

**Phase 9 polish (nearly done).** Eval CI gate ✅; README refresh ✅; Grafana deploy
doc + `observability` compose profile ✅. Remaining polish: live `monitor.` enable on
VPS (operator SSH) or import-cache append-to-cache.

## Done this session (2026-06-16)

- **Grafana deploy doc (Phase 9):** `docs/observability-deploy.md`; enabled Caddy
  `monitor.` route; added `docker-compose.observability.yml` (Prometheus + Grafana +
  node-exporter behind `observability` profile); provisioning + starter dashboards;
  `make deploy-obs`; updated setup/runbook/interfaces/README.

## Last decisions

- Observability stays **profile-gated** (tenet 7) — default `deploy` unchanged;
  `make deploy-obs` enables Grafana on `monitor.`.
- Mem0 `/metrics` scrape target may stay DOWN until ADR 014 app instrumentation ships;
  node-exporter host metrics work immediately.
- Phase 9 eval gate uses **synthetic gold only** for now — live Mem0 eval stays in BACKLOG.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
import cache append-to-cache; live VPS `monitor.` enable (operator SSH).

## Open blockers / risks

- **Import cache refresh** — full `list_all_memories` after each write overloaded server
  on bulk run 1; idempotent re-run recovered; consider append-to-cache fix.
- **`GET /memories` cap** — live API returns ~20 rows regardless of `limit`; prefix
  discovery must use exact `external_id` search filter (documented in retrieval layer).
- **Mem0 `/metrics`** — Prometheus job configured; endpoint not yet on Mem0 server.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev` (setx persisted 2026-06-11).
- Cursor shells may need env reload:
  `$env:AI_MEMORY_BASE_URL = [Environment]::GetEnvironmentVariable('AI_MEMORY_BASE_URL','User')`

## Next action

> **RESUME HERE — Phase 9 polish (wrap-up) or parked work:**
> **Operator:** SSH to VPS, set `GRAFANA_ADMIN_PASSWORD` in `infra/.env`, run
> `make deploy-obs`, verify `https://monitor.<domain>/` — or tackle **import cache
> append-to-cache** if bulk ingest is the priority.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
