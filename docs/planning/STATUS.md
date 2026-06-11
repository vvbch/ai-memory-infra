# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (Phase 5 migration — import_md TDD green).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`. Memory
write/read contract locked; acceptance probe PASS. **Bulk CSV ingest** parked
until Chandra finishes `data/reconciled-facts.csv` — unrelated to build track.

**Active build track:** **Phase 5 migration pipeline** — markdown parser done;
categorizer + dedup + CLI next.

## Current phase

**Phase 5 migration (TDD).** `import_md.py` splits `.md` on headings and emits
bulk-seed-shaped facts with stable `migration:md:…` external_ids.

## Done this session (2026-06-11)

- **`docs/design/migration-pipeline.md`** — short pipeline design.
- **`src/migration/import_md.py`** + **`tests/test_migration/test_import_md.py`**
  (7 tests green).

## Last decisions

- Migration outputs same contract as `bulk_seed_importer` (`infer=false`, `event_date`,
  `source_doc_id`); does not write live bank until explicit dry-run approval.
- CSV reconciled seed remains operator-driven; migration is for repo/docs automation.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest (operator); Phase 3
premise test (after phases 5–8); market world model.

## Open blockers / risks

- **Bulk CSV load** — waiting on operator sheet (say "ingest the sheet" when ready).
- **OpenClaw adapter** — not in workspace.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.

## Next action

> **RESUME HERE — Phase 5 migration (categorizer TDD):**
> Add failing tests in `tests/test_migration/test_categorizer.py` for venture
> tagging (ADR 003 paths/keywords), then implement `src/migration/categorizer.py`.
> After that: `dedup.py`, then `cli.py` dry-run over a docs directory.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
