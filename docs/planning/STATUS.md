# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-11 (Cursor User rules handoff done; ADR 028 audit + gate).
Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **ADR 036 is complete** on every targeted
surface. **ADR 037 closed.** **ADR 028 audited** on in-workspace consumers
(extension ✅, MCP proxy ✅); OpenClaw adapter still pending (external repo).

**Curated bank (`user_id=chandrav`):** ~21 facts; extension auto-capture off by
policy; MCP primary write surface.

## Current phase

**Infra phases 0–4 live; ADR 036 + ADR 037 closed.** Phases 5–8 stubs — **active
build track**.

## Done this session (2026-06-11)

- **Cursor User rules handoff** — operator updated Settings → Rules → User rules
  with commit/push alignment for ai-memory workspace.
- **ADR 028 audit** — extension + MCP proxy conform; `metadata.source` enforced on
  MCP `add_memory`; `check_memory_contract.py` extended + tests added; ADR 028
  Propagation/conformance section added.

## Last decisions

- Global Cursor User rules now distinguish default (ask before commit) vs
  ai-memory workspace (commit+push per `AGENTS.md`).
- OpenClaw adapter (`serenichron/openclaw-memory-mem0`) stays parked until repo
  is checked out — never fork `user_id`; patch adapter for `source`/`agent_id`.

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Top: Neo4j `metadata.source` propagation
verify; OpenClaw adapter gate; MCP droplet redeploy for ADR 037 tools.

## Open blockers / risks

- **MCP droplet behind git** — ADR 037 delete/update tools until redeploy.
- **OpenClaw adapter** — not in workspace; conformance audit blocked on checkout.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` param for paths with
  spaces/parens.

## Next action

> **RESUME HERE — BACKLOG P2 top item (Neo4j source propagation) or MCP droplet
> redeploy:**
> 1. Verify Mem0 write path propagates `metadata.source` to Neo4j nodes (probe +
>    patch if dropped) — see BACKLOG P2 `[memory] Enforce source into Mem0 and
>    Neo4j graph metadata`.
> 2. Or: redeploy MCP droplet so ADR 037 delete/update tools are live.

**How to talk to the next agent:** type **`/resume`** — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
