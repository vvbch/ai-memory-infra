# Skill: Operator Assistant — Memory Daily Driver (conversational operating practice)

> Phase 2 of Memory Daily Driver v0 (STATUS "Next action", direction pivot
> 2026-06-09). Unlike the previous skills this is **not a new script** — the
> mechanism (`scripts/memory.py`, Phase 1) already exists and is live-proven.
> This skill is the **operating practice** that wires it into conversation, so
> the agent reads/writes the memory bank when Chandra talks to it.

**Implementation:** `scripts/memory.py` (Phase 1 helper, unit-tested + live-proven)
**Owner persona:** Operator Assistant (`docs/agent-personas.md`)
**Canonical practice text:** `AGENTS.md` § "Memory Daily Driver — conversational practice"
(this spec explains; AGENTS.md governs)

## What pain it removes

The memory layer is live but unused — the product premise (*does self-hosted
memory make my AI tools better?*) stays untested while open items live in
Chandra's head. After this skill, saying *"plan my day"* or *"log this, follow
up Friday"* in a normal chat is enough: the agent runs the contract-enforcing
helper and the bank does the remembering.

## Trigger table (operator phrase → agent action)

| Chandra says (any phrasing like…) | Agent runs | Then says |
|---|---|---|
| "plan my day" / "what's on my plate?" / "what's overdue?" | `python scripts/memory.py agenda` | The buckets in plain English (overdue first), ending with one recommended next action |
| "log this…" / "todo: …" / "remind me…" / "follow up &lt;day&gt;" | `python scripts/memory.py add-open-item "<verbatim text>" [--due YYYY-MM-DD] [--revisit YYYY-MM-DD] [--venture <tag>]` | Confirmation: stored text, type, dates, ventures, short id |
| "recruiter X reached out…" / "track this reachout" | `add-open-item … --venture career` (+ due/revisit from phrasing) | Same confirmation |
| "show recruiters" / "recruiter board" | `python scripts/memory.py recruiters` | The board, soonest follow-up first |
| "we decided X (because Y)" | `python scripts/memory.py add-decision "<decision + reason>" [--occurred YYYY-MM-DD] [--venture <tag>]` | Confirmation incl. occurred date |
| "we're reversing X / changed our mind (because Z)" | **Supersession flow** (below) | Confirmation: new decision stored + which old decision it supersedes |
| "done" / "that happened: …" / "drop it" | `python scripts/memory.py close <id> --resolution "<what happened>" [--status dropped]` | Confirmation: closed, with resolution |
| "remember that &lt;fact&gt;" | `python scripts/memory.py add-fact "<fact>" [--venture <tag>]` | Confirmation |

Date phrases resolve against today's date ("Friday" → next Friday's ISO date,
"tomorrow" → today+1); the agent states the resolved date in the confirmation so
a wrong guess is visible immediately.

## Supersession flow (decision reversed later, possibly in another tool)

ADR 029 §2: supersession is ultimately a LifeGraph edge; at v0 it is a **text +
timestamp convention** that any client (Cursor, ChatGPT via extension, Claude)
can produce and any search can read:

1. **Find the prior decision** — `search`/list for `type=decision` on the topic.
2. **Capture the reversal as a new decision** (never edit the old text):
   `add-decision "Supersedes <old-short-id> ('<old gist>'): <new decision>. Reason: <why>." --occurred <date>`
3. The old decision **stays in the bank** (the trail is the point); "what's
   current on X?" = the latest non-superseded decision by `occurred_at`/`created_at`.

This keeps both the **history** (every decision verbatim, dated, with reasons)
and the **current snapshot** (latest decision wins), independent of which chat
surface captured each step. The Mem0 history table additionally records every
ADD/UPDATE/DELETE with old/new values as a server-side audit trail.

## Confirmation contract (non-negotiable)

Every write is followed by a plain-English confirmation of **exactly what was
stored**: verbatim text, type, status, resolved dates, ventures, short id. A
silent write is a contract violation — Chandra must always be able to catch a
mis-tag or wrong date in the same breath.

## Store / retrieve boundary

| | |
|---|---|
| **May write** | `open_item` / `decision` / `fact` memories under `user_id="chandrav"`, `source=cursor`, validated ventures/dates (the helper enforces this) |
| **Must never write** | secrets, API keys, vault values; multi-paragraph transcript dumps (capture the item, not the chat); unverified hypotheses as facts |
| **Canonical truth** | repo files (STATUS/ADRs) for project state — the bank holds *personal operating* items; if memory and repo disagree, repo wins (Memory Steward rule) |

## Success condition

In a fresh session, "plan my day" returns the real agenda (proven: read-only
`agenda` runs green against the live bank), and a "log this / follow up
&lt;date&gt;" round-trips: captured → visible in the next `agenda` under the right
bucket → closeable with a resolution. Phase 3 (the premise test) exercises this
with Chandra's real items.

## Deliberately not built (tenet 7 / BACKLOG)

- MCP-tool exposure of these verbs in `src/mcp_proxy/server.py` (the shell path
  works in every surface that can run Python; add MCP verbs when a surface needs them).
- Server-side date-range filters, recurring revisit cron, todo UI, LifeGraph
  `:Decision`/`:OpenItem` nodes — all tracked in `docs/planning/BACKLOG.md`.
