# ADR 035: Minimal self-hosted OAuth 2.1 for the remote MCP endpoint

**Status:** Accepted
**Date:** 2026-06-10
**Deciders:** the operator (operator: "Build minimal self-hosted OAuth now")
**Supersedes / extends:** ADR 034 §2 (auth v1 = static bearer token). The rest
of ADR 034 (subdomain, container, transport, tool surface) stands unchanged.

## Context

ADR 034 shipped `https://mcp.example.com/` behind a static bearer token,
assuming claude.ai's connector UI accepts an `authorization_token`. It does not
(COE 2026-06-10-claude-connector-auth-assumption): the **claude.ai custom
connector UI supports only OAuth or no auth**. Verified against the
surface-specific docs this time (fetched 2026-06-10):

- [Authentication for connectors](https://claude.com/docs/connectors/building/authentication):
  supported types are `oauth_dcr` (RFC 7591 Dynamic Client Registration,
  out of the box), `oauth_cimd` (Client ID Metadata Documents, out of the box),
  `oauth_anthropic_creds` / `custom_connection` (require contacting Anthropic),
  and `none`. **No static-token option.**
- PKCE is mandatory: Claude sends `code_challenge_method=S256` on every
  authorization request and requires
  `"code_challenge_methods_supported": ["S256"]` in the AS metadata.
- Discovery: the MCP server must host RFC 9728 protected-resource metadata at
  `/.well-known/oauth-protected-resource` pointing at the authorization server,
  whose own metadata lives at `/.well-known/oauth-authorization-server`.
- OAuth callback for hosted surfaces: `https://claude.ai/api/mcp/auth_callback`
  ([Building custom connectors](https://claude.com/docs/connectors/building)).
- Token endpoint must accept `application/x-www-form-urlencoded`; refresh
  tokens are supported; clients may send the RFC 8707 `resource` parameter.

Unauthenticated (`none`) is ruled out — this endpoint reads/writes the
personal memory bank (same one-way-door reasoning as ADR 034).

## Decision

### 1. Self-hosted OAuth 2.1 inside the existing `mcp-proxy` container

The endpoint becomes its own **authorization server + resource server** at the
same origin (`https://mcp.example.com`), implemented with the **auth framework
already shipped by our pinned `mcp` Python SDK (1.27.2)** — `AuthSettings` +
`OAuthAuthorizationServerProvider`. The SDK mounts and handles:

- `/.well-known/oauth-authorization-server` (advertises S256 + registration endpoint)
- `/.well-known/oauth-protected-resource` (RFC 9728)
- `/register` (DCR, RFC 7591), `/authorize`, `/token` (PKCE S256 verification,
  refresh grant), plus the 401 `WWW-Authenticate` challenge with
  `resource_metadata` on the MCP route.

We write only the **single-user provider** (~one module): client store,
auth-code/token issuance, and an operator consent page. **No new dependency, no
external IdP, no new vendor** (tenets 7, 12).

### 2. Single-user consent = the existing connector secret

`/authorize` redirects to a minimal `/consent` page where the operator pastes
`MCP_CONNECTOR_BEARER_TOKEN` (already generated, in the machine stores and
pending Bitwarden). Correct secret → auth code → redirect back to
`https://claude.ai/api/mcp/auth_callback`. This keeps **one secret class**:
the token's role changes from transport credential to consent password.
Anyone can DCR-register a client (the RFC requires it to be open), but
registration grants nothing — no tokens without the consent secret.

### 3. Token model — opaque, hashed at rest, file-persisted

- Access tokens: opaque 256-bit random, **1 h** lifetime.
- Refresh tokens: opaque 256-bit random, **60 d** lifetime, **rotated on use**.
- Stored **SHA-256-hashed** in a small JSON state file on a Docker named volume
  (`/data/oauth_state.json`) together with registered clients — tokens survive
  container redeploys (no re-consent on every deploy), and the file never
  contains a usable bearer secret. Client-store capped (50, evict-oldest) so
  open DCR cannot grow the file unboundedly.
- The **static bearer token remains accepted** as an access token on the MCP
  route — it is the agent's live-verification path (curl) and a working
  fallback for API-path callers that do support `authorization_token`.

**Rejected alternatives:**

| Option | Why not |
|---|---|
| External IdP (Auth0/Cognito/etc.) | New vendor + recurring cost + lock-in for one user (tenets 7, 12, 15) |
| JWT / stateless signed tokens | Needs a signing-key secret + no revocation without a denylist (which is state again); file-backed opaque tokens are simpler and revocable |
| CIMD-only (skip DCR) | CIMD officially documented only for Claude Code; claude.ai web/mobile path is DCR — DCR via the SDK costs nothing extra |
| In-memory tokens (no persistence) | Every deploy/restart kills the connector session → operator re-consents constantly; violates "zero cognitive load" |
| Authless (`none`) | Public read/write of the memory bank — fails the one-way-door test |

### 4. Unchanged from ADR 034

Subdomain, Caddy route, container, internal Mem0 network path, the three tools,
`user_id=primary-user`, `metadata.source=mcp`, `/health` open for probes.

## Propagation / conformance

| Consumer | Action |
|---|---|
| `src/mcp_proxy/http_server.py` | Replace `BearerGate` wiring with SDK auth (AS+RS) |
| `src/mcp_proxy/oauth.py` (new) | Provider + state store + consent page |
| `infra/docker-compose.yml` | `mcp-proxy`: add state volume + `MCP_PUBLIC_BASE_URL` |
| `docs/interfaces.md` §13 | Auth contract: OAuth endpoints + static-token fallback |
| `docs/setup.md` | Connector walkthrough: OAuth connect flow (no token paste field) |
| `docs/design/remote-mcp-oauth.md` | Design doc (this ADR's shape) |
| `ai-memory-extension` / local stdio proxy | **No change** — different surfaces |

## Consequences

**Positive:** the claude.ai registration path actually works; tokens are
short-lived and rotated (strictly better than a long-lived static bearer in
Claude's store); revocation = delete state file entry or rotate the consent
secret; still zero external dependencies.

**Negative / risks:** ~300 LoC of auth-adjacent code we now own (mitigated:
protocol mechanics — PKCE, DCR validation, redirect-URI checks — are the SDK's,
not ours; ours is storage + consent); a consent page is a phishable surface
(mitigated: secret never leaves the operator's clipboard except into our own
origin's form; rate-limited by Caddy later, BACKLOG).

**Exit / decommission:** unchanged from ADR 034; additionally delete the
`mcp_oauth_state` volume. Reverting to bearer-only is a git revert.

## Sources (tenet 8)

- Anthropic — [Authentication for connectors](https://claude.com/docs/connectors/building/authentication)
  (the claude.ai-surface auth doc — the page COE-mandated for this decision) — fetched 2026-06-10
- Anthropic — [Building custom connectors](https://claude.com/docs/connectors/building) — fetched 2026-06-10
- Anthropic — [Lazy authentication / CIMD example](https://claude.com/docs/connectors/building/lazy-authentication) — fetched 2026-06-10
- `mcp` SDK 1.27.2 source (`mcp/server/auth/*`) — read locally 2026-06-10; ships
  metadata/DCR/authorize/token handlers + PKCE S256 verification
- ADR 034 — endpoint architecture (stands); COE 2026-06-10-claude-connector-auth-assumption
