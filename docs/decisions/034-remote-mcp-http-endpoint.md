# ADR 034: Remote MCP HTTP endpoint for Claude mobile

**Status:** Accepted — **§2 (auth v1 = static bearer) superseded by ADR 035**
(claude.ai's connector UI accepts only OAuth/no-auth; see COE
2026-06-10-claude-connector-auth-assumption). Endpoint architecture stands.
**Date:** 2026-06-10
**Deciders:** Chandra (operator goal 2 of 2026-06-10 day plan)
**Supersedes / extends:** ADR 025 (local stdio proxy only)

## Context

Goal 2 of the 2026-06-10 day plan: all four memory surfaces must read/write the
same live Mem0 bank. Three already work:

| Surface | Path | Verified 2026-06-10 |
|---|---|---|
| Cursor / VS Code / Claude Code | Local stdio MCP proxy → REST (`metadata.source=mcp`) | Live add + search round-trip |
| Claude.ai / ChatGPT (Chrome desktop) | OpenMemory extension → REST (`metadata.source=extension`) | Live add + search round-trip |
| ChatGPT Chrome | Same extension contract as Claude Chrome | API reachable; same write path |

The fourth surface — **Claude on iPhone** — cannot start a local stdio process.
Anthropic's consumer clients require a **public HTTPS remote MCP server**
([Claude MCP connector docs](https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector),
verified 2026-06-10; [Claude Code MCP transport docs](https://docs.anthropic.com/en/docs/claude-code/mcp),
verified 2026-06-10).

Key client requirements (web-verified 2026-06-10):

1. **Transport:** Streamable HTTP is the current standard; legacy SSE is
   deprecated (`mcp-client-2025-11-20` beta header on the API path).
2. **Exposure:** `https://` URL, publicly reachable; stdio is not accepted.
3. **Capability:** Tools only for the Messages API / connector path (no resources
   or prompts on that surface today).
4. **Registration:** Add the connector at `claude.ai` → Customize → Connectors
   (paid Pro/Max plans). **Mobile inherits connectors configured on web/desktop
   first** ([Claude connector design guidelines](https://claude.com/docs/connectors/building/mcp-apps/design-guidelines),
   verified 2026-06-10).
5. **Auth:** Claude supports (a) OAuth 2.0 discovery (`401`/`403` +
   `WWW-Authenticate`, callback `https://claude.ai/api/mcp/auth_callback` per
   industry docs) and (b) a static `authorization_token` / `Authorization: Bearer`
   header on the connector definition.

Exposing an unauthenticated MCP endpoint on the public internet would let anyone
read and write Chandra's memory bank. **Auth model choice is a one-way door**
(tenet 17 effect test: a mistaken public launch cannot be un-seen). This ADR
deliberates before any droplet route goes live.

Our existing `src/mcp_proxy/server.py` already exposes the right three tools
(`search_memories`, `add_memory`, `list_memories`) and tags writes
`metadata.source=mcp` (ADR 028). The Python `mcp` package's `FastMCP` already
ships `streamable_http_app` / `run_streamable_http_async` — we do not need Mem0
upstream to grow HTTP MCP routes (ADR 025 confirmed Mem0 returns `404` on `/mcp`).

## Decision

### 1. Add a dedicated remote MCP service (not a path on `memory.`)

- **URL:** `https://mcp.{domain}/` (new subdomain `mcp.chandrav.dev`).
- **Why a subdomain:** keeps MCP session traffic separate from the Mem0 REST API,
  allows distinct auth and future rate limits without touching the extension/CORS
  surface on `memory.`.
- **Implementation:** run the same `mcp_proxy` code in **Streamable HTTP mode**
  inside a small Docker container on the droplet; reverse-proxy via Caddy (ADR
  009: only Caddy faces the internet).
- **Data plane:** unchanged — HTTP MCP tools still call the live Mem0 REST API
  with `X-API-Key` server-side; no second brain.

### 2. Auth v1 — dedicated static bearer token (not OAuth)

For a **single-user** deployment, ship v1 with:

- A **dedicated** `MCP_CONNECTOR_BEARER_TOKEN` (generate separately from
  `ADMIN_API_KEY` — smaller blast radius; revoking MCP access does not break the
  Chrome extension or local stdio proxy).
- The HTTP MCP server rejects requests without
  `Authorization: Bearer <MCP_CONNECTOR_BEARER_TOKEN>` (`401 Unauthorized`).
- Chandra registers the connector at `claude.ai` → Customize → Connectors with:
  - Transport: **Streamable HTTP**
  - URL: `https://mcp.chandrav.dev/`
  - Auth: paste the bearer token (Claude's connector UI and API both support
    `authorization_token` per Anthropic docs, 2026-06-10).

**Rejected for v1:**

| Option | Why not now |
|---|---|
| No auth / IP allowlist only | Public internet + dynamic Claude egress IPs ([Anthropic outbound ranges](https://docs.anthropic.com/en/api/ip-addresses)) — too fragile; fails the effect test. |
| Reuse `ADMIN_API_KEY` directly in Claude | Same key as extension + local MCP + bulk admin — one leak compromises everything; violates least-privilege. |
| Full OAuth 2.0 authorization server | Correct long-term for multi-user; disproportionate ops burden for solo use (client registration, token refresh, `/.well-known` metadata, callback handling). Revisit if we add other humans or publish the connector. |

OAuth remains the documented **v2 upgrade path** if we outgrow a static bearer.

### 3. Tool surface and contracts

- **Tools:** same three as ADR 025 / `docs/interfaces.md` §3.
- **Identity:** default `user_id=chandrav`; `metadata.source=mcp` on writes (ADR
  028).
- **No new memory contract fields** — this is transport only.

### 4. Infrastructure touch list (implementation follows this ADR)

1. `src/mcp_proxy/` — HTTP entrypoint (`streamable_http_app` + bearer gate).
2. `infra/docker-compose.yml` — `mcp-proxy` service (internal port; env:
   `MCP_CONNECTOR_BEARER_TOKEN`, `AI_MEMORY_API_KEY`, `AI_MEMORY_BASE_URL`).
3. `infra/Caddyfile` — `mcp.{$DOMAIN}` → `mcp-proxy:PORT`.
4. `infra/terraform/` — add `"mcp"` to `subdomains` (DNS A record).
5. Droplet `.env` — generate/store token in Bitwarden + private secrets catalog
   (ADR 017).
6. Operator step (cannot be automated): register connector on `claude.ai`, confirm
   it appears on iPhone, run one live round-trip.

## Propagation / conformance

| Consumer | Action |
|---|---|
| `src/mcp_proxy/server.py` | Add HTTP mode; shared tool implementations |
| `infra/*` | Compose + Caddy + Terraform subdomain |
| `docs/interfaces.md` | Register §13 remote MCP HTTP surface |
| `docs/setup.md` | Connector registration walkthrough |
| `docs/architecture.md` | Coverage matrix: iOS Claude → remote MCP (live) |
| Local `.cursor/mcp.json` | **No change** — stdio proxy stays for Cursor |

No changes required in `ai-memory-extension` (extension path is unchanged).

## Consequences

**Positive**

- Claude iPhone gains the same memory bank as Cursor and Chrome without forking
  data.
- Reuses proven tool code; Streamable HTTP is supported by our pinned `mcp>=1.0`
  dependency today.
- Bearer auth is operable by one person in minutes; token rotation = update
  droplet `.env` + re-paste in Claude connector settings.

**Negative / risks**

- Static bearer in Claude's connector store is only as safe as Claude's account
  security — acceptable for personal use; not enterprise-grade.
- A new public endpoint increases attack surface; mitigated by mandatory bearer
  auth, HTTPS, and (future) Caddy rate limiting (BACKLOG).
- Connector must be added on web before it appears on mobile — extra operator step.

**Exit / decommission**

- Remove Caddy route + DNS + container; delete connector in Claude settings;
  rotate/revoke `MCP_CONNECTOR_BEARER_TOKEN`. Local stdio proxy and extension
  continue unaffected (ADR 025, ADR 024).

## Sources (tenet 8)

- Anthropic — [MCP connector (Messages API)](https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector) — fetched 2026-06-10
- Anthropic — [Claude Code MCP transports & OAuth](https://docs.anthropic.com/en/docs/claude-code/mcp) — fetched 2026-06-10
- Anthropic — [Claude connector design guidelines (mobile)](https://claude.com/docs/connectors/building/mcp-apps/design-guidelines) — fetched 2026-06-10
- ADR 025 — Mem0 serves REST only; local stdio proxy
- ADR 009 — Caddy-only public exposure
- ADR 028 — `user_id` + `metadata.source` contract
