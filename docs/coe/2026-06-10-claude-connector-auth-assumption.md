# COE: Shipped bearer-token auth for a surface that only accepts OAuth

- **Date:** 2026-06-10
- **Author(s):** Build Agent (session with operator)
- **Severity:** low *(no data loss or exposure; one wasted operator step and one
  extra build session — the endpoint itself was correct and stays)*
- **Status:** closed
- **Related:** ADR 034 (remote MCP endpoint), ADR 035 (OAuth v2 — the fix),
  tenet 8 (verify in the right tier), AGENTS.md "web-verify volatile UI steps
  before prompting"

## Summary

ADR 034 chose a static bearer token as remote-MCP auth v1 and asserted
"Claude's connector UI and API both support `authorization_token`". That is
true for the **Messages API** MCP-connector path, but the **claude.ai custom
connector UI** (the surface the whole goal targets — iPhone inherits from
claude.ai web) only supports **OAuth (DCR/CIMD) or no auth**. The error
surfaced when the operator reached the registration step: there is no field to
paste a bearer token. Goal 2 close-out stalled; auth had to be rebuilt as
minimal self-hosted OAuth (ADR 035).

## Impact

- One operator round-trip wasted (registration attempt that could not succeed).
- One extra agent session to design/build OAuth; Goal 2 close-out delayed by a day.
- No security or data impact — the endpoint rejected unauthenticated traffic
  throughout.

## Timeline

- `2026-06-10 am` — ADR 034 written; auth v1 = static bearer, citing the
  Messages-API connector doc for `authorization_token` support.
- `2026-06-10 pm` — Endpoint built, deployed, live-verified with the token.
- `2026-06-10 pm` — **Operator detects the error** at claude.ai → Add custom
  connector: only Name/URL (+ optional OAuth client fields); no token field.
- `2026-06-10 pm` — Decision: build minimal self-hosted OAuth now (ADR 035).

## Detection

**Human catch (operator), at the final registration step.** The agent verified
the *endpoint* live (TLS, 401, tool round-trip) but never verified the
*registration surface* — the one step it cannot execute itself.

## Industry benchmark

- **Google SRE "test the rollback/last mile":** validating every step you own
  while leaving the only human-gated step unvalidated is a classic last-mile
  gap. Not met before; met by this COE's prevent action.
- **Amazon "working backwards":** starting from the registration UI (the
  customer-visible step) would have surfaced the OAuth requirement before any
  auth code was written.

## Root cause — 5 Whys

1. Why did registration fail? → claude.ai's custom-connector UI has no bearer
   token field; it only initiates OAuth or connects authless.
2. Why did the ADR assume a token field existed? → It generalized from the
   Messages-API connector doc (`authorization_token`) to all Claude surfaces.
3. Why was the wrong doc used? → Both docs are Anthropic MCP-connector docs;
   the surface distinction (API caller vs consumer UI) is easy to conflate and
   was not explicitly checked.
4. Why wasn't the actual UI surface verified before building auth? → The
   AGENTS.md rule "web-verify volatile UI steps before prompting" was applied
   only to the *operator instruction* step (planned for after the build), not
   to the *design assumption* the build depended on.
5. Why? → **Root cause (systemic):** the verification rule triggers on
   "writing click-by-click instructions", not on "an ADR whose viability
   depends on a third-party surface". Auth-model choice depended on a UI the
   agent never inspected; nothing forced that check at design time.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| ADR 035: replace bearer-only auth with minimal self-hosted OAuth 2.1 (DCR + PKCE) using the already-pinned `mcp` SDK auth framework | Mitigate | Build Agent | 2026-06-10 | done |
| When an ADR's viability depends on a third-party surface the agent cannot exercise (a registration UI, an approval flow), verify that surface's *current* requirements against its own doc page — not a sibling product's — **before** accepting the ADR; record the exact surface in Sources | Prevent | Build Agent (applied in ADR 035 Sources) | 2026-06-10 | done |

## Lessons learned

Live-verifying everything you can execute is not the same as verifying the one
step you can't. When a design's go/no-go lives in someone else's UI, check that
UI's own documentation (or the UI itself) at design time; "a nearby Anthropic
doc said so" is the same class of drift tenet 8 exists to prevent.
