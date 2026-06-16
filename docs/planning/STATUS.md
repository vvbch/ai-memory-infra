# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-16 (import cache append-to-cache).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract **green** —
acceptance probe **3/3 PASS** with 249 ADR facts loaded (`chandrav` @
`memory.chandrav.dev`).

**Build track:** Phases **6–8 core code** landed. **Phase 9 polish** — eval CI gate ✅;
README refresh ✅; Grafana deploy doc + compose profile ✅; bulk import cache fix ✅.

## Current phase

**Phase 9 polish (wrap-up).** Code/doc slices done. Remaining: operator enables
`monitor.` on VPS (`make deploy-obs`).

## Done this session (2026-06-16)

- **Import cache append-to-cache:** bulk seed importer no longer calls
  `list_all_memories` after every write — cache extends from the write response or a
  targeted `external_id` search (`idempotent_write.py`).

## Last decisions

- Bulk import cache: append on write / verify-after-timeout; full list only at start.
- Observability stays **profile-gated** — `make deploy-obs` on VPS is operator SSH.
- Mem0 `/metrics` scrape target may stay DOWN until ADR 014 app instrumentation ships.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
live VPS `monitor.` enable (operator SSH).

## Open blockers / risks

- **`GET /memories` cap** — live API returns ~20 rows regardless of `limit`; prefix
  discovery must use exact `external_id` search filter (documented in retrieval layer).
- **Mem0 `/metrics`** — Prometheus job configured; endpoint not yet on Mem0 server.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev` (setx persisted 2026-06-11).
- Cursor shells may need env reload:
  `$env:AI_MEMORY_BASE_URL = [Environment]::GetEnvironmentVariable('AI_MEMORY_BASE_URL','User')`

## Next action

> **RESUME HERE — operator one-way door or new thread:**
> **Operator:** SSH to VPS, set `GRAFANA_ADMIN_PASSWORD` in `infra/.env`, run
> `make deploy-obs`, verify `https://monitor.<domain>/` (`docs/observability-deploy.md`).
> Or pick next backlog slice (bulk CSV ingest, Phase 3 premise test).

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
