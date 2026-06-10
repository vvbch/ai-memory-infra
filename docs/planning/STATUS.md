# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**Goal 2 built: remote MCP endpoint for Claude iPhone is
deployed + live-verified; only the two operator steps remain — Bitwarden save + claude.ai
connector registration**). Repo-health green at session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly. **All four memory surfaces now have working
plumbing:** Cursor/VS Code/Claude Code (local MCP proxy), Chrome extension, ChatGPT
(extension contract), and — new this session — a public remote MCP endpoint at
`https://mcp.chandrav.dev/` for Claude on iPhone (ADR 034). The agent verified it live
end-to-end: TLS works, requests without the secret token are rejected (401), and an
authorized MCP search returned real memories from the bank.

**Day plan (operator-set, 2026-06-10):** (1) model-switch hardening — **done**; (2) all
four surfaces read/write mem0 — **build done, operator registration pending**; (3) memory
bank snapshot + honest graph report — parked until Goal 2 closes.

**What changed this session (Goal 2 build, 2026-06-10):**
- **`src/mcp_proxy/http_server.py`** — Streamable HTTP MCP entrypoint reusing the same
  three tools, behind a bearer-token gate (TDD, 6 new tests; suite 75 passed, 89% cov).
- **Infra:** `mcp-proxy` Compose service + slim Dockerfile, Caddy `mcp.{$DOMAIN}` route,
  Terraform `mcp` subdomain (applied — 1 DNS record added, nothing else touched).
- **`MCP_CONNECTOR_BEARER_TOKEN` generated** and persisted per the persistent-credential
  pattern: Windows user env var + local `infra/.env` + droplet `.env` (never echoed).
  Bitwarden save is the pending operator step; secrets-catalog row added (private repo).
- **Deployed to the droplet** (git pull → compose build → up → Caddy restart) and
  live-verified: `/health` 200, no-token 401, authorized `initialize` + `search_memories`
  round-trip returned live memories over `https://mcp.chandrav.dev/`.
- **Docs:** interfaces.md §13 (remote MCP surface), setup.md connector walkthrough,
  architecture.md iOS row → deployed/live-verified; legacy `chrome-extension-user`
  examples in setup.md aligned to `chandrav` (ADR 028).

**What you pay:** ~₹2,600/mo cloud box; full stack ≈ ₹3,800/mo landed; pause anytime with
`scripts/teardown.py`. (The new container is on the same box — no new spend.)

## Current phase

**Goal 2 of the 2026-06-10 day plan — remote MCP for Claude iPhone.** Build + deploy +
live verification are **done**. Remaining: operator saves the bearer token to Bitwarden,
registers the connector at `claude.ai` (web first; mobile inherits), and confirms one
iPhone round-trip. Goal 1 (model-switch hardening) remains done. Infra phases 0–4 live;
phases 5–8 stubs.

## Done this session (2026-06-10)

- **ADR 034 implemented end-to-end** — HTTP MCP entrypoint (bearer gate, stateless,
  DNS-rebinding protection scoped to `mcp.chandrav.dev`), `mcp-proxy` container, Caddy
  route, Terraform DNS record, token generated + persisted, deployed, live-verified
  (401 without token; authorized search returned real memories).
- **Docs/DoD propagation** — interfaces.md §13, setup.md remote-connector walkthrough,
  architecture.md coverage row, secrets-catalog row (private), ADR 028 user-id drift fix
  in setup.md examples.

## Last decisions

- **Remote MCP auth v1 = dedicated bearer token** — not OAuth (solo-operator
  proportionality); not reusing `ADMIN_API_KEY` (blast-radius). OAuth remains v2 (ADR 034).
- **`mcp-proxy` talks to Mem0 over the internal Docker network** (`http://mem0:8000`) —
  no hairpin through Caddy; admin key stays server-side, never in the Claude connector.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Unchanged this step: ADR 033 gates
#2/#4, graph-source one-way door (ADR 032 §4), supply-chain pinning, `MEM0_DEFAULT_LLM_MODEL`
boot-assert, Caddy rate limiting for the new MCP route.

## Open blockers / risks

- **Operator steps for Goal 2 close-out:** Bitwarden save of `MCP_CONNECTOR_BEARER_TOKEN`,
  then claude.ai connector registration + iPhone round-trip (agent hands these one at a time).
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
- **Claude iPhone connector:** must be added on `claude.ai` → Settings → Connectors (web)
  before it appears on mobile (Anthropic docs, 2026-06-10). Walkthrough: `docs/setup.md`
  → "Remote MCP connector for Claude".

## Next action

> **RESUME HERE — close out Goal 2 with the two operator steps** (concierge mode, one at
> a time): (1) put `MCP_CONNECTOR_BEARER_TOKEN` on the operator's clipboard
> (`Set-Clipboard` from the user env var — never print it) and have him save it as
> Bitwarden item `MCP_CONNECTOR_BEARER_TOKEN (mcp.chandrav.dev)` in the `ai-memory-infra`
> folder; (2) walk him through `claude.ai` → Settings → Connectors → Add custom connector
> (URL `https://mcp.chandrav.dev/`, paste the token), then confirm the connector appears
> in the iPhone Claude app and run one live round-trip (`search_memories` for a known
> fact). The endpoint itself is already deployed and live-verified.
>
> After Goal 2 (or ~9pm IST): **Goal 3** — memory-bank snapshot + honest graph report.

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
