# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**ADR 033 implemented: the operating contract is now a
structured single-source — `contract/*.yaml` renders the AGENTS.md/tenets.md prose +
a coverage report; `--check` gates pre-commit + CI; first enforcement-backlog gate
(pointer-file purity) landed**). Repo-health green at session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly, reachable from Chrome and Cursor/Claude Code
(local MCP proxy). The conversational practice ("plan my day", "log this", "we decided X")
is wired.

**Why this session existed:** the operator chose order **(A) then (B)**. This session did
**(A): implement ADR 033** — make the operating contract model-agnostic. Until now the
contract was ~900 lines of *prose* a model had to read and choose to follow, so adherence
varied by model (Opus 4.8 vs Composer 2.5). Now the high-value rules are **structured data
+ mechanisms**, and the prose is *generated from* that data.

**What changed this session (2026-06-10):**
- **The contract is now a structured single-source.** `contract/tenets.yaml` (18),
  `contract/practices.yaml` (8), `contract/dod.yaml` (12 DoD rows) hold each rule
  **verbatim** plus an honest `enforcement.status` (enforced / tested / prose) + mechanism
  + gate_id. `scripts/render_contract.py` (TDD) **generates** the fenced sections of
  `AGENTS.md` + `docs/tenets.md` and writes `docs/reports/contract-coverage.md`.
- **The lift was proven faithful.** Rendered output is **byte-equal** to the old
  hand-authored prose — the only diff to AGENTS.md/tenets.md was the inserted
  `<!-- generated:* -->` fence comments. An in-sync test pins it forever.
- **Drift is now impossible by construction.** `render_contract.py --check` is wired into
  pre-commit (gate 4) + CI: if anyone edits the prose without editing the YAML, the commit
  fails.
- **First enforcement-backlog gate landed (ADR 033 §4 #3): pointer-file purity.**
  `scripts/check_pointer_purity.py` (pre-commit gate 5 + CI) fails if an `alwaysApply`
  Cursor rule / `CLAUDE.md` drifts into carrying tenets/rules (closes COE
  2026-06-07-cursor-rule-drift). The coverage report now reads **38 rules — 11 enforced,
  0 tested, 27 prose**: the model-dependent surface is finally *measured* and shrinking.

**What you pay:** ~₹2,600/mo cloud box; full stack ≈ ₹3,800/mo landed; pause anytime with
`scripts/teardown.py`.

## Current phase

**Control plane further hardened (ADR 033 done). (A) is substantially complete** — the
structured contract + renderer + two gates (render-freshness, pointer-purity) are live; the
remaining enforcement-backlog gates are parked in `BACKLOG.md`. **Next track is (B) Phase 3
premise test** (the operator's "then go back to phase 3"). Infra phases 0–4 are done/live;
phases 5–8 are stubs (see AGENTS.md build-phase status).

## Done this session (2026-06-10)

- **ADR 033 implemented** (migration steps 1–5): `contract/*.yaml` (verbatim lift,
  enforcement.status per rule) + `scripts/render_contract.py` (+ tests) generating the
  fenced AGENTS.md/tenets.md sections + `docs/reports/contract-coverage.md`; byte-equal
  no-op diff proved the lift faithful; `--check` wired into pre-commit + CI; PyYAML added
  to deps; ADR 033 → Implemented with a Propagation note.
- **Pointer-file purity gate** (`scripts/check_pointer_purity.py`, + tests) — ADR 033 §4
  enforcement-backlog item #3 / ADR 018's deferred guard; pre-commit gate 5 + CI; promotes
  DoD row `dod-05` prose → enforced.
- **Registry + backlog updated** — `docs/interfaces.md` §9 (operating contract) + §10
  (pointer purity); `BACKLOG.md` Workstream C marked done where landed; new parked item:
  decide the fate of glob-scoped helper rules `10`/`20`.
- **Repo green:** ruff + mypy + 56 tests (90% cov) + all five pre-commit gates pass.

## Last decisions

- **Operating contract is a generated view of `contract/*.yaml` (ADR 033 — Implemented).**
  Prose can no longer drift from the structured source; the prose-only (model-dependent)
  surface is measured by `contract-coverage.md` and shrinks deliberately via the
  enforcement backlog.
- **Pointer-purity gate is scoped to contractually-pure pointers** (`alwaysApply` rules +
  `CLAUDE.md`), not the glob-scoped helper rules — whose fate is a separate parked decision
  (avoids unilaterally deleting curated content, tenet 17).

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Updated this session: Workstream C
structured single-source = DONE; enforcement-backlog gate #3 (pointer purity) = DONE;
**remaining ADR 033 gates** still open — #1 final-response/handoff validator (already a
promoted P1 governance item), #2 operator-action format routing, #4 DoD trigger-table
conformance. New parked item: decide the fate of glob-scoped helper rules `10`/`20`. Other
open items unchanged: graph-source one-way-door decision (ADR 032 §4), supply-chain
pinning/lockfile, `MEM0_DEFAULT_LLM_MODEL` boot-assert, droplet OS patch/reboot cadence.

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

> **RESUME HERE.** (A) ADR 033 is implemented and committed; its remaining enforcement-backlog
> gates are parked in `BACKLOG.md` (do them later, one per session). Per the operator's chosen
> order **(A) then (B)**, the next track is:
>
> **(B) Phase 3 — premise test.** Capture your REAL open items + 1–2 recruiter reachouts
> (conversational, one at a time per AGENTS.md § Memory Daily Driver), run "plan my day" for
> a few days, judge genuine utility. Operator-facing; expect conversation, not code. This is
> what COE 2026-06-10-delayed-memory-buildout urges before more buildout.
>
> *(Or, if you'd rather keep hardening the control plane first, pick the next ADR 033
> enforcement-backlog gate — #1 final-response/handoff validator is the highest-value.)*

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
