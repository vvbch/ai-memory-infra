# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (ChatGPT web **live-verified**; consent HTML redirect
fix; session committed+pushed; COE 2026-06-10-session-end-commit-permission-ask).
Repo-health green at session end.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **All ADR 036 web surfaces are live:**
Claude (web + iPhone via remote MCP + OAuth), Perplexity (custom connector),
and **ChatGPT** (developer-mode custom app). One server (`https://mcp.chandrav.dev/`),
one OAuth story (ADR 035).

**ChatGPT registration (this session):** OAuth connected after consent-page HTML
auto-redirect fix (bare 302 stalled in ChatGPT's popup). Live memory proof:
`CallToolRequest` → Mem0 `POST /search` 200 in proxy logs when operator enabled
ai-memory per-chat (+ → Developer mode) and forced `search_memories`. ChatGPT's UI
shows **abbreviated tool snippets**, not full JSON — server logs are the honest
proof (same class of lesson as Perplexity's profile hallucination).

**Operator tips for ChatGPT:** (1) toggle **ai-memory ON per chat** under
Developer mode — Settings "Connected" is not enough; (2) vague "search my memories"
routes to Google connectors or ChatGPT memory — name the **ai-memory** app and
`search_memories` explicitly; (3) Chrome extension still auto-captures on desktop
(ADR 036 coexistence).

**Not yet verified:** mobile inherit for Perplexity + ChatGPT apps; iPhone Claude
connector spot-check (quick, operator, non-blocking).

## Current phase

**Multi-LLM remote integrations (ADR 036) — web registration complete on all
three platforms.** Infra phases 0–4 live; phases 5–8 stubs.

## Done this session (2026-06-10, ChatGPT registration + verify)

- Repo-health green at start (both repos clean, 0 ahead/behind).
- **ChatGPT developer-mode app registered + OAuth-connected** (Plus plan; DCR;
  callback `https://chatgpt.com/connector/oauth/...`).
- **Consent redirect fix:** HTML success page with JS + manual link (ChatGPT popup
  stalled on bare 302); deployed to droplet; TDD (2 new tests + ChatGPT resource
  flow test; 23 OAuth tests pass).
- **ChatGPT live-verified:** `search_memories` round-trip confirmed in mcp-proxy
  logs (`CallToolRequest` + Mem0 search 200); architecture.md ChatGPT row updated.
- **Hallucination triage (ChatGPT):** first attempts answered from ChatGPT memory /
  Google namespaces with zero tool calls; enabling app per-chat + explicit tool
  prompt required (documented pattern matches Perplexity lesson in setup.md).

## Last decisions

- **ADR 036 — one server, three platforms** (unchanged): ChatGPT developer-mode
  custom app + Perplexity custom connector on ADR 035 OAuth; extension coexists on
  ChatGPT desktop.
- **Consent completion returns HTML auto-redirect** (not bare 302) — reversible
  UX fix for ChatGPT OAuth popup; Claude/Perplexity unaffected.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Parked: Goal 3
(memory-bank snapshot + honest graph report); mobile inherit verification
(Perplexity + ChatGPT, ~1 min each); iPhone Claude connector spot-check.

## Open blockers / risks

- **ChatGPT developer mode is beta** — OpenAI can re-gate it; extension still covers
  ChatGPT desktop regardless.
- **ChatGPT Plus read-only custom MCP** — write tools (`add_memory`) may be
  disabled on Plus; `search_memories` verified read path only.
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
  *user* env vars, and both `.env` files; never print it. Clipboard handoff via
  tkinter `clipboard_append` (verified); agent clears after use.
- **OAuth endpoint:** consent page `https://mcp.chandrav.dev/consent` (password = the
  connector secret); state file on the `mcp_oauth_state` Docker volume.

## Next action

> **RESUME HERE — ADR 036 mobile spot-checks (operator, ~2 min):**
> open Perplexity mobile + ChatGPT mobile apps; confirm ai-memory connector
> inherited from web and run one forced `search_memories` each (or note missing).
> Optional: iPhone Claude connector spot-check. Then pick next from BACKLOG (Goal 3
> or infra hardening). Web ADR 036 integration is **done**.

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
