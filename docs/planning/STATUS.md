# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-12 (Phase 9 eval CI gate landed).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract **green** —
acceptance probe **3/3 PASS** with 249 ADR facts loaded (`chandrav` @
`memory.chandrav.dev`).

**Build track:** Phases **6–8 core code** landed. **Public/private boundary** scrubbed
(ADR 038). **Phase 5 bulk load** — **249 ADR facts live** in bank. **Phase 9 polish**
started — eval regression gate now blocks CI on synthetic gold (ADR 007 thresholds).

## Current phase

**Phase 9 polish (in progress).** Eval CI gate ✅; README refresh and Grafana deploy doc
remain.

## Done this session (2026-06-12)

- **Eval CI gate (Phase 9):** `scripts/run_eval_gate.py` runs retrieval/extraction/
  categorization suites against bundled synthetic gold; fails below ADR 007 thresholds.
  Wired into `ci.yml` (every push/PR) + new `eval-suite.yml` (weekly + manual).
  Synthetic retrieval gold calibrated so `precision@5` ≥ 0.7; contract + interfaces
  updated (`practice-eval-framework` → enforced).

## Last decisions

- Phase 9 eval gate uses **synthetic gold only** for now — fast, no Docker stack; live
  Mem0 eval against expanded gold stays in BACKLOG.
- Public repo carries engineering context only; operator profile + ventures are private.
- Canonical public `user_id` is `primary-user`; live deploy overrides via env (private doc).

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
Phase 9 README refresh + Grafana deploy doc; import cache append-to-cache.

## Open blockers / risks

- **Import cache refresh** — full `list_all_memories` after each write overloaded server
  on bulk run 1; idempotent re-run recovered; consider append-to-cache fix.
- **Phase 9 polish** — README refresh + Grafana deploy doc remain.
- **`GET /memories` cap** — live API returns ~20 rows regardless of `limit`; prefix
  discovery must use exact `external_id` search filter (documented in retrieval layer).

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev` (setx persisted 2026-06-11).
- Cursor shells may need env reload:
  `$env:AI_MEMORY_BASE_URL = [Environment]::GetEnvironmentVariable('AI_MEMORY_BASE_URL','User')`

## Next action

> **RESUME HERE — Phase 9 polish (continued):**
> Pick the next slice — **README refresh** (honest phase/status claims) or **Grafana
> deploy doc** (`monitor.` route + compose profile) — or tackle **import cache
> append-to-cache** if bulk ingest is the priority.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
