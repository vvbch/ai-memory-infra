# ADR 028: One `user_id`; `source` is the discriminator (through Mem0 and graph)

Date: 2026-06-09

## Status

Accepted — **supersedes ADR 026** (OpenClaw writes must be source-tagged).

## Context

ADR 026 set a "hard rule" for OpenClaw writes: use the shared personal
`user_id="chandrav"` *only if* the adapter could pass `source` and `agent_id`
through to Mem0 and the graph; otherwise fall back to a **separate prototype
`user_id`**. The operator rejected this on review: identity is the wrong layer
to discriminate on, and the fallback fragments the one curated bank.

This was already settled once. **ADR 003 (soft separation over hard isolation)**
chose a single `user_id` with all memories pooled and discriminated by
*metadata* (venture categories), precisely so cross-domain recall works
naturally. Splitting `user_id` per source is exactly the "hard isolation" ADR 003
rejected — it would:

- break cross-source recall (the todo app, OpenClaw, the extension, and Cursor
  could no longer see each other's context for the same person),
- fragment the durable asset into per-tool silos, and
- contradict ADR 003 and the soft-separation model the whole system is built on.

`source` matters — it must stay filterable, editable, and removable — but that is
a **metadata** concern, not an **identity** concern.

## Decision

1. **One `user_id` for the person, always: `user_id="chandrav"`.** Every write
   from every source — OpenClaw, Cursor/VS Code, Claude, the Chrome extension,
   the future todo app, any future tool — uses the shared personal `user_id`.
   There is no per-source / per-prototype `user_id`. Identity is never the
   discriminator.

2. **`source` is the discriminator, and it is mandatory.** Every write carries a
   `source` tag (e.g. `source="openclaw"`, `source="cursor"`,
   `source="extension"`, `source="todo-app"`), plus `agent_id` where the writer
   has one. `source` extends the ADR 003 metadata model (alongside the venture
   categories), it does not replace it.

3. **`source` must reach the graph database, not just the vector store.** The
   same `source` (and `agent_id`) must propagate into Neo4j metadata on the Mem0
   graph nodes/edges, so a memory's origin is queryable in *both* stores. A tag
   that only lives in pgvector but not in the graph is an incomplete write.

4. **An adapter that cannot carry `source`/`agent_id` is a blocker to fix, not a
   license to fork `user_id`.** If `serenichron/openclaw-memory-mem0` (or any
   future writer) does not pass `source`/`agent_id` through to Mem0 *and* graph
   metadata, the corrective action is to **patch the adapter** so it does. The
   old escape hatch — "give it its own `user_id`" — is removed.

5. **No untagged writes.** A write with no `source` is the failure mode to
   prevent. Tag at the source, or fix the source.

## Consequences

- The curated bank stays unified: one person, one `user_id`, cross-source recall
  intact (ADR 003 upheld, not undermined).
- Prototype / disposable writes (OpenClaw today, others later) stay **filterable,
  editable, and removable by `source`** in *both* the vector store and the graph
  — the actual goal ADR 026 was reaching for, achieved at the right layer.
- The adapter-verification step from ADR 026 survives but its *consequence*
  changes: a non-conforming adapter blocks the integration until patched; it no
  longer triggers a `user_id` split.
- This is the foundation ADR 029 builds on: `type` (fact / decision / open_item),
  timestamps, and the open-item lifecycle are *also* metadata on this single
  `user_id`, discriminated the same way.

## Notes

- Initial OpenClaw scope is unchanged: email processing from Chandra's desk only;
  no LinkedIn crawling. ClawPack/fallback config remains prototype reasoning
  plumbing only; Mem0 extraction is unchanged.
- Verification one-liner (after adapter work): write a probe memory with
  `source="openclaw"`, then confirm the tag is present *both* via the REST
  `/search` result metadata and on the corresponding Neo4j node
  (`graph.chandrav.dev`).
