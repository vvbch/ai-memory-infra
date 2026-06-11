# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (Phase 5 migration — dedup TDD green).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`. Memory
write/read contract locked; acceptance probe PASS. **Bulk CSV ingest** parked
until Chandra finishes `data/reconciled-facts.csv` — unrelated to build track.

**Active build track:** **Phase 5 migration pipeline** — parse, classify, and dedup
done; CLI dry-run next.

## Current phase

**Phase 5 migration (TDD).** `dedup.py` filters facts whose `external_id` or
normalized text already exists in the bank (including within-batch duplicates).

## Done this session (2026-06-11)

- **`src/migration/dedup.py`** + **`tests/test_migration/test_dedup.py`**
  (8 tests green; 160 total).

## Last decisions

- Migration outputs same contract as `bulk_seed_importer` (`infer=false`, `event_date`,
  `source_doc_id`); does not write live bank until explicit dry-run approval.
- Dedup is deterministic pre-import filter; write-time `external_id` skip remains
  in `bulk_seed_importer` (ADR 037).

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest (operator); Phase 3
premise test (after phases 5–8); market world model.

## Open blockers / risks

- **Bulk CSV load** — waiting on operator sheet (say "ingest the sheet" when ready).
- **OpenClaw adapter** — not in workspace.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.

## Next action

> **RESUME HERE — Phase 5 migration (CLI dry-run):**
> TDD `src/migration/cli.py` — `python -m migration import --source ./docs/decisions/
> --dry-run` wires import_md → categorizer → dedup and prints chunk counts +
> sample `external_id`s (no live write). Add `tests/test_migration/test_cli.py` or
> extend e2e stub as needed.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
