# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**Goal 2 auth rebuilt as self-hosted OAuth (ADR 035): built,
tested, deployed, and the full OAuth flow rehearsed live against `mcp.chandrav.dev` — only
the two operator steps remain: Bitwarden save + claude.ai connect**). Repo-health green at
session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly. All four memory surfaces have working plumbing;
the last one (Claude iPhone via `https://mcp.chandrav.dev/`) hit a registration blocker:
**claude.ai custom connectors only accept OAuth** — the static bearer token from ADR 034 has
no place to be pasted (COE 2026-06-10-claude-connector-auth-assumption). You decided: build
minimal self-hosted OAuth now.

**This session built and shipped it (ADR 035):** the endpoint is now its own OAuth 2.1
authorization server — discovery, dynamic client registration, PKCE — using the auth
framework already inside our pinned MCP SDK (no new vendor, no new dependency). The only
new code is the single-user part: a consent page where you paste the existing connector
secret to approve Claude, and a small state file (hashed tokens, Docker volume) so the
connector survives redeploys. Your old token still works for curl tests. 25 new tests
(suite 103 passed, 94% coverage, lint/types clean), deployed to the droplet, and the agent
rehearsed the entire flow Claude will run — register → authorize → consent → token →
memory search — live against `https://mcp.chandrav.dev/`, getting real memories back with
an OAuth-issued token.

**Day plan (operator-set, 2026-06-10):** (1) model-switch hardening — **done**; (2) all
four surfaces read/write mem0 — **OAuth build done; deploy + claude.ai registration
remain**; (3) memory bank snapshot + honest graph report — parked until Goal 2 closes.

## Current phase

**Goal 2 of the 2026-06-10 day plan — remote MCP for Claude iPhone.** OAuth build,
droplet deploy, and live flow rehearsal are **done**. Remaining: the two operator steps —
Bitwarden save of `MCP_CONNECTOR_BEARER_TOKEN`, claude.ai connector registration (an
OAuth connect + consent-page approval, no token field), one iPhone round-trip. Goal 1
remains done. Infra phases 0–4 live; phases 5–8 stubs.

## Done this session (2026-06-10, OAuth session)

- **COE 2026-06-10-claude-connector-auth-assumption** — ADR 034 assumed a token field the
  claude.ai UI doesn't have; root cause: design verified against the Messages-API doc, not
  the claude.ai connector-auth doc; prevent action codified in the COE + ADR 035 Sources.
- **ADR 035** (supersedes ADR 034 §2) — self-hosted OAuth 2.1 AS+RS in the same
  `mcp-proxy` container: SDK-provided DCR/PKCE/discovery/token endpoints; ours is only
  `src/mcp_proxy/oauth.py` (single-user provider + JSON state store, tokens SHA-256-hashed
  on the `mcp_oauth_state` volume; access 1 h / refresh 60 d rotated) and a `/consent`
  page gated by the existing `MCP_CONNECTOR_BEARER_TOKEN` (consent password + still a
  valid fallback bearer token). Design doc `docs/design/remote-mcp-oauth.md`.
- **TDD:** `tests/test_mcp_proxy/test_oauth.py` (full flow + abuse paths) + reworked
  `test_http_server.py`; 103 passed, 94% cov; ruff + mypy strict clean.
- **Infra:** compose volume + `MCP_PUBLIC_BASE_URL`; Caddyfile/Dockerfile/.env.example
  comments; docs propagated (interfaces §13, setup walkthrough, architecture row,
  private interview-packet decision log, BUILD-JOURNEY entry).
- **Deployed + live-verified** (`acbdcbb` on the droplet): `/health` 200; discovery
  metadata correct (S256, `/register`); no-token MCP call → 401 with
  `resource_metadata` challenge; **full OAuth rehearsal** (DCR → authorize → consent →
  PKCE token → `search_memories`) returned real memories; static-token path still green.

## Last decisions

- **Remote MCP auth = self-hosted OAuth 2.1 (ADR 035)** — claude.ai accepts nothing else;
  external IdP rejected (new vendor for one user); SDK owns protocol, we own policy only.
- **One secret class kept** — `MCP_CONNECTOR_BEARER_TOKEN` becomes the OAuth consent
  password and stays a valid static access token for verification/API-path callers.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Unchanged this step: ADR 033 gates
#2/#4, graph-source one-way door (ADR 032 §4), supply-chain pinning, `MEM0_DEFAULT_LLM_MODEL`
boot-assert, Caddy rate limiting for the MCP route (now incl. `/consent`).

## Open blockers / risks

- **Goal 2 close-out (operator steps only):** Bitwarden save of the secret, claude.ai
  OAuth connect (consent page), iPhone round-trip (agent hands these one at a time).
- **OpenClaw adapter gate (ADR 028):** verify `source`/`agent_id` before enabling writes.
- **`gpt-4.1-nano` silent fallback** if `MEM0_DEFAULT_LLM_MODEL` unset on the droplet.
- **Operator income change risk (end-June 2026):** spend must stay pause-able (`scripts/teardown.py`).

## Environment notes

- Use `working_directory` param, not raw `cd` (Drive path has spaces/parens). Windows
  PowerShell 5.1 (no `&&`); git push auth cached.
- **SSH:** Windows `ssh-agent` service is Automatic with the key loaded — droplet SSH
  works non-interactively (`BatchMode=yes`). Fallback only: `python scripts/ssh_unlock.py`
  after operator copies the passphrase to clipboard. Droplet `root@168.144.145.29`; stack
  `/opt/ai-memory-infra/infra`.
- **Token handling:** `MCP_CONNECTOR_BEARER_TOKEN` is in the Windows *user* env vars and
  both `.env` files; never print it — compare via hash, hand to operator via clipboard.
- **Claude connector:** added on `claude.ai` → Settings → Connectors (web) before it
  appears on mobile; registration is OAuth — leave client-id/secret fields empty, approve
  on our `/consent` page. Walkthrough: `docs/setup.md` → "Remote MCP connector for Claude".

## Next action

> **RESUME HERE — close out Goal 2 with the two operator steps** (concierge mode, one at
> a time): (1) put `MCP_CONNECTOR_BEARER_TOKEN` on the operator's clipboard
> (`Set-Clipboard` from the *user-scope* env var — never print it) and have him save it as
> Bitwarden item `MCP_CONNECTOR_BEARER_TOKEN (mcp.chandrav.dev)` in the `ai-memory-infra`
> folder; (2) walk him through `claude.ai` → Settings → Connectors → Add custom connector
> (URL `https://mcp.chandrav.dev/`, OAuth client-id/secret fields **empty**) → he approves
> on the `mcp.chandrav.dev/consent` page by pasting that same secret → confirm the
> connector appears in the iPhone Claude app and run one live `search_memories`
> round-trip. The endpoint, OAuth flow, and deploy are already live-verified end-to-end.
>
> After Goal 2 (or ~9pm IST): **Goal 3** — memory-bank snapshot + honest graph report.

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
