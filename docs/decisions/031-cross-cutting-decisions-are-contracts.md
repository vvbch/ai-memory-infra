# ADR 031: A cross-cutting decision is a contract across every consumer repo (conformance gate)

Date: 2026-06-09

## Status

Accepted.

## Context

ADR 028 (one `user_id="chandrav"`; `source` is the discriminator carried in
`metadata` so it reaches both pgvector and the Neo4j graph) was authored,
ratified, and committed in `ai-memory-infra` — and then was simply **false** in
the repo that writes most browser memories. The Chrome extension
(`ai-memory-extension`) kept the upstream-fork defaults (`user_id=
"chrome-extension-user"`, a top-level `source="OPENMEMORY_CHROME_EXTENSION"`
that the self-hosted mem0 `/memories` contract silently drops), and the MCP
proxy (`src/mcp_proxy/client.py`) carried the same legacy `DEFAULT_USER_ID`.
See COE `docs/coe/2026-06-09-extension-memory-identity-drift.md`.

The root cause was systemic, not local: the project treated a decision as a
**document** (write the ADR, update STATUS, commit it) rather than as a
**contract that must hold in every repo it governs**. Our aggressive
enforcement — the completion gate (ADR 027/030), repo-health, gitleaks —
polices the control-plane repo's *git hygiene* (committed, pushed, no secrets),
never *cross-repo decision conformance*. So an ADR could read "Accepted" while a
sibling consumer silently violated it, and nothing mechanical noticed. The
operator did: "you've been aggressive about infra and the private repo but not
the plugin repo — why?" That asymmetry is the symptom of this gap.

This is the classic distributed-systems failure of **contract drift**: a
server/schema change shipped without updating every client. Consumer-driven
contract testing exists precisely because a change is not done until every
consumer conforms. Our memory write payload (`user_id` + `metadata.source`,
later `type`/timestamps per ADR 029) is exactly such a contract, and the
extension/proxy/OpenClaw adapter/todo app are its consumers.

## Decision

A **cross-cutting decision is a contract, not a document.** It is not "done"
until it is verified — and patched where needed — in **every consumer repo it
governs**, enforced by both a soft (process) and a hard (mechanical) control.

1. **Every cross-cutting ADR ships a "Propagation / conformance" section.** Any
   ADR that changes a contract shared across repos — memory write shape
   (`user_id`, `source`, `type`, timestamps), auth/transport scheme, schema, or
   any other client-server agreement — must list the affected consumer repos and
   the verification status of each (✅ conforms / 🔧 patched here / ⬜ pending).
   The decision is not Accepted-and-done while any consumer is ⬜.

2. **Consumers of the memory write contract, enumerated.** Today:
   `ai-memory-extension` (browser), `ai-memory-infra` MCP proxy
   (`src/mcp_proxy/client.py`), the OpenClaw adapter
   (`serenichron/openclaw-memory-mem0`), and the future todo app. New writers are
   added here when introduced. "Every consumer" means this list.

3. **A canonical-constants source of truth + a detect gate.** Each consumer
   defines the contract constants once (`DEFAULT_USER_ID="chandrav"`,
   `SOURCE`/source-in-`metadata`, the legacy values being migrated *away* from)
   and routes writes through a single normalizing chokepoint. `scripts/
   check_memory_contract.py` greps the consumer repos and **fails** if a stray
   legacy `user_id` or a top-level `source` survives outside the
   migration/normalization path — so future drift is caught by a check, not by a
   human noticing months later.

4. **DoD trigger row.** A memory/data-contract decision (`user_id`, `source`,
   schema, auth) is added to the AGENTS.md Definition-of-Done table: it must be
   verified — and patched if needed — in **every** consumer repo before it is
   done. The completion gate already forces commit/push of every touched repo;
   this adds the missing *conformance* dimension on top of *hygiene*.

## Consequences

- Closes the asymmetry the operator named: enforcement now points at cross-repo
  conformance, not only at the control-plane repo's git state. A decision that is
  true in `ai-memory-infra` but false in `ai-memory-extension` now fails a gate
  instead of passing silently.
- Mechanism over memory (tenet 14): the guarantee moves from "remember to check
  the extension" onto an ADR section + a DoD row + `check_memory_contract.py`.
- Small ongoing cost: cross-cutting ADRs carry one extra section; the check must
  learn about each new consumer repo. Both are bounded and intentional.
- Reversible (tenet 12): it is process + one script; delete the script and the
  row to back it out. No new vendor or dependency.

## Propagation / conformance (this decision and ADR 028)

| Consumer repo | Contract point | Status |
|---|---|---|
| `ai-memory-extension` | `user_id="chandrav"`, `metadata.source="extension"`, single write path (`postMemory` + background relay `normalizeMemoryWriteBody`), legacy id/source auto-healed | ✅ patched + committed |
| `ai-memory-infra` MCP proxy (`src/mcp_proxy/client.py`) | `DEFAULT_USER_ID="chandrav"` (overridable via `AI_MEMORY_USER_ID`) | ✅ patched + committed |
| OpenClaw adapter (`serenichron/openclaw-memory-mem0`) | pass `source`/`agent_id` into Mem0 **and** graph; patch adapter, never fork `user_id` (ADR 028 §4) | ⬜ pending — tracked in BACKLOG P2 (memory model) |
| Future todo app | reads/writes the same `user_id` + `source`/`type` contract | ⬜ N/A until built (ADR 029) |

## Notes

- Pairs with the completion gate (ADR 027/030): that gate guarantees *hygiene*
  (every touched repo committed + pushed); this ADR guarantees *conformance*
  (every consumer repo actually upholds the contract). Both are needed; neither
  substitutes for the other.
- Verification one-liner (post-deploy, ADR 028): write a probe from the
  extension, confirm `source="extension"` on the `/search` result metadata **and**
  on the corresponding Neo4j node, under `user_id="chandrav"`.
