# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (global vs workspace rule conflict resolved in control
plane). Repo-health green; committing+pushing.

## Plain English — where we are (resume here)

**The product:** self-hosted memory at `https://memory.chandrav.dev/docs`, backed
up nightly + restore-drilled monthly. **ADR 036 is complete** on every targeted
surface (Claude, Perplexity, ChatGPT — web + iPhone). One server
(`https://mcp.chandrav.dev/`), one OAuth story (ADR 035).

**Curated bank (`user_id=chandrav`):** ~21 portfolio/MCP-seeded facts after
cleanup. **Legacy extension silo (`chrome-extension-user`): 47 memories deleted**
(2026-06-10). **Extension auto-capture is off by policy** until opt-in guardrails
land; MCP is the primary write surface. **Neo4j node count = 0** (ADR 032).

**What's next:** build track — ADR 028/029 write-path hardening, then phases 5–8.
Premise/usefulness test parked until builds land (operator 2026-06-10).

## Current phase

**Infra phases 0–4 live; ADR 036 + ADR 037 closed.** Phases 5–8 stubs — **active
build track**. Premise test parked post-build.

## Done this session (2026-06-10)

- **Rule conflict COE:** `docs/coe/2026-06-10-global-workspace-rule-conflict.md` —
  root cause = global Cursor user rule vs `AGENTS.md` standing authorization;
  operator locked workspace-wins + park-still-commits + push-with-commit.
- **`AGENTS.md`:** park semantics + rule-conflict protocol (ask once, then fix
  control plane same session).
- **Open operator step:** replace global Cursor user rule text per COE § Global rule
  replacement (Settings → Rules).

## Last decisions

- **Workspace rules trump global user rules** for ai-memory (tenet 2).
- **Park** = stop new work; still checkpoint + commit+push completed changes.
- **Commit+push** is standing authorization for reversible work — no permission ask.
- **On rule conflict:** ask once → workspace wins → fix all layers same session.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Top candidates: ADR 028
`source` tagging on writes + OpenClaw adapter gate; weekly compaction review;
remaining metrics seed via `bulk_seed_importer.py`; MCP droplet redeploy for ADR 037
tools.

## Open blockers / risks

- **Global Cursor user rule not yet updated in Settings** — copy from COE
  `2026-06-10-global-workspace-rule-conflict.md` § Global rule replacement.
- **MCP droplet behind git** — ADR 037 delete/update tools not on live connector
  until redeploy.
- **ChatGPT developer mode is beta** — OpenAI can re-gate it.
- **ChatGPT Plus read-only custom MCP** — write tools may be disabled on Plus.
- **OpenClaw adapter gate (ADR 028):** verify `source`/`agent_id` before enabling writes.
- **`gpt-4.1-nano` silent fallback** if `MEM0_DEFAULT_LLM_MODEL` unset on the droplet.

## Environment notes

- Use `working_directory` param, not raw `cd` (Drive path has spaces/parens). Windows
  PowerShell 5.1 (no `&&`); git push auth cached.
- **SSH:** droplet `root@168.144.145.29`; stack `/opt/ai-memory-infra/infra`.
- **Token handling:** `MCP_CONNECTOR_BEARER_TOKEN` in Bitwarden — never print it.

## Next action

> **RESUME HERE — ADR 028 write-path: `source` metadata on Mem0 writes:**
> audit extension + MCP proxy + OpenClaw adapter for `metadata.source` propagation;
> patch if missing; add/extend tests. OpenClaw adapter gate: verify before enabling
> writes. Agent-led; no operator steps unless a live write probe is needed.

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
