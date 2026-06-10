# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**Goal 2 started: three surfaces live-verified + ADR 034
accepted for remote MCP; droplet deploy is next**). Repo-health green at session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly. Three of four memory surfaces are proven
working today; the fourth (Claude on iPhone) has a design locked in ADR 034 and needs a
droplet deploy.

**Day plan (operator-set, 2026-06-10):** (1) model-switch hardening — **done**; (2) all
four surfaces read/write mem0 — **in progress** (verify ✅, ADR ✅, build ⬜); (3) memory
bank snapshot + honest graph report — parked until Goal 2.

**What changed this session (Goal 2, 2026-06-10):**
- **Live round-trips verified** for Cursor/MCP (`metadata.source=mcp`), Chrome extension
  (`metadata.source=extension`), and ChatGPT (same extension contract) against the live API.
- **ADR 034 accepted** — remote Streamable HTTP MCP at `mcp.chandrav.dev`, bearer-token auth
  v1 (dedicated token, not the admin API key), same three tools as the local proxy.
- **Cursor MCP config fixed** — `.cursor/mcp.json` `AI_MEMORY_USER_ID` corrected from legacy
  `chrome-extension-user` to `chandrav` (ADR 028).
- **Droplet SSH permanently unblocked** — operator set the Windows `ssh-agent` service to
  Automatic (admin PowerShell) and the key is loaded; Windows persists agent keys across
  reboots. Verified non-interactive (`BatchMode=yes`) SSH to the droplet. No more
  per-session passphrase handoffs; `ssh_unlock.py` stays as fallback only.
- **Persistent-credential pattern codified** (AGENTS.md § collab + handoff spec): one-time
  machine persistence beats recurring handoffs. Full inventory verified — every credential
  the agent needs is already durable on this Windows box: SSH key (ssh-agent), git push
  (GCM), `gh` (keyring), `AI_MEMORY_API_KEY` (user env var), Terraform secrets
  (`terraform.tfvars`), stack `.env`. Only gap: the future `MCP_CONNECTOR_BEARER_TOKEN`
  (ADR 034) — persist as user env var + Bitwarden when generated in Goal 2.

**What you pay:** ~₹2,600/mo cloud box; full stack ≈ ₹3,800/mo landed; pause anytime with
`scripts/teardown.py`.

## Current phase

**Goal 2 of the 2026-06-10 day plan — remote MCP for Claude iPhone.** Verification and
auth deliberation are done (ADR 034). Next: implement the HTTP MCP service + Caddy route +
DNS on the droplet, then operator registers the connector at `claude.ai`. Goal 1 (model
switch hardening) remains done. Infra phases 0–4 live; phases 5–8 stubs.

## Done this session (2026-06-10)

- **Three-surface live verification** — MCP path, extension path, and ChatGPT contract path
  all passed add + semantic search round-trips against `memory.chandrav.dev`.
- **ADR 034** — remote MCP HTTP endpoint design (Streamable HTTP, bearer auth, `mcp.` subdomain).
- **`.cursor/mcp.json`** — `AI_MEMORY_USER_ID` aligned to `chandrav`.
- **`docs/architecture.md`** — iOS Claude row updated to ADR 034 / deploy pending.
- **`scripts/ssh_unlock.py` + `operator-credential-handoff` skill** — clipboard → agent
  SSH unlock; AGENTS.md + interfaces §12 updated. (ADR 034 + skill artifacts from the
  previous session were found uncommitted and are now committed + pushed.)

## Last decisions

- **Remote MCP auth v1 = dedicated bearer token** — not OAuth (solo-operator proportionality);
  not reusing `ADMIN_API_KEY` (blast-radius). OAuth remains the v2 path (ADR 034).
- **`mcp.chandrav.dev` subdomain** — separate from `memory.` REST API; same tool code as local
  stdio proxy; Caddy-only public exposure (ADR 009 + ADR 034).

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Unchanged this step: ADR 033 gates
#2/#4, graph-source one-way door (ADR 032 §4), supply-chain pinning, `MEM0_DEFAULT_LLM_MODEL`
boot-assert, Caddy rate limiting for the new MCP route.

## Open blockers / risks

- **OpenClaw adapter gate (ADR 028):** verify `source`/`agent_id` before enabling writes.
- **`gpt-4.1-nano` silent fallback** if `MEM0_DEFAULT_LLM_MODEL` unset on the droplet.
- **Operator income change risk (end-June 2026):** spend must stay pause-able (`scripts/teardown.py`).

## Environment notes

- Use `working_directory` param, not raw `cd` (Drive path has spaces/parens). Windows
  PowerShell 5.1; git push auth cached.
- **SSH:** Windows `ssh-agent` service is Automatic with the key loaded (persists across
  reboots) — droplet SSH works non-interactively, no passphrase handoff needed. Fallback
  only if the key is ever missing: `python scripts/ssh_unlock.py` after operator copies
  the passphrase (Bitwarden) to clipboard. Droplet `root@168.144.145.29`; stack
  `/opt/ai-memory-infra/infra`.
- **Claude iPhone connector:** must be added on `claude.ai` → Customize → Connectors (web)
  before it appears on mobile (Anthropic docs, 2026-06-10).

## Next action

> **RESUME HERE — implement ADR 034 on the droplet** (SSH is unblocked — agent connects
> directly, no operator handoff needed). Build:
> (1) HTTP MCP entrypoint in `src/mcp_proxy/` with bearer gate; (2) `mcp-proxy` Compose
> service; (3) Caddy `mcp.{$DOMAIN}` route; (4) Terraform `mcp` subdomain; (5) generate
> `MCP_CONNECTOR_BEARER_TOKEN` → Bitwarden + droplet `.env`; (6) deploy; (7) operator
> registers connector at `claude.ai` and confirms iPhone round-trip.
>
> After Goal 2 (or ~9pm IST): **Goal 3** — memory-bank snapshot + honest graph report.

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
