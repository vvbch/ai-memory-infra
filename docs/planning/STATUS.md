# STATUS — resumable session snapshot

> **Overwritten each session — overwrite means replace** (tenet 16; COE
> 2026-06-10-status-snapshot-log-drift; shape machine-enforced by
> `scripts/check_status_snapshot.py` in pre-commit + CI). **Read this first to
> resume.** History lives in the private `BUILD-LOG.md`; reasoning in
> `docs/decisions/`; working model + teaching prefs in `AGENTS.md`.

**Last updated:** 2026-06-10 (**control-plane hardening session: secrets catalog +
hygiene, HLD-drift fix (Neo4j), LLD design-template + interface registry, maturity
honesty, and the structured-operating-contract design (ADR 033, model-agnostic)**).
Repo-health green at session start.

## Plain English — where we are (resume here)

**The product:** your self-hosted memory server is live (`https://memory.chandrav.dev/docs`),
backed up nightly + restore-drilled monthly, reachable from Chrome and Cursor/Claude Code
(local MCP proxy). The conversational practice ("plan my day", "log this", "we decided X")
is wired.

**Why this session existed:** you noticed that when you switch models (Opus 4.8 high vs
Composer 2.5), adherence to tenets/guidelines/operating-style varies a lot — because the
contract is ~900 lines of *prose* the model must read and choose to follow. You asked to
(1) make the buildout model/reasoning-agnostic, (2) check we manage scope/architecture/
HLD/LLD well, and (3) confirm secrets are catalogued in the private repo (purpose + where
they live, no values). We did all three as control-plane hardening, **before** going back
to Phase 3.

**What changed this session (2026-06-10):**
- **Secrets are now catalogued.** New `ai-memory-infra-private/docs/security/secrets-catalog.md`
  lists every secret (no values) — purpose, where it lives (console URL / Bitwarden item),
  rotation, blast radius. AGENTS.md DoD now requires a catalog row whenever a secret is
  created/rotated. Two hygiene snags flagged + the working-copy scrubbed.
- **HLD drift fixed (ADR 032).** The "Neo4j dual namespace / Mem0 auto-graph" claim was
  wrong (deployed Mem0 ships no graph store, writes nothing to Neo4j). Corrected everywhere;
  Neo4j is now honestly described as reserved-for-LifeGraph (Phase 6).
- **LLD/HLD discipline is now systematic.** Added a design-doc template
  (`docs/design/TEMPLATE.md`) + a DoD rule (design doc before code), and an interface/
  contract registry (`docs/interfaces.md`) with enforcement status per contract.
- **Maturity honesty.** Reworded AGENTS.md engineering practices to `[in place]` vs
  `[target]`, annotated build-phase reality, deleted 4 red stub workflows, fixed the
  extension's stale README default + rewrote its privacy policy for the self-hosted reality.
- **Model-agnostic direction decided (Option B), designed, handed off.** ADR 033 specs a
  *structured single-source contract* (`contract/*.yaml` -> renders AGENTS.md + an
  enforcement-coverage report; gates read the same ids). Implementation is the next
  session's one task.

**What you pay:** ~₹2,600/mo cloud box; full stack ≈ ₹3,800/mo landed; pause anytime with
`scripts/teardown.py`.

## Current phase

**Control plane hardened (this session). Two candidate next tracks, operator picks order:**
(A) implement ADR 033 structured contract (per the approved plan, next session's single
task); (B) Phase 3 premise test (your originally-stated "then go back to phase 3", and what
COE 2026-06-10-delayed-memory-buildout urges first). Infra phases 0-4 are done/live; phases
5-8 are stubs (see AGENTS.md build-phase status).

## Done this session (2026-06-10)

- **Secrets catalog** — `ai-memory-infra-private/docs/security/secrets-catalog.md` (no
  values): full inventory with purpose/location/rotation/blast-radius; AGENTS.md custody +
  DoD rows now require a catalog row on every secret create/rotate.
- **Secret hygiene** — redacted the partial basic-auth password prefix from the private
  `BUILD-LOG.md` working copy; documented the exposure + the `.env` plaintext block as open
  hygiene items in the catalog. **Operator action still needed** (see blockers): rotate the
  Caddy basic-auth password + delete the `.env` block (closes P1 burn-in).
- **HLD drift (ADR 032)** — corrected the Neo4j/Mem0-graph overclaim in `architecture.md`,
  `AGENTS.md`, `README.md`, `scaffold.py`, compose + Dockerfile comments, ADR 005 note,
  setup-prompt banner. Live `MATCH (n) count` confirm deferred to next operator SSH session.
- **LLD mechanism** — `docs/design/TEMPLATE.md` + DoD trigger "design doc before code".
- **Interface registry** — `docs/interfaces.md` (8 contracts, enforcement status).
- **Maturity honesty** — practices `[in place]`/`[target]`; build-phase reality; deleted
  `cd.yml`/`eval-suite.yml`/`backup-verify.yml`/`docker-build.yml` stubs; extension
  README/privacy fixed.
- **ADR 033** — structured operating contract design + enforcement backlog; Option B chosen,
  implementation handed to next session.

## Last decisions

- **Operating contract becomes structured single-source (ADR 033, Option B).** Prose is
  generated from `contract/*.yaml`; gates read the same ids; coverage report makes the
  model-dependent surface visible and shrinkable. Build deferred to next session (tenet 16).
- **Neo4j is reserved for LifeGraph, not a live Mem0 graph (ADR 032).** Corrects ADR 005
  premise #1. Graph-source decision (LifeGraph-only vs graph-capable Mem0) is a pre-Phase-6
  one-way door.
- **Secrets get a private catalog (index), Bitwarden stays the value store.** Creating/
  rotating a secret is not done until it's in both.
- **Design doc before code** for any new phase/module/capability (HLD+LLD template).

## Backlog (parked work)

Prioritized backlog in **`docs/planning/BACKLOG.md`**. Updated this session: the
`[docs-drift]` Neo4j P1 doc-fix is done (ADR 032) — remaining is the live count confirm +
the graph-source one-way-door decision. New: **Workstream C enforcement backlog** (ADR 033)
— final-response/handoff validator (promoted P1 governance), operator-action gate wiring,
pointer-purity gate, DoD-trigger conformance. Still open: `.env` plaintext strip (now
unblocked by the rotation action), supply-chain pinning/lockfile, `MEM0_DEFAULT_LLM_MODEL`
boot-assert.

## Open blockers / risks

- **Operator action — basic-auth password rotation (this session's one handoff item):**
  a partial prefix of the admin-UI/basic-auth password sits in private `BUILD-LOG.md`
  git history. Recommended fix (reversible; neutralizes the leaked prefix, no history
  rewrite): rotate it. Needs a live droplet change + Bitwarden write. **One step:** when
  ready, I'll walk you through `caddy hash-password` → update `infra/.env` on the droplet →
  reload Caddy → store the new plaintext in Bitwarden → I tick the catalog. The same SSH
  session can run the Neo4j `MATCH (n) RETURN count(n)` confirm + delete the `.env` block.
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
- **SSH:** key passphrase in Bitwarden; **ssh-agent is not auto-loaded in agent shells** —
  SSH to the droplet (`root@168.144.145.29`) is operator-gated this way. Stack in
  `/opt/ai-memory-infra/infra`; mem0 source `/opt/mem0-src`.
- **Droplet repo sync:** `git fetch && git diff --stat origin/main` then `git reset --hard origin/main`.
- Nightly backup (18:30 UTC) + monthly restore drill (1st, 19:30 UTC), watched by healthchecks.io.
  Drill canary `user_id=drill-canary` is planted — leave it.

## Next action

> **RESUME HERE.** Control plane is hardened + committed. Pick the track:
>
> **(A) Implement ADR 033 — structured operating contract (the approved next task).**
> Lift the 18 tenets + DoD table + practices into `contract/*.yaml` (verbatim) with an
> `enforcement.status` per rule; write `scripts/render_contract.py` (TDD) to generate the
> fenced AGENTS.md/tenets.md sections + `docs/reports/contract-coverage.md`; wire `--check`
> into pre-commit + CI; then pick the top 1-2 enforcement-backlog gates. See ADR 033 §
> "Migration steps".
>
> **(B) Phase 3 — premise test.** Capture your REAL open items + 1-2 recruiter reachouts
> (conversational, one at a time per AGENTS.md § Memory Daily Driver), run "plan my day"
> for a few days, judge genuine utility. Operator-facing; expect conversation, not code.
>
> Recommended: (A) is the directed plan and removes the model-drift pain you raised; (B)
> is what the delayed-buildout COE urges and what you said you'd "go back to". Your call.
> Also pending: the basic-auth rotation handoff item (Open blockers).

**How to talk to the next agent:** type **`/resume`** in a new chat — or paste:

```
Resume ai-memory-infra — read docs/planning/STATUS.md (Plain English + Next action) and AGENTS.md, run repo-health, then do the Next action. Concierge mode: one step at a time, plain English.
```
