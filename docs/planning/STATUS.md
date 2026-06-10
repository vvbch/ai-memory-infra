# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (Goal 3 done — memory-bank snapshot + honest graph
report; ADR 036 iPhone mobile verified earlier this session). Repo-health green;
committed+pushed.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **ADR 036 is complete** on every targeted
surface (Claude, Perplexity, ChatGPT — web + iPhone). One server
(`https://mcp.chandrav.dev/`), one OAuth story (ADR 035). Chrome extension still
auto-captures on desktop.

**Goal 3 snapshot (this session):** **56 memories** in Mem0 (mostly extension
captures under `chrome-extension-user`; only 3/56 have explicit `source` metadata
yet). **Neo4j node count = 0** — no graph in production today (ADR 032 honest
truth). Full report: `docs/reports/memory-bank-snapshot-2026-06-10.md`.

**What's next:** memory contract hardening — tag `source`/`agent_id` on writes
(ADR 028) and verify the OpenClaw adapter before enabling it.

## Current phase

**Infra phases 0–4 live; ADR 036 closed.** Phases 5–8 stubs. Active work shifts to
memory-model implementation (ADR 028/029) and P1 hardening from BACKLOG.

## Done this session (2026-06-10)

- **ADR 036 iPhone:** Perplexity + ChatGPT connectors inherited from web; Claude
  iPhone connector call confirmed.
- **Goal 3:** live Mem0 snapshot (56 memories, source breakdown) + Neo4j count
  (0 nodes); honest report written.

## Last decisions

- **ADR 036 mobile inherit verified live (2026-06-10):** all three platforms on iPhone.
- **Graph honesty (ADR 032 reaffirmed):** Neo4j has zero nodes; Mem0 does not write
  a graph at the pinned deployment — report documents this explicitly.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Top candidates: ADR 028
`source` tagging on writes + OpenClaw adapter gate; P1 supply-chain pinning;
ADR 032 graph-source one-way-door (LifeGraph-only vs Mem0 graph).

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
  *user* env vars, and both `.env` files; never print it.
- **OAuth endpoint:** consent page `https://mcp.chandrav.dev/consent` (password = the
  connector secret); state file on the `mcp_oauth_state` Docker volume.

## Next action

> **RESUME HERE — ADR 028 write-path: `source` metadata on Mem0 writes:**
> audit extension + MCP proxy + OpenClaw adapter for `metadata.source` propagation;
> patch if missing; add/extend tests. OpenClaw adapter gate: verify before enabling
> writes. Agent-led; no operator steps unless a live write probe is needed.

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
