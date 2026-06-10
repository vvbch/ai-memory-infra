# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**ChatGPT + Perplexity platform research done against
first-party docs; ADR 036 written: both reuse `mcp.chandrav.dev` + ADR 035 OAuth
unchanged. Awaiting operator's plan tiers before registration**). Repo-health green
at session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly. All four original surfaces are live,
including Claude (web + iPhone) via the remote MCP connector with self-hosted OAuth 2.1
(ADR 035, operator-approved on claude.ai).

**This session:** the Perplexity/ChatGPT research the COE demanded is **done, against
each platform's own docs**. Good news — both support exactly what we already built:

- **ChatGPT** (OpenAI docs): custom remote MCP servers via **developer mode** (Settings
  → Apps → Advanced → Developer mode; web registration; Plus plan or above). Auth =
  OAuth with DCR — our server's exact protocol. No static tokens accepted.
- **Perplexity** (help center + changelog): **custom remote connectors** since
  2026-03-13 (Pro plan or above). Account settings → Connectors → + Custom connector;
  OAuth 2.0 with DCR supported; Streamable HTTP supported.

**ADR 036 is written:** both platforms register against the existing
`https://mcp.chandrav.dev/` endpoint and the existing OAuth server — near-zero new
server code (only the consent page's "Claude" wording gets generalized). Coverage
claims in architecture.md update only after a live memory round-trip on each platform.

**The one thing blocking registration:** we don't know the **plan tiers** of your
ChatGPT and Perplexity accounts. ChatGPT custom connectors need **Plus or above**;
Perplexity custom connectors need **Pro or above**. Free tier on either = that
platform is blocked on a paid-subscription decision (yours, tenet 12/15).

**Quick pending check (non-blocking):** open the Claude iPhone app once and run a
memory search to confirm the connector synced from web.

## Current phase

**Multi-LLM remote integrations (Perplexity, ChatGPT) — design done (ADR 036),
registration not started.** Infra phases 0–4 live; phases 5–8 stubs.

## Done this session (2026-06-10, platform-research session)

- Repo-health green at start (both repos clean, 0 ahead/behind).
- **Web-verified ChatGPT support against OpenAI's own docs** (developers.openai.com
  MCP guide + developer-mode guide): remote MCP custom apps supported; developer mode
  full read/write client (no `search`/`fetch` shape needed); SSE + Streamable HTTP;
  OAuth (CIMD or DCR) / None / Mixed — **no static tokens**; eligibility Pro/Plus/
  Business/Enterprise/Edu, **web registration only**.
- **Web-verified Perplexity support against its own help center + changelog**
  (article 13915507, changelog 2026-03-13): custom remote connectors on Pro/Max/
  Enterprise; OAuth 2.0 (DCR supported — client ID/secret only if no DCR) / API Key /
  None; Streamable HTTP or SSE; HTTPS required; OAuth callback
  `https://www.perplexity.ai/rest/connections/oauth_callback`.
- **ADR 036 written:** one server, three platforms; ChatGPT = developer-mode custom
  app, Perplexity = custom remote connector, both on ADR 035 OAuth via DCR; extension
  contract unchanged (coexists on ChatGPT); honest-coverage rule (architecture.md
  updates only after live verification); plan-tier gate flagged as operator decision.
- **Interview packet decision log** appended (ADR 036 entry, private repo).
- **Plan-tier gate cleared (operator):** ChatGPT = Plus+, Perplexity = Pro+ — both
  platforms are go; no new subscription spend needed.
- **Consent page generalized + deployed + live-verified:** TDD (2 new tests incl.
  hostile client_name escaping; 105 passed, 94% cov), deployed to droplet, smoke-tested
  live — consent page now names the requesting client; old "Claude" copy gone.

## Last decisions

- **ADR 036 — ChatGPT + Perplexity reuse the ADR 035 endpoint + OAuth unchanged.**
  ChatGPT via developer-mode custom apps (OAuth/DCR; data-only `search`/`fetch` shape
  rejected — would reshape our tools for no need). Perplexity via custom remote
  connectors (OAuth 2.0/DCR over Streamable HTTP; static API key rejected — one auth
  story for all platforms). Only expected code change: generalize consent-page copy.
- Mobile availability on both platforms is third-party-reported only — treat as
  "verify live at registration", never claim it in architecture.md beforehand.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Unchanged this step: ADR 033
gates #2/#4, graph-source one-way door (ADR 032 §4), supply-chain pinning,
`MEM0_DEFAULT_LLM_MODEL` boot-assert, Caddy rate limiting for the MCP route (incl.
`/consent`). Parked: Goal 3 (memory-bank snapshot + honest graph report); iPhone
connector spot-check (quick, operator, non-blocking).

## Open blockers / risks

- **Plan-tier gate (operator input pending):** ChatGPT custom connectors need Plus+;
  Perplexity needs Pro+. Operator's current tiers unknown — asked 2026-06-10 evening.
  Free tier on either platform = paid-subscription decision before that registration.
- **ChatGPT developer mode is beta** — OpenAI can re-gate it; extension still covers
  ChatGPT desktop regardless.
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
  revokes all issued tokens (one re-consent per platform afterwards).

## Next action

> **RESUME HERE — register the connectors (ADR 036; plan tiers confirmed, consent
> page generalized + deployed; concierge mode):** (1) Concierge the Perplexity
> registration (Account settings → Connectors → + Custom connector → Remote; OAuth
> 2.0; Streamable HTTP; URL `https://mcp.chandrav.dev/`; consent password =
> `MCP_CONNECTOR_BEARER_TOKEN` from Bitwarden) — **in progress 2026-06-10 evening,
> operator was handed the registration step**; live-verify with a real memory
> search, then update architecture.md coverage + setup.md walkthrough. (2) Same for
> ChatGPT (web Settings → Apps & Connectors → Advanced settings → Developer mode →
> create app; OAuth). (3) Verify mobile availability on both before claiming it
> anywhere.
>
> Parked behind this: Goal 3 (memory-bank snapshot + honest graph report); iPhone
> Claude connector spot-check (operator, 1 min, anytime).

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
