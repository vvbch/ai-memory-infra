# ADR 032: Neo4j is reserved for LifeGraph, not a live Mem0 graph (HLD drift correction)

**Status:** Accepted
**Date:** 2026-06-10
**Deciders:** the operator (+ agent)
**Corrects:** ADR 005 (premise #1 only). **Ties:** tenet 8 (verify at source),
tenet 10 (no drift), COE 2026-06-10-delayed-memory-buildout (action: "correct the
Neo4j dual-namespace claim").

### Context

The architecture docs described Neo4j as a live **"dual namespace: Mem0
auto-managed graph + LifeGraph"** (ADR 005, `architecture.md`, `AGENTS.md`,
`README.md`, compose + Dockerfile comments). A source review found this overstates
reality.

**Source-verified finding** (tenet 8 — repo source beats a live snapshot):

- At our pinned upstream ref (`MEM0_REF=3669459…`), the mem0 `server/` REST app
  **never reads `NEO4J_*`** and **configures no `graph_store`**.
- The `mem0ai` 2.0.4 wheel ships **zero** graph-memory code; there is no `graph`
  extra, so `pip install "mem0ai[graph]"` in `infra/mem0-server.Dockerfile`
  resolves to plain `mem0ai` (with a warning).
- Therefore the compose `NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD` env vars
  passed into the mem0 container are **inert/dead config**, and **nothing writes
  Neo4j today**.

So Neo4j is running, healthy, and backed up, but it is **reserved future capacity
for LifeGraph** (ADR 005 namespace #2 — people/ventures/skills/decisions/
milestones), which is **Phase 6 and not yet built**. ADR 005's namespace #1 (a
Mem0 auto-managed graph in the same instance) does not hold for the deployed stack.

### Decision

1. **Correct the drift everywhere it appears** to: "Neo4j — provisioned, healthy,
   backed up, but not yet written; reserved for LifeGraph (Phase 6)." Done this
   session in `docs/architecture.md` (diagram node + edge + a status note),
   `AGENTS.md` architecture summary, `README.md`, `scaffold.py`'s README template,
   `infra/docker-compose.yml` comment, and `infra/mem0-server.Dockerfile` comment;
   ADR 005 carries a correction note pointing here.
2. **Keep Neo4j deployed + backed up.** It is cheap reserved capacity on the
   single droplet and avoids a re-provision when Phase 6 lands (tenet 7 trade-off
   accepted deliberately, not by accident).
3. **Keep the inert graph extras in the Dockerfile** as forward-leaning
   scaffolding (clearly commented as inert), rather than removing deps now — a
   reversible call; the removal-vs-keep is folded into the graph-source decision
   below.
4. **Defer the graph-source decision** — LifeGraph-only (current plan) vs. adopting
   a graph-capable Mem0 build/version — to a one-way-door operator call **before
   Phase 6** (it gates ADR 005's cross-namespace promise). Not decided here.
5. **Reaffirm tenet 8 as a pre-doc gate:** verify product/API capabilities at
   source before baking them into docs. This drift existed because an upstream
   capability was assumed, not checked.

### Propagation / conformance

Drift sites corrected (grep `dual.?namespace|auto-managed graph|Mem0 graph` returns
only historical/ADR-title references after this change):
`docs/architecture.md`, `AGENTS.md`, `README.md`, `scaffold.py`,
`infra/docker-compose.yml`, `infra/mem0-server.Dockerfile`, `docs/decisions/005-…`
(correction note), `docs/planning/setup-prompt.md` (historical-snapshot banner).

### Consequences

- **Positive:** Docs match reality; no false "graph memory" capability claim in a
  portfolio repo; the real graph work (LifeGraph) is correctly scoped to Phase 6.
- **Negative:** Neo4j + its backup run with no current writes (small, deliberate
  idle cost; revisit at Phase 6 / steady-state downsizing).
- **Live droplet confirm (2026-06-11):** `MATCH (n) RETURN count(n)` → **0** via
  `scripts/verify_source_propagation.py` (before and after a tagged Mem0 write).
  No Mem0-written nodes; belt-and-suspenders item closed.
