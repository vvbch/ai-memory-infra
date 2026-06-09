# ADR 029: Temporal tagging + open-item lifecycle (the todo-app foundation)

Date: 2026-06-09

## Status

Accepted. Builds on ADR 003 (soft separation), ADR 005 (Neo4j dual namespace /
LifeGraph), and ADR 028 (one `user_id`; `source` is the discriminator).

## Context

A memory bank without time is a pile, not a record. The operator wants the system
to reason about **when** things happened and to **follow up on what is still
open**:

- **Facts** and **decisions** must be timestamped, so the system can reason about
  recency, supersession ("which decision is current?"), and history.
- **Open items** (todos / follow-ups / "I need to check back on this") are a
  first-class kind of memory, not a fact. An open item has a lifecycle: it is
  raised, it is worked, and eventually **something happens** — it gets done,
  dropped, or superseded — and the system must **circle back and record what
  happened** rather than letting it rot silently.
- A **todo app** will be built on top of this memory layer. Per tenets 4 and 7 it
  must be a *thin client / projection* over the existing stores, not a second
  brain.

LifeGraph already anticipates the temporal half of this: ADR 005 defines
`:Decision`, `:Milestone`, `:Goal` nodes as "a temporal knowledge graph … with
timestamped edges." This ADR makes time and the open-item lifecycle explicit and
uniform across the whole bank.

## Decision

### 1. Every memory carries time

Two timestamps, kept distinct because capture time ≠ event time:

- **`created_at`** — when the memory was captured. Mem0 stamps this; we rely on
  it.
- **`occurred_at`** *(optional)* — when the fact/decision/event actually happened,
  carried in metadata when it differs from capture time (e.g. "decided last
  Tuesday", logged today). Absent ⇒ assume it equals `created_at`.

### 2. Every memory carries a `type`

A `type` metadata tag classifies the memory (alongside `source` from ADR 028 and
the venture categories from ADR 003):

- **`fact`** — durable knowledge (the default; Mem0's normal extraction output).
- **`decision`** — a choice made, timestamped; in LifeGraph a `:Decision` node
  (ADR 005). Supersession is an edge to the decision it replaces, so "what is the
  current decision on X?" is a graph query, not a guess.
- **`open_item`** — a todo / follow-up with a lifecycle (below).

### 3. Open items have an explicit lifecycle

An `open_item` carries:

- **`status`**: `open` → `in_progress` → (`done` | `dropped`).
- **`created_at`**, optional **`due_at`**, and optional **`revisit_at`** (when the
  system should check back).
- on closure: **`resolution`** (free text — *what happened*) and **`closed_at`**.

In LifeGraph an open item is an `:OpenItem` node carrying these temporal/status
properties, linked to the related entities, decisions, and ventures so follow-ups
keep their context.

### 4. The revisit loop — "check back what happened"

The system must close the loop, not just record it. A recurring pass (owned by
the **Operator Assistant** / **Memory Steward** personas, see
`docs/agent-personas.md`) queries open items whose `revisit_at`/`due_at` has
passed (or that are simply stale) and for each one either:

- records progress (update `status`/notes), or
- closes it with a `resolution` + `closed_at` ("what happened"), or
- re-schedules it (new `revisit_at`).

This is the mechanism that makes "for open items we need to check back what
happened" real, rather than relying on anyone remembering.

### 5. The todo app is a projection, not a store

The todo app is a **thin REST/MCP client** (tenets 4, 7) over `open_item`
memories + their `:OpenItem` LifeGraph nodes. It adds **no new datastore** — it
renders, filters, and updates open items that already live in the memory layer.
The memory bank stays the single durable asset (ADR 028); the app is a view.

## Consequences

- Time becomes queryable and uniform across facts, decisions, and todos; "what's
  current / what's overdue / what did I decide and when" are answerable.
- Open items can no longer silently rot — the revisit loop is an explicit,
  owned mechanism (tenet 14 spirit: a mechanism, not memory).
- The todo app inherits everything from ADR 028: one `user_id`, `source`-tagged,
  graph-visible — no silo.
- New moving parts are deferred, not free: the `:OpenItem` node type, the revisit
  pass, and the app are **backlog** (`docs/planning/BACKLOG.md`), not built here.
  This ADR fixes the model; implementation is tracked work.

## Notes

- `type`, `occurred_at`, `status`, `due_at`, `revisit_at`, `resolution`,
  `closed_at` are all **metadata on the single `user_id`** (ADR 028) — the same
  discrimination model as `source` and the venture categories (ADR 003).
- This does **not** turn the bank into a manually-synced store (tenet 10 caveat):
  facts still flow through Mem0's dedup/conflict pipeline. The lifecycle fields
  govern *open items*, which are intentionally authored/updated state.
