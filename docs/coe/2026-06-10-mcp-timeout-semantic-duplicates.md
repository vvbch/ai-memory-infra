# COE: MCP bulk-write timeout surfaced false failure → semantic duplicates

- **Date:** 2026-06-10
- **Author(s):** Cursor agent (incident reported by operator)
- **Severity:** Medium *(data integrity: three duplicate facts + three verification
  markers; no secret exposure; originals preserved)*
- **Status:** closed
- **Related:** ADR 037 (write-path idempotency & dedup contract), ADR 028/031,
  Tenet 19; COE index #14.

## Summary

While bulk-writing portfolio facts through the OAuth MCP `add_memory` tool, the
client timed out on several writes. The agent treated timeouts as failures,
re-verified too quickly against a not-yet-indexed store, then retried with
reworded text — creating three semantic duplicates of facts that had already
committed server-side ~3s after the timeout. Six ids were deleted on cleanup
(three dupes + three verification markers); four originals confirmed intact.

## Impact

- **Duplicates created:** three reworded retries bypassed hash dedup and Mem0's
  ADD/UPDATE neighbor check (originals not yet indexed):
  - `e4249f1f` dup of `48e2097a` (pgvector/BLR1)
  - `b1961936` dup of `aef44e07` (gpt-5-mini / embeddings)
  - `a1ed5622` dup of `cd6ffc57` + `80b5a5df` (LifeGraph / Neo4j reserved)
- **Noise:** three goal2 verification markers left in the bank.
- **Operational:** MCP lacked `delete_memory` / `update_memory` — cleanup could
  not happen in the connector session.
- **Metrics batch:** partially committed at 15:49:01 UTC (build span, ~17h,
  36 ADRs/13 COEs/107 tests/94% coverage); remaining metrics (18 tenets, 56
  memories, ₹3,370, 24h RPO, restore drill, CI/CD, precision@5) **not** found —
  must not be blindly re-added via reworded MCP retries.

## Timeline

- `2026-06-10 ~15:49 UTC` — Batch 1 portfolio facts sent via MCP; client timeout
  on some calls; server committed extracted facts at `15:49:57` (8 facts incl.
  endpoint URLs and ADR refs).
- `2026-06-10 ~15:50 UTC` — Agent verified too early (store looked empty),
  retried with reworded text → duplicates at `15:50:18`–`15:50:45`.
- `2026-06-10` — Operator diagnosed false-negative timeout + duplicate chain;
  specified corrective actions and review-gated compaction policy.
- `2026-06-10` — ADR 037, `delete_memory`/`update_memory` on MCP + CLI, bulk
  importer, compaction job; six ids deleted; originals verified.

## Detection

Human catch by the operator during bulk-seed session — including post-hoc pgvector
timestamp proof that the "failed" batch had landed.

## Industry benchmark

- **AWS/Amazon COE:** blameless 5-Whys to systemic cause with owned preventive
  actions. Meets bar: root cause is missing idempotency + wrong timeout semantics,
  not operator error.
- **Google SRE:** actions must change behavior. Meets bar: ADR 037 contract,
  importer with verify-then-skip, MCP delete/update, offline compaction with
  mandatory first-pass human review.
- **Gap:** no automated alert on duplicate-rate spike yet — parked as P2 in
  BACKLOG (compaction schedule + eval dedup metric).

## Root cause — 5 Whys

1. Why three duplicate memories? → Agent retried with reworded text after
   perceived failure.
2. Why did it retry? → MCP client returned read timeout; agent classified timeout
   as hard failure.
3. Why did reworded retry create dupes? → Rewording changed hash (bypassed
   exact-hash dedup) and originals were not yet indexed for Mem0's ADD/UPDATE
   neighbor check.
4. Why no idempotency guard? → Bulk writes had no `external_id`; MCP exposed
   only add/list/search — no delete to recover in-session.
5. Why was timeout trusted as failure? → **Root cause (systemic):** no documented
   async-commit contract for Mem0 extraction writes; clients default to 30s timeout
   and treat it as failure signal.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| ADR 037: idempotency, timeout, dedup split, MCP delete/update | Prevent | infra | 2026-06-10 | Done |
| `scripts/bulk_seed_importer.py` (external_id, verify-then-skip) | Prevent | infra | 2026-06-10 | Done |
| `scripts/memory_compaction.py` (review-first clustering) | Detect | infra | 2026-06-10 | Done |
| Expose `delete_memory` / `update_memory` on MCP + `memory.py` CLI | Mitigate | infra | 2026-06-10 | Done |
| Delete 6 incident ids; verify 4 originals | Mitigate | agent | 2026-06-10 | Done |
| Tenet 19 + interview_packet lesson | Prevent | infra | 2026-06-10 | Done |
| Schedule weekly compaction review | Detect | operator | post-burn-in | Parked (BACKLOG) |
| Conflict-question answers + sensitive-cluster namespace ruling before merge | Prevent | operator+agent | TBD | **Blocked — operator input required** |

## Lessons learned

- **Vector store ≠ dedup** — pgvector is retrieval; dedup is Mem0 write-time LLM
  logic plus offline compaction.
- **Never reword on retry** — use deterministic `external_id` and verify-then-skip.
- **Timeout ≠ failure** on `infer=True` writes — commit may land seconds later.
- **First compaction pass is review-only** — batch-1 vs batch-2 Neo4j facts may
  be near-dupes worth keeping distinct; auto-merge would silently drop nuance.

Mirror: `interview_packet.md` (session append). Follow-ups: `BACKLOG.md`.
