# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (Phase 5 migration — CLI dry-run green).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`. Memory
write/read contract locked; acceptance probe PASS. **Bulk CSV ingest** parked
until Chandra finishes `data/reconciled-facts.csv` — unrelated to build track.

**Active build track:** **Phase 5 migration pipeline** — parse → classify → dedup →
CLI dry-run complete. No live bank writes until operator approves export + bulk load.

## Current phase

**Phase 5 migration (TDD).** `python -m migration import --source <dir> --dry-run`
wires the full pipeline; verified on `docs/decisions/` (37 files → 244 chunks).

## Done this session (2026-06-11)

- **`src/migration/cli.py`** + **`src/migration/__main__.py`** +
  **`tests/test_migration/test_cli.py`** (7 tests; 167 total).

## Last decisions

- CLI defaults to dry-run only; live import deferred to JSON export +
  `bulk_seed_importer` (operator gate).
- `--use-bank` optional for dedup against live Mem0 (needs API credentials).

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest (operator); Phase 3
premise test (after phases 5–8); market world model.

## Open blockers / risks

- **Bulk CSV load** — waiting on operator sheet (say "ingest the sheet" when ready).
- **OpenClaw adapter** — not in workspace.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.

## Next action

> **RESUME HERE — Phase 5 export + operator gate:**
> Extend migration CLI with `--output facts.json` (bulk_seed_importer shape) from
> kept facts after dedup; operator runs `bulk_seed_importer.py --dry-run` then
> approves live load. Optional: `test_e2e_migration.py` with fake Mem0 client.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
