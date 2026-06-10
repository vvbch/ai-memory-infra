# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (ADR 036 **complete** — iPhone mobile inherit
verified for Perplexity, ChatGPT, and Claude; operator confirmed connector
calls on all three). Repo-health green at session end.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **ADR 036 is done on every surface we
targeted:** Claude (web + iPhone remote MCP + OAuth), Perplexity (web + iPhone),
and ChatGPT (web + iPhone developer-mode app). One server (`https://mcp.chandrav.dev/`),
one OAuth story (ADR 035). Desktop Chrome extension still auto-captures alongside
all of the above.

**iPhone spot-check (this session):** operator confirmed **ai-memory** connector
visible and live on Perplexity and ChatGPT mobile apps (inherited from web
registration). On Claude iPhone: **Load all connectors** enabled, query made a
real connector call. ADR 036 mobile inherit is **verified**, not third-party-reported.

**Operator tips (unchanged):** ChatGPT — toggle **ai-memory ON per chat** under
Developer mode; force `search_memories` by name. Perplexity — turn connector ON
per thread; don't trust profile-only answers. Server logs remain the honest proof
when UIs show abbreviated snippets.

## Current phase

**Multi-LLM remote integrations (ADR 036) — complete (web + iPhone).** Infra
phases 0–4 live; phases 5–8 stubs. Next: Goal 3 (memory-bank snapshot + honest
graph report).

## Done this session (2026-06-10, ADR 036 iPhone mobile verify)

- Repo-health green at start (both repos clean, 0 ahead/behind).
- **Perplexity iPhone:** ai-memory connector inherited from web — visible and live.
- **ChatGPT iPhone:** ai-memory connector inherited from web — visible and live.
- **Claude iPhone:** Load all connectors ON; operator query triggered connector call.

## Last decisions

- **ADR 036 mobile inherit verified live (2026-06-10):** Perplexity + ChatGPT apps
  inherit web connectors on iPhone; Claude iPhone uses the same remote MCP connector
  registered on claude.ai web. Coverage table updated accordingly.
- **ADR 036 — one server, three platforms** (unchanged): all three on ADR 035 OAuth.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Next up: **Goal 3**
(memory-bank snapshot + honest graph report per ADR 032). Then infra hardening
(P1 supply chain, OpenClaw adapter gate, etc.).

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

> **RESUME HERE — Goal 3: memory-bank snapshot + honest graph report:**
> query the live Mem0 bank (memory count, sources, sample) and Neo4j node count
> (expect 0 per ADR 032); write a short honest report (no graph claims). Agent
> can run via SSH/API; no operator steps unless auth fails.

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
