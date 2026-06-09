# COE: Chrome extension never received the memory-identity decision (ADR 028 drift)

- **Date:** 2026-06-09
- **Author(s):** Cursor agent
- **Severity:** High *(blast radius: every memory written from the browser — the
  primary capture surface — was mis-identified and effectively untagged)*
- **Status:** closed
- **Related:** ADR 028 (one `user_id`, `source` is the discriminator), ADR 029,
  ADR 003 (soft separation), ADR 024 (extension fork); ADR 031 (systemic fix);
  Tenets 10, 14. Repos: `ai-memory-extension`, `ai-memory-infra`.

## Summary

ADR 028 (2026-06-09) settled that there is exactly **one** `user_id="chandrav"`
for every source and that `source` is a mandatory discriminator carried in
**metadata** so it reaches both pgvector and the Neo4j graph. The decision was
authored, ratified, and committed in the control-plane repo (`ai-memory-infra`)
— but it was **never propagated to the Chrome extension**, the client that
actually writes most browser memories. The extension still defaulted
`user_id="chrome-extension-user"` and sent `source="OPENMEMORY_CHROME_EXTENSION"`
as a **top-level** field that the self-hosted mem0 `/memories` contract silently
drops. So every extension write went to a *fragmented per-tool bank* under the
wrong id with **no source tag persisted anywhere** — the exact failure modes ADR
028 (and ADR 003 before it) exist to prevent.

## Impact

No data lost and no secret exposed, but the curated memory bank's integrity was
quietly compromised at its busiest write surface:

- **Identity fragmentation:** browser memories landed under
  `user_id="chrome-extension-user"`, a per-tool silo, instead of the single
  `chandrav` bank. Cross-source recall (Cursor / MCP / OpenClaw ↔ extension) was
  broken for everything captured via the browser. This is precisely the "hard
  isolation" ADR 003 rejected and ADR 028 re-banned.
- **Untagged writes:** because `source` was sent top-level (not in `metadata`),
  the self-hosted mem0 OSS `/memories` contract dropped it. The tag reached
  **neither** pgvector nor the graph — so those writes were not filterable,
  editable, or removable by `source`, violating ADR 028 §2–§3 and §5 ("no
  untagged writes").
- **Duration:** latent since the Phase-3 rewire (the fork carried the upstream
  defaults forward); active from ADR 028's acceptance (2026-06-09) until this
  fix the same day. The verification in earlier sessions was itself run against
  `user_id=chrome-extension-user`, so the "proof" reinforced the wrong id.

## Timeline

- `2026-06-08` — ADR 024: fork the extension, rewire transport/auth to the
  self-hosted server (`X-API-Key`, `memory.chandrav.dev`). Identity/source were
  out of that scope and left at the upstream defaults.
- `2026-06-09` — ADR 026 → superseded same day by ADR 028: one `user_id`,
  `source` is the discriminator into Mem0 **and** the graph. Committed in
  `ai-memory-infra` (`abd941e`) and logged in `ai-memory-infra-private`.
- `2026-06-09` — The decision was applied to infra-adjacent code reasoning only;
  `ai-memory-extension`'s latest commit predated ADR 028 and was never revisited.
- `2026-06-09` — **Operator catch:** "we decided user_id/identity for mem0 as
  chandrav — did we change the Chrome plugin? … you've been aggressive about
  infra and private repos but not the plugin repo — why?"
- `2026-06-09` — Investigated, confirmed both violations, fixed the extension and
  the same latent bug in the MCP proxy, added the systemic conformance gate
  (ADR 031), wrote this COE.

## Detection

Human catch by the operator — and a *second-order* one: the operator noticed not
just the defect but the **pattern** (the agent enforced commit/push discipline
aggressively on `ai-memory-infra`/`-private` while treating the extension as a
second-class repo). A human catching the meta-pattern is a strong detection-gap
signal: nothing mechanical verified that an accepted cross-cutting decision was
actually true in every repo it governs.

## Industry benchmark

- **AWS/Amazon COE:** blameless 5-Whys to a systemic cause with owned actions
  that prevent recurrence. This meets it: the root cause is a missing
  *cross-repo conformance gate*, fixed by mechanism (ADR 031), not by "remember
  to check the extension next time."
- **Google SRE postmortem:** actions must improve prevention/detection, not just
  narrate. We add both a Prevent control (DoD conformance row + ADR 031 checklist
  in every cross-cutting ADR) and a Detect control (a contract-conformance check
  that greps client repos for the canonical `user_id`/`source` constants).
- **Distributed-systems contract drift:** the canonical analog is an API/schema
  change shipped to the server but not to every client — "consumer-driven
  contract" testing exists precisely because a decision is not done until every
  consumer conforms. The memory write payload (`user_id` + `metadata.source`) is
  that contract here; the extension is a consumer that drifted.

## Root cause — 5 Whys

1. Why were browser memories mis-identified/untagged? → The extension used the
   upstream defaults (`chrome-extension-user`, top-level `OPENMEMORY_…` source),
   not the ADR 028 contract (`chandrav`, `metadata.source="extension"`).
2. Why did it still use the upstream defaults? → ADR 028 changed code reasoning
   in the control plane but no one changed the extension; the decision never
   propagated to that repo.
3. Why didn't it propagate? → "Done" for a decision (the DoD "major decision"
   row) means *ADR + interview log + STATUS updated* — it does **not** require
   verifying conformance in every client repo the decision governs.
4. Why was conformance never required? → The workspace model classifies
   `ai-memory-extension` as a secondary "data/support repo," and the enforcement
   mechanisms that *are* aggressive (the completion gate, repo-health) police
   commit/push **hygiene**, not **decision conformance**. So a decision can read
   "Accepted" while a sibling repo silently violates it.
5. Why is there no conformance mechanism? → **Root cause (systemic):** the
   project treats decisions as *documents* (write the ADR) rather than as
   *contracts that must hold across all consumers*. There was no gate — soft or
   hard — that fails when an accepted cross-cutting decision is untrue in any repo
   it governs. The asymmetry the operator noticed is the symptom: enforcement was
   pointed at the control-plane repo's git state, never at cross-repo conformance.

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| Extension: one canonical `user_id="chandrav"` (`DEFAULT_USER_ID`) + auto-heal legacy/empty ids; `SOURCE="extension"` carried in `metadata.source`; every write routed through `postMemory` / the normalizing background relay (single write path); one-time storage migration of stored legacy id | Mitigate + Prevent | Cursor agent | 2026-06-09 | Done |
| Fix the same latent default in the control plane: MCP proxy `client.py` `DEFAULT_USER_ID` → `chandrav` (+ test) | Mitigate | Cursor agent | 2026-06-09 | Done |
| **ADR 031** — cross-cutting decisions are contracts: every such ADR ships a "Propagation / conformance" checklist of affected client repos; the decision is not "done" until each is verified/patched | Prevent | Cursor agent | 2026-06-09 | Done |
| Add a DoD trigger row: a memory/data-contract decision (`user_id`, `source`, schema, auth) must be verified — and patched if needed — in **every** client repo (extension, MCP proxy, OpenClaw adapter, future todo app) before it is done | Prevent | Cursor agent | 2026-06-09 | Done |
| `scripts/check_memory_contract.py` — verifies each consumer repo's structural invariants (canonical constants + a single normalizing write path with no `fetch('/memories')` bypass), so future drift is caught by a check, not a human | Detect | Cursor agent | 2026-06-09 | Done |
| Re-verify post-deploy: write a probe from the extension, confirm `source="extension"` on the `/search` metadata **and** the Neo4j node, under `user_id="chandrav"` | Detect | Operator + agent | next browser session | Open |

## Lessons learned

**A decision is a contract across every consumer, not a document in one repo.**
The control plane can be immaculate — ADR written, STATUS updated, commits pushed
— while the decision is simply *false* in a sibling repo that no mechanism was
watching. Enforcement that only polices the control-plane repo's git hygiene
creates exactly the blind spot the operator named: aggressive on
`ai-memory-infra`, absent on `ai-memory-extension`. The fix mirrors the
completion-gate lesson (COE 2026-06-09-model-dependent-completion-gate): move the
guarantee from "remember to" onto a mechanism — here, a conformance gate that
treats a cross-cutting decision as undone until it holds in **every** repo it
governs (consumer-driven contract thinking). Interview-worthy; mirrored to
`interview_packet.md`.
