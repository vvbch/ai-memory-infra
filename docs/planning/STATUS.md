# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (reconciled-facts CSV template; session handoff).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. Memory **write/read contract** locked and
**acceptance probe PASS** (`docs/reports/acceptance-probe-2026-06-11.md`).

**Curated bank (`user_id=chandrav`):** empty of probe rows; ready for reconciled
seed once Chandra finishes the sheet.

**Your sheet:** edit `data/reconciled-facts.csv` (Excel/Sheets OK — save as CSV
UTF-8). Delete `example:*` rows when done. Half-day update in progress — **no
bulk load until you say go.**

## Current phase

**Infra phases 0–4 live.** Bulk fact seed is the active gate; Phase 5 migration
and other buildouts **can continue in parallel** — they do not block on the CSV.

## Done this session (2026-06-11)

- Memory contract + idempotent writes + live acceptance probe (prior commit
  `8aaf2c9`).
- **`data/reconciled-facts.csv`** — operator-editable template with column contract.
- **`scripts/csv_to_bulk_seed.py`** — CSV → JSON → `bulk_seed_importer.py`.

## Last decisions

- Bulk ingest path: CSV (human edit) → JSON (script) → idempotent importer.
- `infer=false` default on curated rows (verbatim facts).
- Further infra buildouts allowed while CSV is being filled; only **bulk load**
  waits on the reconciled sheet.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. After seed: Phase 5 migration TDD; MCP droplet
redeploy for extended `add_memory`; weekly compaction timer.

## Open blockers / risks

- **Bulk load** — blocked on operator completing `data/reconciled-facts.csv`.
- **OpenClaw adapter** — not in workspace.

## Environment notes

- Windows: open CSV in Excel, **Save As → CSV UTF-8** to keep encoding clean.
- Rows with `external_id` starting `example:` are skipped on convert.

## Next action

> **RESUME HERE — after Chandra updates the CSV:**
> 1. `python scripts/csv_to_bulk_seed.py data/reconciled-facts.csv`
> 2. `python scripts/bulk_seed_importer.py data/reconciled-facts.json --dry-run`
> 3. On clean dry-run: `python scripts/bulk_seed_importer.py data/reconciled-facts.json`
>
> Say **"ingest the sheet"** when ready. Until then: optional parallel work only
> (no writes to production bank).

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
