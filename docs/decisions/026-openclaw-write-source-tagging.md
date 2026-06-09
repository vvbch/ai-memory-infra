# ADR 026: OpenClaw writes must be source-tagged

Date: 2026-06-09

## Status

**Superseded by ADR 028.** The source-tagging requirement survives, but the
`user_id`-split fallback this ADR allowed is removed: there is now exactly one
`user_id="chandrav"`, and `source` is the discriminator (carried through Mem0 and
graph metadata). An adapter that cannot pass `source`/`agent_id` is a blocker to
fix, not a reason to fork `user_id`. See ADR 028 (and ADR 029 for temporal tags +
open-item lifecycle).

## Context

OpenClaw is being added as a prototype consumer of the memory layer for AI-proof projects:
first email processing from Chandra's desk, later expanded only if it proves useful. The
memory bank is the durable asset; OpenClaw is disposable prototype code.

OpenClaw should read the same curated personal memory context as Chandra's other agents,
but its writes must not land as indistinguishable curated facts.

## Decision

All OpenClaw agent writes use the shared personal `user_id` for Chandra's spaces:
`user_id="chandrav"`.

Every OpenClaw write must also carry `source="openclaw"` and its `agent_id` through the
Mem0 write path, and the same `source` must propagate to the graph database metadata.

Before enabling prototype writes, verify `serenichron/openclaw-memory-mem0` passes
`source` and `agent_id` through to Mem0 writes. If it does not, OpenClaw must use its own
prototype `user_id` instead. One of these isolation mechanisms is mandatory; prototype
noise must not land untagged in the shared bank.

## Notes

- Shared `user_id` lets OpenClaw read existing curated memories.
- `source="openclaw"` keeps prototype writes filterable, editable, and removable later.
- Initial OpenClaw scope is email processing only; no LinkedIn crawling.
- Prototype reasoning uses Neurometric ClawPack Advanced (`base_url:
  https://api.neurometric.ai/v1`, `model: neurometric/clawpack`) with the firm's frontier
  API key configured as OpenClaw `fallbacks`.
- ClawPack fronts OpenClaw's agent-loop reasoning only. Mem0 extraction remains unchanged.

## Consequences

- If OpenClaw is removed, its writes can be queried and cleaned by `source`.
- The curated memory bank remains protected while the prototype iterates.
- Adapter verification is a blocker for shared-user writes.
