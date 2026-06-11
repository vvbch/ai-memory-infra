# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-11 (Phase 5 live load complete; acceptance probe regression).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract locked;
acceptance probe **regressed** after bulk load (1/3 pass — see blockers).

**Build track:** Phases **6–8 core code** landed. **Public/private boundary** scrubbed
(ADR 038). **Phase 5 bulk load** — **249 ADR facts live** in bank (`chandrav` @
`memory.chandrav.dev`); all verified by `external_id` search.

## Current phase

**Post–Phase 5 acceptance probe triage.** Live load done; probe must pass at scale
before calling the memory contract fully green.

## Done this session (2026-06-11)

- **Phase 5 live load:** `bulk_seed_importer` wrote 249 ADR facts to
  `chandrav@memory.chandrav.dev` (run 1: 193 before server disconnect on cache
  refresh; run 2: +56 idempotent). All 249 verified via `find_by_external_id`.
- **Acceptance probe:** `structured_filter` PASS; `backdated_recency` and
  `entity_collision` FAIL — probe facts drowned by ADR corpus in vector search
  (`docs/reports/acceptance-probe-2026-06-11.md`).

## Last decisions

- Public repo carries engineering context only; operator profile + ventures are private.
- Canonical public `user_id` is `primary-user`; live deploy overrides via env (private doc).
- Git history: **option 3 accepted** — no rewrite; strangers reading HEAD only are safe.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest; Phase 3 premise test;
Phase 9 README/eval CI workflow/Grafana deploy.

## Open blockers / risks

- **Acceptance probe regression** — 2/3 queries fail after 249-fact load; probe needs
  isolation from ADR corpus (external_id prefix or dedicated namespace).
- **Import cache refresh** — full `list_all_memories` after each write overloaded server
  on run 1; idempotent re-run recovered; consider append-to-cache fix.
- **Phase 9 polish** — README/eval CI workflow/Grafana deploy remain.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev` (setx persisted 2026-06-11).
- Cursor shells may need env reload:
  `$env:AI_MEMORY_BASE_URL = [Environment]::GetEnvironmentVariable('AI_MEMORY_BASE_URL','User')`

## Next action

> **RESUME HERE — triage acceptance_probe at scale:**
> Fix probe isolation so `backdated_recency` and `entity_collision` pass with 249 ADR
> facts loaded (filter by `probe:acceptance:` external_id prefix or dedicated namespace
> in `search_with_contract` / probe queries). Re-run `python scripts/acceptance_probe.py`.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action.
```
