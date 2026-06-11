# Memory-bank snapshot — 2026-06-10 (Goal 3)

> Honest point-in-time report of the live Mem0 bank and Neo4j graph store.
> No personal memory content included — counts and metadata only.

## Mem0 (pgvector) — live at `https://memory.example.com`

| Metric | Value |
|---|---|
| Total memories | **56** |
| Date range | 2026-06-08 → 2026-06-10 (UTC) |
| Distinct `user_id` values | 5 |
| Avg memory text length | ~177 chars (min 87, max 379) |

### By `user_id` (top)

| `user_id` | Count | Notes |
|---|---|---|
| `chrome-extension-user` | 47 | Extension auto-capture (desktop) |
| `primary-user` | 3 | Primary user / MCP path |
| `diag-roundtrip-20260608` | 2 | Deploy verification |
| `diag-rebuild-20260608` | 2 | Image rebuild verification |
| `drill-canary` | 2 | Restore-drill canary |

### By `metadata.source`

| Source | Count |
|---|---|
| `(none / unset)` | 53 |
| `extension` | 2 |
| `mcp` | 1 |

**Honest read:** most memories predate or bypass the ADR 028 `source` tagging
contract — only 3 of 56 carry an explicit source. `category` and `agent_id` are
unset on all 56. This is expected technical debt, not a graph claim.

## Neo4j — live on droplet (`ai-memory-infra-neo4j-1`, healthy)

| Metric | Value |
|---|---|
| Node count (`MATCH (n) RETURN count(n)`) | **0** |
| Mem0-written graph edges | **0** |

**Honest read (ADR 032):** Neo4j is running and backed up but **not written to**
by the deployed Mem0 stack. There is no knowledge graph in production today —
only vector memories in PostgreSQL/pgvector. LifeGraph (Phase 6) is the planned
graph writer; the graph-source one-way-door decision remains open in BACKLOG P1.

## Coverage context (same day)

ADR 036 remote MCP is live and operator-verified on web + iPhone for Claude,
Perplexity, and ChatGPT. The `mcp` source count (1) will grow as tagged writes
land through the connector path.

## Method

- Mem0: `GET https://memory.example.com/memories` with admin API key (env var;
  not logged).
- Neo4j: `cypher-shell` on droplet via SSH (`MATCH (n) RETURN count(n)`).
