# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (memory contract + acceptance probe PASS).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **Remote MCP** at `https://mcp.chandrav.dev`
ships five tools incl. delete/update (ADR 037).

**Curated bank (`user_id=chandrav`):** extension auto-capture off by policy; MCP
+ `scripts/memory.py` primary write surfaces.

**Contract locked (2026-06-11):** fact metadata (`event_date`, `source`,
`source_doc_id`, `namespace`, `external_id`), idempotent shared write path, read
convention (event_date recency, metadata filters, entity qualifier rerank). **5-fact
acceptance probe PASS** — see `docs/reports/acceptance-probe-2026-06-11.md`.

## Current phase

**Infra phases 0–4 live.** Phase 5 migration — parked behind reconciled fact seed.

## Done this session (2026-06-11)

- **`src/memory/contract.py` + `retrieval.py`** — event_date, namespace, read helpers.
- **`src/mcp_proxy/idempotent_write.py`** — shared verify-then-skip; wired to client,
  MCP, `memory.py`, bulk importer.
- **`scripts/acceptance_probe.py`** — live 6-fact probe, 3/3 queries PASS, cleanup OK.
- **ADR 037 amended** (SS6–8), interfaces §1b, tenet 20, extension `namespace` default.

## Last decisions

- `event_date` canonical; `occurred_at` dual-written for ADR 029 compat.
- `namespace` = flat tags (`public` \| `sensitive`) on one `user_id` (operator choice).
- Direct SQL on pgvector metadata deferred (ADR 037 §8 option B post-seed).
- Bulk load **not** started this session — reconciled fact set is next.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Top active: **reconciled fact seed** (separate
session). Parked: Phase 5 migration TDD; market world model; weekly compaction timer.

## Open blockers / risks

- **OpenClaw adapter** — not in workspace; conformance audit blocked on checkout.
- **MCP droplet** — redeploy needed for extended `add_memory` params (optional; bulk
  importer path used for probe).

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` param for paths with
  spaces/parens.
- `scripts/memory.py` shadows `src/memory/` if `scripts/` stays on `sys.path` — fixed
  via path bootstrap in scripts.

## Next action

> **RESUME HERE — reconciled fact seed:**
> Load the reconciled portfolio fact set via `scripts/bulk_seed_importer.py` with
> full metadata contract (`event_date`, `source`, `external_id`, `namespace`). Do not
> bulk-load until operator supplies the reconciled JSON. Re-run
> `scripts/acceptance_probe.py` if contract code changes.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
