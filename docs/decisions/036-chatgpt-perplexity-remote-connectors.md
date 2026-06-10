# ADR 036: ChatGPT and Perplexity remote memory connectors reuse the ADR 035 endpoint

**Status:** Accepted
**Date:** 2026-06-10
**Deciders:** Chandra (operator direction 2026-06-10 evening: "similar remote
integrations for Perplexity and ChatGPT")
**Extends:** ADR 034 (endpoint), ADR 035 (self-hosted OAuth 2.1). Neither is
superseded; this ADR adds two client platforms to the same server.

## Context

Goal 2 closed with claude.ai connected to `https://mcp.chandrav.dev/` via
self-hosted OAuth 2.1 (ADR 035). The operator's next direction is the same
class of native remote integration for **ChatGPT** and **Perplexity**. Today
ChatGPT is covered only by the Chrome extension on desktop; Perplexity has
nothing.

Per COE 2026-06-10-claude-connector-auth-assumption, each platform's
**registration surface's own docs** were web-verified before this design
(all fetched 2026-06-10; sources at the bottom).

### What ChatGPT supports (OpenAI's own docs)

- **Custom remote MCP servers are supported** as "apps" (renamed from
  "connectors" on 2025-12-17), added via **Settings → Apps & Connectors**.
- Two integration shapes:
  - **Data-only app** (chat, deep research, company knowledge): requires the
    server to expose `search` / `fetch` tools in OpenAI's compatibility shape.
    Our server's tools (`search_memories`, `add_memory`, `list_memories`) do
    **not** match that shape.
  - **Developer mode** (beta): full MCP client, **all tools read/write, no
    `search`/`fetch` requirement**. Enabled at Settings → Apps → Advanced
    settings → Developer mode. This is our path.
- **Eligibility:** Pro, Plus, Business, Enterprise, Education — **on the web**
  (registration is web-only; third-party guides report apps enabled on web are
  then usable in the mobile app — verify live at registration, not guaranteed
  by OpenAI's docs).
- **Transport:** SSE and Streamable HTTP — ours (Streamable HTTP) is fine.
- **Auth:** OAuth, No Authentication, or Mixed. **No static token / API key.**
  For OAuth, ChatGPT prefers CIMD (Client ID Metadata Documents) when the AS
  advertises it, and **supports DCR when configured**. Our ADR 035 server does
  standard OAuth 2.1 + RFC 7591 DCR + PKCE S256 + RFC 9728/8414 discovery —
  the same protocol surface claude.ai consumed.

### What Perplexity supports (Perplexity's own help center + changelog)

- **Custom remote MCP connectors shipped 2026-03-13** ("Bring Your Own
  Connector"): **Pro, Max, and Enterprise** plans.
- Added via **Account settings → Connectors → + Custom connector → Remote**:
  Name, MCP Server URL (**HTTPS required**), optional Description,
  **Authentication = OAuth 2.0 / API Key / None**, **Transport = Streamable
  HTTP or SSE**, optional icon (≤128 KB).
- **OAuth 2.0:** client ID/secret only needed "if the MCP server does not
  support dynamic client registration" — i.e. **DCR is supported**; with DCR
  no manual client credentials are required. OAuth callback:
  `https://www.perplexity.ai/rest/connections/oauth_callback`.
- Surfaces: registered in web account settings; third-party setup guides
  report the connector then works across web/iOS/Android/desktop clients
  (account-scoped tokens) — verify live at registration.

## Decision

### 1. One server, three platforms — no new endpoint, no new auth code

Both platforms register against the **existing** `https://mcp.chandrav.dev/`
endpoint with the **existing** ADR 035 OAuth 2.1 AS+RS. DCR means each
platform self-registers its client and redirect URI; PKCE S256 and the consent
page work unchanged. Expected build delta is **near zero server code**:

- **Consent-page copy generalization** (cosmetic): the page currently says
  "Approve Claude connector access" — generalize to name the requesting
  client. Same consent password (`MCP_CONNECTOR_BEARER_TOKEN`), same one
  secret class.
- **No transport change** (both accept Streamable HTTP), **no tool change**
  (developer mode lifts ChatGPT's `search`/`fetch` shape requirement), **no
  client allowlist change** (DCR is open by design; tokens still gated by
  consent — ADR 035 §2).

### 2. ChatGPT path = developer-mode custom app (web registration)

Register as a custom app with Authentication = OAuth under developer mode.
The Chrome extension contract for ChatGPT **stays** — the two coexist and
complement: the extension auto-captures/injects in the browser; the connector
gives ChatGPT on-demand memory tools natively (and plausibly on mobile, to be
verified). Nothing falls back; this is additive.

### 3. Perplexity path = custom remote connector (web registration)

Register with Authentication = OAuth 2.0, Transport = Streamable HTTP.
This is Perplexity's **first** memory surface (the extension supports
perplexity.ai pages, but Perplexity was previously listed as uncovered in
architecture.md's surface table — the connector becomes its primary coverage).

### 4. Plan-tier gate (operator fact, unresolved at ADR time)

- ChatGPT custom apps require **Plus or above**.
- Perplexity custom connectors require **Pro or above**.

The operator's current plan tiers are not on record. **If either account is on
a free tier, that platform's integration is blocked on a paid subscription —
a tenet 12/15 spend decision the operator makes explicitly**, documented in
architecture.md as "not covered (plan gate)" if declined. No new vendor either
way (both would be existing accounts upgraded).

### 5. Honest-coverage rule

architecture.md's coverage table is updated **only after live verification**
on each platform (rehearsal: connector registered → OAuth consent → a real
`search_memories` round-trip returns memories), mirroring the Goal 2 closeout
discipline. Until then the row stays at today's truth.

**Rejected alternatives:**

| Option | Why not |
|---|---|
| Data-only ChatGPT app (`search`/`fetch` shape) | Requires reshaping our tool surface to OpenAI's compatibility contract; developer mode needs no server change (tenet 7). Revisit only if developer-mode beta access is unavailable on the operator's plan |
| Static API-key auth on Perplexity | Works there, but ChatGPT rejects static tokens, and ADR 035 OAuth already exists — one auth story for all three platforms beats a per-platform split (tenet 10) |
| CIMD for ChatGPT | Optional optimization; DCR is supported and already proven with claude.ai. Add CIMD only if registration fails on DCR |
| Separate endpoints per platform | More moving parts, zero benefit — the protocol is standard (tenet 7) |

## Propagation / conformance

| Consumer | Action |
|---|---|
| `src/mcp_proxy/oauth.py` | Generalize consent-page copy (cosmetic; only code change expected) |
| `docs/interfaces.md` §13 | Note ChatGPT + Perplexity as additional OAuth clients of the same contract |
| `docs/architecture.md` | Coverage rows for ChatGPT (native connector) and Perplexity — **only after live verification** (§5) |
| `docs/setup.md` | Registration walkthroughs for both platforms (after live verification) |
| `ai-memory-extension` | **No change** — extension contract stands; coexists on ChatGPT |
| Local stdio proxy / OpenClaw adapter | **No change** |

## Consequences

**Positive:** two more surfaces from the same server and the same secret
class; validates ADR 035's "standard OAuth, not Claude-specific" design;
near-zero new code to own.

**Negative / risks:** developer mode is a **beta** OpenAI can change or gate
(mitigation: extension already covers ChatGPT desktop; coverage table stays
honest); mobile availability on both platforms is third-party-reported only
until verified live; possible paid-tier spend gate (§4, operator decision);
two more platforms hold refresh tokens to the memory bank (same revocation
lever as ADR 035: delete the OAuth state file or rotate the consent secret).

**Exit / decommission:** disconnect the app/connector in each platform's
settings; revoke tokens by deleting their entries from the
`mcp_oauth_state` volume. Server-side nothing was added that needs removal.

## Sources (tenet 8)

- OpenAI — [Building MCP servers for ChatGPT Apps and API integrations](https://developers.openai.com/api/docs/mcp)
  (apps/connector rename, data-only shape, OAuth/CIMD/DCR support) — fetched 2026-06-10
- OpenAI — [ChatGPT Developer mode](https://developers.openai.com/api/docs/guides/developer-mode)
  (eligibility Pro/Plus/Business/Enterprise/Edu on web; SSE + streamable HTTP;
  OAuth / No Auth / Mixed; no `search`/`fetch` requirement) — fetched 2026-06-10
- Perplexity — [Adding Custom Remote Connectors (help center, article 13915507)](https://www.perplexity.ai/help-center/en/articles/13915507-adding-custom-remote-connectors)
  (full registration flow, auth options incl. DCR, transports, redirect URL) — fetched 2026-06-10
- Perplexity — [Changelog 2026-03-13](https://www.perplexity.ai/changelog/what-we-shipped---march-13-2026)
  ("Bring Your Own Connector": Pro/Max/Enterprise) — fetched 2026-06-10
- Third-party setup guides (Truthifi, Atlan, Otter, contextprotocol.dev) for
  the mobile-availability and UI-flow claims marked "verify live" above —
  deliberately not load-bearing (COE lesson: first-party docs decide)
