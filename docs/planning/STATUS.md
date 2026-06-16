# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model in `AGENTS.md`.

**Last updated:** 2026-06-16 (LifeGraph redesign handoff).

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.example.com/docs` (operators
override via env — see private `OPERATOR.md`). Memory write/read contract **green** —
acceptance probe **3/3 PASS** with 249 ADR facts in Mem0/pgvector (`chandrav` @
`memory.chandrav.dev`).

**Graph reality:** Neo4j is **up but empty** (0 nodes). Memories are **not**
visualized as a graph today — only list/search via API/dashboard. **LifeGraph** (the
planned professional-life knowledge graph) was a **small in-memory POC** in code;
operator wants a **redesign from scratch** — see `docs/design/lifegraph.md`.

**Build track:** Phase 9 polish largely done (eval gate, README, Grafana doc, import
cache fix). **New thread:** LifeGraph redesign.

## Current phase

**LifeGraph redesign (draft).** Park Phase 9 operator chores (VPS `make deploy-obs`)
unless blocking.

## Done this session (2026-06-16)

- **Handoff:** documented what LifeGraph was vs what exists live; added redesign
  kickoff `docs/design/lifegraph.md` with open questions — POC in `src/life_graph/`
  frozen until new design approved.

## Last decisions

- **LifeGraph:** redesign from scratch — do not extend in-memory POC without approved
  `docs/design/lifegraph.md` HLD.
- Neo4j stays provisioned; backfill waits on new design + ADR if model changes.
- Mem0 remains vector source of truth for facts; graph is a projection (default
  assumption — confirm in redesign workshop).

## Backlog (parked work)

See **`docs/planning/BACKLOG.md`**. Parked: VPS `monitor.` enable; bulk CSV ingest;
Phase 3 premise test.

## Open blockers / risks

- **No graph visualization** until LifeGraph redesign lands + Neo4j seed.
- **`GET /memories` cap** — ~20 rows per list; use `external_id` search filter.
- **Mem0 `/metrics`** — not on server yet.

## Environment notes

- Windows PowerShell 5.1 (no `&&`); use `working_directory` for paths with spaces.
- Live env: `chandrav` @ `https://memory.chandrav.dev`.
- Neo4j Browser: `https://graph.chandrav.dev` (empty).

## Next action

> **RESUME HERE — LifeGraph redesign:**
> Read `docs/design/lifegraph.md` (legacy POC summary + open questions). Workshop
> HLD with operator: problem, scope, visualization, Mem0↔Neo4j sync, public
> boundary. Output: approved design doc §2–4, then ADR if needed, then TDD.

**How to talk to the next agent:** type **`/resume`** — or paste the handoff below.
