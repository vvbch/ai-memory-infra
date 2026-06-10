# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (ADR 028 Neo4j source probe closed; pgvector ✅).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **ADR 036 complete.** **ADR 037 closed.**
**ADR 028 pgvector source tagging live** on all in-workspace writers; Neo4j graph
`source` propagation is **N/A until LifeGraph (Phase 6)** — Mem0 writes no graph
(ADR 032; droplet confirmed 0 nodes before/after probe).

**Curated bank (`user_id=chandrav`):** extension auto-capture off by policy; MCP
primary write surface.

## Current phase

**Infra phases 0–4 live; ADR 036 + ADR 037 closed.** Phases 5–8 stubs — **active
build track**.

## Done this session (2026-06-11)

- **ADR 028 Neo4j source probe** — live verify: `metadata.source` round-trips on
  pgvector; Neo4j `node_count=0` before and after tagged write (no Mem0 graph —
  not a dropped field). Added `scripts/verify_source_propagation.py` + tests;
  closed ADR 032 belt-and-suspenders droplet confirm.

## Last decisions

- Neo4j `metadata.source` enforcement is **deferred to LifeGraph Phase 6**, not a
  Mem0-server patch today (graph store absent at pinned mem0ai ref).
- OpenClaw adapter stays parked until repo checkout — never fork `user_id`.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Top: **MCP droplet redeploy** (ADR 037
delete/update tools live); OpenClaw adapter gate.

## Open blockers / risks

- **MCP droplet behind git** — ADR 037 delete/update tools until redeploy.
- **OpenClaw adapter** — not in workspace; conformance audit blocked on checkout.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` param for paths with
  spaces/parens.

## Next action

> **RESUME HERE — MCP droplet redeploy (ADR 037 tools on production):**
> Redeploy the MCP proxy container on the droplet so `delete_memory` /
> `update_memory` (ADR 037) are live in production — `make deploy` or equivalent
> SSH pull + compose up on `168.144.145.29`. Verify with a throwaway add →
> update → delete round-trip via remote MCP or `scripts/memory.py`.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
