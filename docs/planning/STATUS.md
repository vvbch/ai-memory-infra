# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (Phases 6–8 core TDD green).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`. Memory
write/read contract locked; acceptance probe PASS.

**Build track:** Phases **6–8 core code** landed today (LifeGraph, eval, observability
+ health). **Phase 5 live data load** scheduled tomorrow (operator). Phase 9 polish
and production wiring (Neo4j live seed, eval CI workflow, Grafana deploy) remain.

## Current phase

**Phases 6–8 (TDD stubs → implemented).** 209 tests green. LifeGraph in-memory POC;
eval metrics + starter gold data; Prometheus metrics + drift/alerts; health checker.

## Done this session (2026-06-11)

- **Phase 6:** `life_graph/{schema,graph_store,seed,queries,ingest}.py` + tests
- **Phase 7:** `eval/{retrieval,extraction,categorization,reporters,runners,guardrails}.py`
  + starter `gold_standard/*.json` + tests
- **Phase 8:** `observability/{metrics,drift_detector,alerts}.py` + tests
- **Health:** `health/checker.py` + tests

## Last decisions

- LifeGraph uses in-memory `GraphStore` for TDD; live Neo4j seed is a follow-up ops step.
- Eval gold datasets are starter-sized (not full 50+); expand after Phase 5 memory load.
- Phase 5 JSON export + live bulk load: **tomorrow** (operator).

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: bulk CSV ingest (operator); Phase 3
premise test; market world model; Phase 9 README/eval CI workflow/Grafana deploy.

## Open blockers / risks

- **Phase 5 data load** — tomorrow: export JSON + `bulk_seed_importer` with approval.
- **Bulk CSV load** — waiting on operator sheet.
- **OpenClaw adapter** — not in workspace.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.

## Next action

> **RESUME HERE — Phase 5 operator load (tomorrow):**
> Add migration CLI `--output facts.json`, run dry-run with `--use-bank`, operator
> approves, then `bulk_seed_importer.py` live load. After load: expand eval gold from
> real memories + optional Neo4j LifeGraph seed.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
