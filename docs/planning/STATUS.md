# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-16 (Phase 9 README refresh).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract **green** —
acceptance probe **3/3 PASS** with 249 ADR facts loaded (`chandrav` @
`memory.chandrav.dev`).

**Build track:** Phases **6–8 core code** landed. **Public/private boundary** scrubbed
(ADR 038). **Phase 5 bulk load** — **249 ADR facts live** in bank. **Phase 9 polish**
in progress — eval CI gate ✅; README refresh ✅; Grafana deploy doc remains.

## Current phase

**Phase 9 polish (in progress).** Eval CI gate ✅; README refresh ✅; Grafana deploy doc
(`monitor.` route + compose profile) remains.

## Done this session (2026-06-16)

- **README refresh (Phase 9):** honest phase/status claims — remote MCP live, LifeGraph
  in-memory POC, manual SSH deploy (no CD yet), eval CI gate, observability code vs
  Grafana `monitor.` deploy target. Added build-status table + `docs/setup.md` pointer.

## Last decisions

- Phase 9 next slice after README: **Grafana deploy doc** (unless bulk ingest pushes
  import-cache append-to-cache first).
- Phase 9 eval gate uses **synthetic gold only** for now — fast, no Docker stack; live
  Mem0 eval against expanded gold stays in BACKLOG.
- Public repo carries engineering context only; operator profile + ventures are private.
- Canonical public `user_id` is `primary-user`; live deploy overrides via env (private doc).

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
Phase 9 Grafana deploy doc; import cache append-to-cache.

## Open blockers / risks

- **Import cache refresh** — full `list_all_memories` after each write overloaded server
  on bulk run 1; idempotent re-run recovered; consider append-to-cache fix.
- **Phase 9 polish** — Grafana deploy doc (`monitor.` route + compose profile) remains.
- **`GET /memories` cap** — live API returns ~20 rows regardless of `limit`; prefix
  discovery must use exact `external_id` search filter (documented in retrieval layer).

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev` (setx persisted 2026-06-11).
- Cursor shells may need env reload:
  `$env:AI_MEMORY_BASE_URL = [Environment]::GetEnvironmentVariable('AI_MEMORY_BASE_URL','User')`

## Next action

> **RESUME HERE — Phase 9 polish (continued):**
> **Grafana deploy doc** — wire `monitor.` Caddy route + Prometheus/Grafana compose
> profile (DNS already reserved). Or tackle **import cache append-to-cache** if bulk
> ingest is the priority.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
