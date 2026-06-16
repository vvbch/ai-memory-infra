# Design Doc — LifeGraph (redesign from scratch)

> **Status:** `draft` — **replaces** the in-memory Phase 6 POC in `src/life_graph/`
> as the canonical design target. Do not extend the POC until this doc is approved.
>
> **Why redesign:** the POC proved schema + query patterns in tests but never
> connected to Neo4j, Mem0, or a visualization surface. Operator asked to rethink
> from first principles (2026-06-16).

## 0. Metadata

- **Scope:** LifeGraph — temporal knowledge graph over professional life
- **Status:** `draft`
- **Author / date:** operator + agent / 2026-06-16
- **Related ADRs:** 005 (original intent), 032 (Neo4j provisioned, empty),
  029 (decision supersession), 038 (public POC vs private ventures)
- **Related interfaces:** `docs/interfaces.md` §1 (`metadata.source`, ventures)

## 1. What LifeGraph was (legacy POC — do not copy blindly)

**Intent (ADR 005):** a **public, interview-safe** graph layered on the same Neo4j
instance as the platform — distinct from Mem0's vector memories and from private
firm graphs (trading, RIA, etc.).

**Legacy node labels:** `Person`, `Venture`, `Skill`, `Decision`, `Milestone`,
`Goal`, `Tool`.

**Legacy relationships:** `CO_FOUNDER`, `WORKS_ON`, `HAS_SKILL`, `DECIDED`,
`ACHIEVED`, `TARGETS`, `USES`, `RELATED_TO`.

**What shipped in code (`src/life_graph/`):**

- In-memory `GraphStore` only — **no Neo4j driver**, no live seed on VPS.
- Synthetic seed (`seed.py`) with fake people/ventures for tests.
- Ingest/queries/cli stubs — not wired to Mem0 bank or `graph.` UI.

**What exists in infra today:**

- Neo4j container **running + backed up**; **0 nodes** (ADR 032).
- `https://graph.{domain}` → Neo4j Browser (empty canvas).
- **249 ADR facts** live in Mem0/pgvector — **not** in the graph.

**Gap the redesign must close:** *visualizable, queryable graph* that relates to
the memory bank without duplicating firm IP in the public repo.

## 2. Problem & scope (redesign — fill in next session)

- **What problem does this solve?** _(TBD — operator input)_
- **In scope:** _(TBD)_
- **Out of scope / parked:** Mem0 auto-graph; private venture graphs; full todo UI
- **Success criteria:** _(TBD — e.g. seed from public fixtures, browse in Neo4j
  Browser, cross-query with memory `external_id` / `source`)_

## 3. Open questions (start here)

1. **Source of truth:** Mem0 facts → graph projection, or graph-first with memory
   as narrative layer?
2. **Visualization:** Neo4j Browser only, Grafana, custom UI, or MCP tools?
3. **Temporal model:** decision supersession as edges, node versions, or both?
4. **Public boundary:** which entities stay synthetic/generic in the public repo?
5. **Sync cadence:** batch seed, event-driven on write, or manual operator job?

## 4. Next step

Workshop HLD (§2–3 of `docs/design/TEMPLATE.md`) in a fresh session — then ADR
if Neo4j usage model changes, then TDD against the new contracts.
