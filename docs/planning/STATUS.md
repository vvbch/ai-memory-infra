# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**model-switch hardening: agent skills are now
harness-discoverable + the final all-repo handoff verifier landed** — Goal 1 of the
operator's 3-goal day; next is Goal 2: remote MCP endpoint for Claude on iPhone).
Repo-health green at session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly, reachable from Chrome and Cursor/Claude Code
(local MCP proxy). The conversational practice ("plan my day", "log this", "we decided X")
is wired.

**Why this session existed:** the operator's Claude credits exhaust today; the next
sessions run on **Cursor Composer 2.5**. Day plan (operator-set, 2026-06-10): (1) harden
interfaces/agents/skills so the model switch is safe; (2) verify all four surfaces
(Claude iPhone, Claude Chrome, ChatGPT Chrome, Cursor) can read/write mem0 — the iPhone
one needs a **new remote MCP HTTP endpoint**; (3) report how "the graph" is shaping
(reality: there is no graph yet — ADR 032; Neo4j is empty by design, reserved for
LifeGraph Phase 6).

**What changed this session (2026-06-10, Goal 1):**
- **Agent skills are now discoverable by any harness/model.** Canonical thin trigger
  pointers versioned in `skills/*/SKILL.md` (`memory-daily-driver`,
  `session-checkpoint`, `operator-action`), installed by
  `scripts/install_ide_hooks.py` to the workspace-root `.cursor/skills/` +
  `.claude/skills/` (Cursor skill discovery verified at cursor.com/docs/skills,
  2026-06-10; root-level placement deliberate — nested skills are dir-scoped, but
  Operator Assistant skills must fire on pure conversation). Registry §12.
- **Final all-repo handoff verifier landed (ADR 033 §4 #1; P1 governance item).**
  `scripts/handoff_verify.py` (+7 tests): every repo clean/pushed/in-sync (incl.
  **behind** check — stale Drive clone, tenet 11), STATUS.md is the checkpoint of
  record (no work committed after the last STATUS update), prints the latest pushed
  commit per repo as push evidence. Registry §11; wired into the `session-checkpoint`
  skill; `completion_gate.py` stays the deterministic turn-end floor.

**What you pay:** ~₹2,600/mo cloud box; full stack ≈ ₹3,800/mo landed; pause anytime with
`scripts/teardown.py`.

## Current phase

**Control plane hardened for the model switch (Goal 1 of the 2026-06-10 day plan done).**
Remaining ADR 033 enforcement-backlog gates (#2 operator-action routing, #4 DoD
trigger-table conformance) stay parked in `BACKLOG.md`. Infra phases 0–4 done/live;
phases 5–8 stubs; Phase 3-premise test still pending (see AGENTS.md build-phase status).

## Done this session (2026-06-10)

- **Skills made harness-discoverable** — `skills/*/SKILL.md` (3 thin trigger pointers
  to the canonical `docs/skills/*` specs + scripts); `install_ide_hooks.py` extended to
  install them to `<root>/.cursor/skills/` + `<root>/.claude/skills/`; installed + verified.
- **`scripts/handoff_verify.py`** (+ `tests/test_scripts/test_handoff_verify.py`, 7 tests)
  — final all-repo handoff verifier; closes the P1 governance backlog item / ADR 033 #1.
- **Registry + contract + backlog updated** — `docs/interfaces.md` §11 (final handoff)
  + §12 (agent skills); `contract/dod.yaml` dod-12 mechanism now includes the verifier
  (re-rendered); BACKLOG P1 governance item marked DONE; AGENTS.md working-model bullet
  notes the installer also installs skills.
- **Repo green:** ruff + mypy + 63 tests (90% cov) + pointer-purity + STATUS-shape gates pass.

## Last decisions

- **Skills install at the workspace root, not nested in the repo** — nested
  `.cursor/skills/` are auto-scoped to that directory's files; Operator Assistant
  skills must trigger on pure conversation. Same versioned-source → generated-adapter
  model as the hooks (ADR 030).
- **The handoff verifier is agent-run (TESTED), not a turn-end hook** — fetch/network
  on every turn would slow all turns; `completion_gate.py` remains the deterministic
  floor, `handoff_verify.py` adds behind-detection + STATUS-freshness + push evidence
  before final responses.

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Updated this session: P1
governance final-handoff verifier = DONE; skills discoverability = DONE. Remaining
ADR 033 gates: #2 operator-action format routing, #4 DoD trigger-table conformance.
Other open items unchanged: glob-scoped helper rules `10`/`20` fate, graph-source
one-way-door decision (ADR 032 §4), supply-chain pinning/lockfile,
`MEM0_DEFAULT_LLM_MODEL` boot-assert, droplet OS patch/reboot cadence.

## Open blockers / risks

- **OpenClaw adapter gate (ADR 028):** verify `source`/`agent_id` propagation before enabling writes.
- **`gpt-4.1-nano` silent fallback** if `MEM0_DEFAULT_LLM_MODEL` unset on the droplet — keep it set.
- **Operator income change risk (end-June 2026):** spend must stay pause-able (`scripts/teardown.py`).
- **Cosmetic:** bcrypt `$` Compose warning; apex `chandrav.dev` TLS unverified from Windows.

## Environment notes

- Use `working_directory` param, not raw `cd` (Drive path has spaces/parens). Windows
  PowerShell 5.1; git push auth cached. Repos: `github.com/vvbch/ai-memory-infra(-private)`,
  `ai-memory-extension`.
- **gitleaks PATH:** refresh in the committing shell:
  `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`.
- **Contract is generated:** edit `contract/*.yaml`, then run `python scripts/render_contract.py`
  and commit — never hand-edit the text between `<!-- generated:* -->` fences in
  `AGENTS.md`/`docs/tenets.md` (the `--check` gate will block it).
- **SSH:** key passphrase in Bitwarden; **ssh-agent is not auto-loaded in agent shells** —
  SSH to the droplet (`root@168.144.145.29`) is operator-gated this way. Stack in
  `/opt/ai-memory-infra/infra`; mem0 source `/opt/mem0-src`.
- **Droplet repo sync:** `git fetch && git diff --stat origin/main` then `git reset --hard origin/main`.
- Nightly backup (18:30 UTC) + monthly restore drill (1st, 19:30 UTC), watched by healthchecks.io.
  Drill canary `user_id=drill-canary` is planted — leave it.

## Next action

> **RESUME HERE.** Goal 1 of the operator's 2026-06-10 day plan is done. Next is
> **Goal 2: make all four surfaces read/write mem0.** Three already work (Cursor via
> local MCP proxy; Claude + ChatGPT on Chrome desktop via the extension) — verify each
> with a live round-trip. The build item is **Claude on iPhone**: a remote MCP
> (Streamable HTTP) endpoint on the droplet behind Caddy with auth, registered as a
> Claude connector (operator confirmed his paid Claude subscription continues — only
> credits exhaust). Auth design for a public MCP endpoint is **one-way-door class**:
> web-verify Claude's current remote-connector requirements (tenet 8), write/extend an
> ADR before exposing anything. Needs operator SSH unlock for droplet work.
>
> After Goal 2 (or ~9pm IST): **Goal 3 (light)** — memory-bank snapshot (counts by
> type/source) + the honest graph report (empty by design; the unlock is the ADR 032 §4
> decision).

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
