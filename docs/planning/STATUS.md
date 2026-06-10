# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**Goal 2 CLOSED: claude.ai connector registered and
OAuth-approved live — the iPhone surface is done. Operator set the next direction:
similar remote integrations for Perplexity and ChatGPT**). Repo-health green at
session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly. **All four memory surfaces are now live
end-to-end**, including the last one: Claude (web + iPhone) talks to the memory bank
through `https://mcp.chandrav.dev/` via a remote MCP connector with **self-hosted OAuth
2.1** (ADR 035 — built, deployed, and operator-approved on claude.ai today). The secret
is in Bitwarden; tokens rotate and survive redeploys.

**New direction (operator, 2026-06-10 evening):** bring the same kind of native remote
integration to **Perplexity and ChatGPT** (primarily those two). Today ChatGPT is covered
only via the Chrome extension on desktop; Perplexity has nothing. Whether each platform
supports remote MCP connectors (and with what auth) is a **volatile external fact that
must be web-verified next session before any design** — that's the COE
2026-06-10-claude-connector-auth-assumption lesson: verify the *registration surface's
own docs* at design time, then ADR, then build.

**Quick pending check (non-blocking):** open the Claude iPhone app once and run a memory
search to confirm the connector synced from web (it inherits automatically).

**Day plan (operator-set, 2026-06-10):** (1) model-switch hardening — **done**; (2) all
four surfaces read/write mem0 — **done (Goal 2 closed)**; (3) memory bank snapshot +
honest graph report — **parked**, superseded in priority by the Perplexity/ChatGPT
direction unless the operator re-orders.

## Current phase

**Between goals.** Goal 2 (remote MCP for Claude iPhone) is closed: ADR 035 OAuth live,
connector registered + approved on claude.ai. Next phase: **multi-LLM remote
integrations (Perplexity, ChatGPT)** — starts with platform-capability research, not
code. Infra phases 0–4 live; phases 5–8 stubs.

## Done this session (2026-06-10, OAuth session)

- **COE 2026-06-10-claude-connector-auth-assumption** — ADR 034 assumed a token field
  the claude.ai UI doesn't have; prevent action: verify the third-party registration
  surface's own docs at design time.
- **ADR 035** (supersedes ADR 034 §2) — self-hosted OAuth 2.1 AS+RS in the `mcp-proxy`
  container: SDK-provided DCR/PKCE/discovery/token endpoints; ours is only
  `src/mcp_proxy/oauth.py` (single-user provider + hashed-token JSON state on the
  `mcp_oauth_state` volume; access 1 h / refresh 60 d rotated) + a `/consent` page gated
  by `MCP_CONNECTOR_BEARER_TOKEN` (consent password + still a valid fallback bearer).
  Design doc `docs/design/remote-mcp-oauth.md`; TDD 25 new tests (103 passed, 94% cov).
- **Deployed + live-verified end-to-end** — full DCR → authorize → consent → PKCE token
  → `search_memories` rehearsal against `https://mcp.chandrav.dev/` returned real
  memories before any operator step.
- **Operator steps completed:** secret saved to Bitwarden
  (`MCP_CONNECTOR_BEARER_TOKEN (mcp.chandrav.dev)`, `ai-memory-infra` folder);
  connector registered on claude.ai → OAuth flow → consent approved → **connected,
  working** ("works!").
- **Docs propagated:** interfaces §13, setup walkthrough (OAuth connect flow),
  architecture coverage row (iOS Claude → Live), .env.example, private
  interview-packet decision log, BUILD-JOURNEY entry.

## Last decisions

- **Remote MCP auth = self-hosted OAuth 2.1 (ADR 035)** — claude.ai accepts nothing
  else; external IdP rejected (new vendor for one user); SDK owns protocol, we own
  policy only. One secret class kept (`MCP_CONNECTOR_BEARER_TOKEN` = consent password +
  fallback bearer).
- **Operator re-prioritization (2026-06-10 evening):** next build target is remote
  memory integration for **Perplexity and ChatGPT**, ahead of the parked Goal 3
  (memory-bank snapshot + graph report).

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Unchanged this step: ADR 033
gates #2/#4, graph-source one-way door (ADR 032 §4), supply-chain pinning,
`MEM0_DEFAULT_LLM_MODEL` boot-assert, Caddy rate limiting for the MCP route (incl.
`/consent`). Newly parked: Goal 3 (memory-bank snapshot + honest graph report);
iPhone connector spot-check (quick, operator, non-blocking).

## Open blockers / risks

- **None blocking.** Perplexity/ChatGPT platform support for remote MCP + auth models
  is unverified — next session's first job (tenet 8; COE lesson: check each platform's
  *own* connector docs before designing).
- **OpenClaw adapter gate (ADR 028):** verify `source`/`agent_id` before enabling writes.
- **`gpt-4.1-nano` silent fallback** if `MEM0_DEFAULT_LLM_MODEL` unset on the droplet.
- **Operator income change risk (end-June 2026):** spend must stay pause-able (`scripts/teardown.py`).

## Environment notes

- Use `working_directory` param, not raw `cd` (Drive path has spaces/parens). Windows
  PowerShell 5.1 (no `&&`); git push auth cached.
- **SSH:** Windows `ssh-agent` service is Automatic with the key loaded — droplet SSH
  works non-interactively (`BatchMode=yes`). Droplet `root@168.144.145.29`; stack
  `/opt/ai-memory-infra/infra`.
- **Token handling:** `MCP_CONNECTOR_BEARER_TOKEN` is in Bitwarden (master), Windows
  *user* env vars, and both `.env` files; never print it. **The agent's shell cannot
  reach the desktop clipboard** (access denied) — for clipboard handoffs, give the
  operator the one-line `... | clip` PowerShell command to run himself.
- **OAuth endpoint:** consent page `https://mcp.chandrav.dev/consent` (password = the
  connector secret); state file on the `mcp_oauth_state` Docker volume; deleting it
  revokes all issued tokens (one re-consent on claude.ai afterwards).

## Next action

> **RESUME HERE — multi-LLM remote memory integrations (operator priority):**
> web-verify, against each platform's **own current docs** (COE lesson), whether and how
> **ChatGPT** and **Perplexity** support user-added remote MCP / custom connectors —
> transport (Streamable HTTP?), auth (OAuth? DCR or pre-registered client? static
> token?), surfaces (web/desktop/mobile), and plan tier required. Then write the ADR:
> what each platform gets (reuse `mcp.chandrav.dev` + ADR 035 OAuth where possible — the
> server is already standard OAuth 2.1 + DCR, so new clients may Just Work), what falls
> back to the extension contract, and what is impossible today (documented honestly in
> architecture.md). Build only after the ADR. Concierge mode for any registration steps.
>
> Parked behind this: Goal 3 (memory-bank snapshot + honest graph report); iPhone
> connector spot-check (operator, 1 min, anytime).

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
