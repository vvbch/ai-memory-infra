# ADR 037: Write-path idempotency & dedup contract

Date: 2026-06-10

## Status

Accepted.

## Context

While bulk-seeding portfolio facts through the OAuth MCP `add_memory` tool
(2026-06-10), two failures compounded:

1. **Timeout is a false negative.** The MCP client returned a read timeout, but
   Mem0's async extraction pipeline committed the write ~3s later server-side.
2. **Verify-and-retry created semantic duplicates.** The client treated the
   timeout as failure, re-verified too quickly against a not-yet-indexed store,
   then retried with *reworded* text. Rewording changed the content hash, so
   exact-hash dedup was bypassed; Mem0's LLM ADD/UPDATE near-neighbor check had
   nothing indexed to match against → ADD → three duplicate memories.

Root cause chain (five whys): client surfaced async-commit as failure → no
idempotency key on writes → reworded retry defeated hash dedup → write-time
semantic dedup blind to not-yet-indexed originals.

See COE `docs/coe/2026-06-10-mcp-timeout-semantic-duplicates.md`.

The MCP proxy exposed only `add_memory` / `list_memories` / `search_memories`, so
the incident could not be cleaned up in-session. `scripts/memory.py` already used
`PUT`/`DELETE` internally for open-item closure but did not expose delete as a
CLI or MCP tool.

## Decision

### 1. Deterministic external IDs on bulk / scripted writes

Any importer or scripted seed path must carry a caller-supplied
`metadata.external_id` (stable string, namespaced e.g. `portfolio:pgvector-blr1`).
Before write, check existence by `external_id`; if present, **skip** — never
reword and retry.

Implemented: `scripts/bulk_seed_importer.py`.

### 2. Timeout semantics — commit may succeed on timeout

`POST /memories` with `infer=True` is **async-commit**: the HTTP response may
arrive after extraction finishes, and a **client read timeout is not proof of
failure**.

Contract for all write clients (MCP, `scripts/memory.py`, extension, future
OpenClaw adapter):

- Use a write timeout ≥ 120s for extraction writes (configurable via
  `AI_MEMORY_WRITE_TIMEOUT`).
- On timeout: **verify-then-skip** — poll for `metadata.external_id` (or the
  original verbatim text hash for non-idempotent paths) for up to ~90s; if found,
  treat as success; if not found, surface `timeout_unverified` and stop — **never
  reword on retry**.

### 3. Dedup responsibilities — online vs offline

| Layer | Responsibility | Mechanism |
|---|---|---|
| **Write-time (online)** | Prevent ADD when a near-duplicate already exists *and is indexed* | Mem0 LLM ADD/UPDATE/DELETE pipeline during extraction |
| **Exact-hash** | Collapse identical verbatim replays | Content hash (bypassed if text is reworded) |
| **Offline compaction** | Find semantic near-dupes the online path missed (timing, wording drift, batch effects) | `scripts/memory_compaction.py` — cluster by search score, **human review first** |

**Vector store ≠ dedup.** pgvector stores embeddings for retrieval; dedup is the
LLM's write-time job plus an offline compaction pass — not implicit in the index.

Auto-merge from compaction is **review-gated** on the first production pass
(operator ruling 2026-06-10): some near-dupes (e.g. Neo4j 0-nodes/ADR-032 line vs
node-count line) are intentionally distinct facts.

### 4. MCP must expose delete and update

The MCP tool surface (local stdio + remote OAuth HTTP per ADR 034/035) must
include:

- `delete_memory(memory_id)`
- `update_memory(memory_id, text, metadata_json?)`

Parity in `scripts/memory.py`: `delete-memory`, `update-memory` subcommands.

### 5. Cross-cutting contract (ADR 031)

This ADR governs **every memory write consumer**:

| Consumer | `external_id` on bulk writes | timeout semantics | delete/update exposed | fact metadata contract |
|---|---|---|---|---|
| `scripts/bulk_seed_importer.py` | ✅ required | ✅ verify-then-skip | N/A (uses REST client) | ✅ required |
| `scripts/memory.py` | ✅ `--external-id` on `add-fact` | ✅ shared `idempotent_write` + env | ✅ CLI | ✅ `--event-date` etc. |
| MCP proxy (`src/mcp_proxy/server.py`) | ✅ optional param / metadata | ✅ shared client timeout | ✅ tools | ✅ optional fields |
| Chrome extension | future bulk path | extension HTTP client | via REST (no UI yet) | `namespace` default `public` |
| OpenClaw adapter | pending gate (ADR 028) | must adopt | must adopt | must adopt |

Shared implementation: `src/mcp_proxy/idempotent_write.py`, `src/memory/contract.py`,
`src/memory/retrieval.py`. Conformance extended in `scripts/check_memory_contract.py`.

### 6. Fact metadata contract (pre-bulk-load gate)

Every fact written through scripted/bulk/probe paths carries controlled metadata
(not buried in prose):

| Field | Rule |
|---|---|
| `event_date` | ISO `YYYY-MM-DD` — when the event actually happened (canonical; dual-write `occurred_at` for ADR 029 compat) |
| `source` | `cursor-repo` \| `chatgpt` \| `perplexity` \| `claude` \| `manual` \| `mcp` \| `extension` |
| `source_doc_id` | optional traceable origin (ADR path, chat id, URL slug) |
| `namespace` | flat tag on `user_id=chandrav`: `public` (default) \| `sensitive` |
| `external_id` | required on bulk/probe; recommended on `add-fact` |
| entity text | qualify colliding names inline (e.g. `Krishna, interview-prep contact`) |

Implemented: `src/memory/contract.py`, `scripts/bulk_seed_importer.py`,
`scripts/memory.py`, MCP `add_memory` optional fields.

### 7. Retrieval temporal contract

`/search` ranks by **embedding similarity**, not time. Read paths must:

1. Resolve "latest status of X" by **`max(event_date)`** among candidates — never
   `created_at` (write/capture time only).
2. Use metadata filters for structured queries (`type=open_item`, `status=open`,
   `namespace=public`) — pure vector search alone is insufficient for follow-ups.
3. For entity-collision queries, rerank scoped hits by inline-qualifier overlap
   (`src/memory/retrieval.py`: `best_entity_match`).

Acceptance gate: `scripts/acceptance_probe.py` (5-fact probe, 3 queries, cleanup).

### 8. Direct SQL access (deferred)

Mem0 stores JSON `metadata` in Postgres. **Writes and contract reads stay on the
Mem0 API** (option A). Optional read-only SQL views on
`metadata->>'event_date'`, `namespace`, `external_id` (option B) are deferred until
after bulk load; periodic export (option C) remains a fallback.

## Consequences

- Incident duplicates and verification markers removed 2026-06-10 via
  `delete_memory` (six ids).
- Metrics batch from the timed-out write **partially landed** at 15:49:01 UTC
  (build span, 17h, 36 ADRs/13 COEs/107 tests/94% coverage in one extracted
  fact); remaining metrics (18 tenets, 56 memories, ₹3,370, 24h RPO, restore
  drill, CI/CD, precision@5) were **not** found — use `bulk_seed_importer.py`
  with fresh `external_id`s, not manual MCP retries.
- Scheduled compaction: run `memory_compaction.py` weekly; review clusters before
  any merge. Operator runbook: `python scripts/memory_compaction.py --report …`;
  merge only with `--merge-from <report> --i-reviewed-clusters`.
- **2026-06-11:** 5-fact acceptance probe **PASS** (all three queries) —
  `docs/reports/acceptance-probe-2026-06-11.md`. Bulk fact load unblocked for a
  separate seed session.

## Related

- COE `docs/coe/2026-06-10-mcp-timeout-semantic-duplicates.md`
- ADR 028 (write metadata contract), ADR 031 (cross-cutting conformance), ADR 029
  (`infer=False` for authored items)
- Tenet 19 (vector store ≠ dedup; timeout ≠ failure), tenet 20 (event_date + namespace + inline entities)
- ADR 029 (`occurred_at` compat; `event_date` canonical per §6)
