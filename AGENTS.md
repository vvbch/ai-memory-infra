# AGENTS.md — ai-memory-infra

> Canonical agent context for this repo. Editor-agnostic by design: read by
> Cursor (`.cursor/rules` point here), VS Code / Copilot, and Claude Code
> (`CLAUDE.md` points here). **Edit this file, not the pointers.**
>
> **▶ Resuming / "what's next?" → read `docs/planning/STATUS.md` first** (current
> phase, last decisions, blockers, next action). Then `docs/setup.md` for the
> operational walkthrough.

## What we're building

Self-hosted, cross-platform AI memory infrastructure with a knowledge graph —
a persistent memory layer under Claude, ChatGPT, Gemini, and DeepSeek, on any
device. The public repo is platform infrastructure and a LifeGraph POC only
(tenet 5); it must read as production-grade infra to any visitor.

## Private agent context

Operator profile, collaboration preferences, venture tag definitions, deployment-
specific URLs/`user_id`, and interview/portfolio narrative live in the private
companion repo **`ai-memory-infra-private`**:

- `OPERATOR.md` — who the operator is, how to collaborate, live env overrides
- `ventures.md` — venture metadata vocabulary and import heuristics for real data
- `docs/interview_packet.md` — portfolio narrative (never duplicated here)

Agents with private-repo access read those files after this one.

## Operator collaboration (generic patterns)

- **Pre-delegation gate (COE 2026-06-10):** before delegating any action to the
  operator, verify it cannot be performed via CLI/API (`gh`, `curl`, shell, MCP).
  Delegate only genuinely operator-exclusive actions (credentials entry, consent,
  account creation requiring PII).
- **Operator-delegated action format:** when delegation is required, give exactly
  one action with: (1) plain-language purpose, (2) exact UI path or command,
  (3) visible success condition, and (4) "tell me what you see."
- **Credential handoff via clipboard:** when a secret lives in the password manager,
  the operator copies; after **"copied"** / **"in clipboard"**, the agent runs the
  handoff script (`scripts/ssh_unlock.py`; spec
  `docs/skills/operator-assistant-credential-handoff.md`). Never echo clipboard
  contents.
- **Persist agent credentials on the machine** (ssh-agent, GCM, `gh` keyring, user
  env vars like `AI_MEMORY_API_KEY`, gitignored tfvars). Password manager remains
  master copy (ADR 017).
- **No resume prompt while waiting on the operator** in the same active flow.
- **Web-verify volatile UI steps** before giving click-by-click instructions.
- **Research discipline:** web-verify volatile facts before baking them in; state
  the source (tenet 8).

## Tenets (non-negotiable — see docs/tenets.md)

<!-- Generated from contract/tenets.yaml by scripts/render_contract.py (ADR 033) — edit the YAML, not the text between the fences. -->
<!-- generated:agents-tenets start -->
1. **Everything versioned.** Every artifact — code, configs, scaffolding
   scripts, decisions, the planning doc, these instructions — lives in source
   control. We learn over time from history. Nothing important exists only in
   a chat window or one machine.
2. **Portable / editor-agnostic.** Cursor must be swappable for VS Code (or
   any agent) tomorrow with zero loss. Canonical context in `AGENTS.md`;
   editor-specific files are thin pointers. No tool lock-in.
3. **Cross-platform out of the box.** Mac and Windows both work without
   special setup. Prefer Python over shell for tooling; containers normalize
   the runtime; no symlinks (Windows-hostile); document OS-specific commands
   where they differ.
4. **Graceful degradation.** VPS down ⇒ every LLM still works with its own
   memory. Zero hard dependency.
5. **No firm IP in this repo.** Public platform + LifeGraph POC only. Trading
   / social / RIA logic lives in separate private repos that plug in via REST.
6. **Cost-conscious, not cost-blind.** Default to cheaper, justify every
   recurring rupee, annotate `(~₹X/mo)`. Justified spend is OK in seed stage.
   `(~₹X/mo)` annotations are vendor **list price**; the operator's **landed cost
   ≈ list × 1.3** (+18% GST, +~4–6% forex) — budget on landed, not sticker. Actual
   ₹ outflow lives in the private operator financial ledger.
7. **Fewer moving parts.** For a solo project, simplicity wins; add a
   container/provider/dep only when its value exceeds lifetime maintenance.
8. **Verify in the right tier.** Web/docs/repo for dated facts → deep research
   for trade-offs → internal knowledge last. Repo source beats blogs.
9. **One provider across pipeline stages** (extraction + embeddings) unless the
   cost/capability gap is vast; keep it swappable, justify splits in an ADR.
10. **Single source of truth; no instruction drift.** Restated facts/decisions
    across docs must agree — a change in one triggers the others (Definition of
    Done below). Does NOT govern Mem0 dynamic memory (dedup-reconciled, not synced).
11. **Drive-synced repos: remote is truth, integrity is checked.** Both repos
    (incl. `.git`) live under Google Drive Mirror — deliberate (off-machine
    backup) but risky (Drive can corrupt `.git`). Mitigation contract: GitHub is
    truth; commit+push every session (never batch); run `check-repo-health` at
    session start + pre-commit + daily; on any red check **re-clone, don't
    repair**; never commit large firm artifacts (one-way door). See ADR 015.
    **The commit+push trigger is harness-enforced, not memory-based:** editor-
    agnostic logic in `scripts/completion_gate.py` (ADR 027; placement ADR 030),
    invoked by a harness turn-end adapter (Cursor `stop` / Claude Code `Stop`),
    refuses to let a turn end with a dirty/unpushed repo, for **any** model — the
    prose gate below is the happy path, the hook is the hard layer.
12. **Vendors are deliberated, documented, and reversible.** No external
    dependency (registrar, cloud, DNS, SaaS, model API, paid tool) is adopted
    *suddenly*. Before committing, weigh in an ADR: total cost **incl. exit cost**,
    portability/lock-in, reliability & track record, company viability (financials/
    longevity), and ecosystem/standards. Recommend a default but let the operator
    decide; every adoption ships with a documented exit (`docs/decommission.md`).
13. **Stay on the critical path; diverge only deliberately.** Each session has one
    goal (STATUS "Next action"); work serves it until done or explicitly re-scoped.
    Guard against scope creep / gold-plating / premature depth / yak-shaving /
    tangents. Match depth to stakes (tenet 8); **park** good-but-off-goal ideas in
    `STATUS.md`, don't chase them (and never lose them). The agent escalates only as
    needed: **caution → advise → (rarely) stop & redirect.** Eyes-open operator
    overrides are fine; *accidental* drift is not.
14. **Errors are mechanisms — run a COE, fix the control plane first.** Treat any
    tenet/rule violation, defect, incident, or agent non-adherence as a chance to
    improve the *system* (Amazon "Correction of Errors"). Beyond-trivial issues get
    a structured, **blameless** COE in `docs/coe/` (impact · timeline · detection ·
    industry benchmark · 5-whys to a systemic root cause · Prevent/Detect/Mitigate
    actions w/ owner+date).
    **Fix the control plane (rule/spec/mechanism) before the data plane (instance)**;
    capture the lesson in a tenet/ADR (+ private interview packet if portfolio-facing). Depth ∝ blast radius.
15. **Fixed, capped cost beats variable — even at a mild premium.** Prefer
    predictable flat-rate pricing over usage-based/on-demand, even when on-demand is
    mildly cheaper: a known bill can't spiral. Default to flat-rate resources; put a
    **hard spend cap + billing alerts** on anything that must be usage-based (LLM
    APIs); set billing alerts on every paying account. Diverge only if the saving is
    *vast*, documented in an ADR, and still capped. Sharpens tenet 6.
16. **Stateless, disposable sessions — checkpoint to the repo, don't accumulate
    context.** One task per session (the STATUS "Next action"), single-shot — not a
    marathon thread. State lives in **files, not chat**: checkpoint `STATUS.md` after
    each logical step, and emit a copy-paste Resume prompt only after that checkpoint is
    current so a fresh chat resumes with zero loss. *Why:* a long-lived stateful session re-sends its whole
    transcript each turn → ~quadratic token cost (*context-window amplification*); one
    half-day session burned a month's Cursor credits. Bounded sessions cap that blast
    radius (agent-tooling analog of tenet 15). Twelve-Factor stateless-process + backing
    store. See COE 2026-06-08.
17. **Minimize operator cognitive load — act on reversible (two-way-door) decisions;
    deliberate only on one-way doors.** For easily-reversible work the agent **just does it
    and reports the call** (commit every session — never leave changes hanging; pick
    reasonable defaults; proceed); a clean `git revert` is the safety net. Do **not** add
    "operator will inspect/commit" gates for routine code: the operator reviews decisions
    and outcomes, while the agent owns reversible implementation, verification, and commits.
    Reserve the operator's attention for **one-way doors** (spend, lock-in, deletion, scope change —
    tenet 12/15 class) and genuine matters of taste. **Classify by the irreversibility of
    the *effect*, not the code:** reversible code (a script/config a `git revert` removes)
    can still encode an *irreversible effect* — destructive restore, delete-on-prune
    retention, `DROP`, TTL/expiry, `--force` push. When code destroys or overwrites data
    (or sets the policy that will), the data-loss semantics are a **one-way door needing
    sign-off**, even though the diff reverts trivially. Test: "if this runs, can I get the
    data back?", not "can I delete the script?". **Bias for action, bounded by
    reversibility (of the effect).** Sharpens "lead, don't quiz"; attention-corollary of
    tenet 7. (Effect-vs-code sharpening: ADR 023.)
18. **Burn-in before hardening — defer non-critical cleanup to a tracked post-launch
    pass.** When a system first goes live, keep a few **convenience/diagnostic
    affordances** (a cred note kept handy, verbose logging, a looser setting) that ease
    the first ~week of real use, then run a **deliberate cleanup/hardening pass** once
    usage proves it stable. The deferral must be **explicit, tracked, and time-boxed** —
    parked in `BACKLOG.md` with a "after ~1 week of full usage" trigger (tenet 13), never
    left to memory. **Never defer an active risk or a one-way door** (secrets reaching git
    history, data loss, public exposure) — those are fixed *now*; burn-in covers only
    reversible convenience/cosmetic debt. Same reversibility test as tenet 17, applied to
    cleanup *timing*.
19. **Vector store ≠ dedup; timeout ≠ failure on async memory writes.** pgvector
    stores embeddings for *retrieval* — it does not deduplicate. Write-time dedup is
    Mem0's LLM ADD/UPDATE pipeline; offline near-dupes are handled by
    `scripts/memory_compaction.py` (review-first). Bulk/scripted writes must use
    deterministic `metadata.external_id` (`scripts/bulk_seed_importer.py`). On client
    timeout during `infer=True` extraction, **verify-then-skip** — never reword and
    retry (ADR 037).
20. **Event time, namespace, and inline entity qualifiers.** Store `event_date` (not
    just Mem0 `created_at`) on every fact; retrieval recency uses `max(event_date)`.
    Use flat `namespace` tags (`public` | `sensitive`) on one `user_id`. Qualify
    colliding entity names inline in fact text. Gate bulk load with
    `scripts/acceptance_probe.py` (ADR 037).
<!-- generated:agents-tenets end -->

## Architecture (summary)

Caddy (auto-HTTPS) → Mem0 (FastAPI REST) over PostgreSQL/pgvector, plus
Neo4j (running + backed up; LifeGraph POC uses in-memory `GraphStore` today —
live Neo4j seed is a follow-up ops step, ADR 032). A local stdio MCP proxy
(ADR 025) lets Claude Code, Cursor, and VS Code call the REST API. Remote HTTP
MCP + OAuth for mobile connectors (ADR 034/035). Prometheus + Grafana for
observability. Reach: Chrome extension + local MCP proxy; remote MCP for Claude
mobile and other OAuth-capable connectors.
Models: single OpenAI provider — `gpt-5-mini` + `text-embedding-3-small`
(swappable, ADR 013). Full diagram: `docs/architecture.md`.

## Engineering practices (standards — with honest status)

<!-- Generated from contract/practices.yaml by scripts/render_contract.py (ADR 033) — edit the YAML, not the text between the fences. -->
<!-- generated:agents-practices start -->
These are the project's engineering standards. Each is tagged **[in place]** (live
and enforced today) or **[target — Phase N]** (the standard we hold ourselves to,
not yet built). Keep these tags honest — a claim outrunning reality is itself drift
(tenet 10; baseline scan 2026-06-10).

- **IaC** — **[in place]** Terraform for all cloud infra; no manual console clicks.
- **TDD** — **[in place]** tests before implementation; 80%+ coverage gate on `src/`
  (enforced in CI).
- **CI** — **[in place]** on every push/PR: ruff + mypy + pytest + the contract/
  STATUS gates (`.github/workflows/ci.yml`). (Tests run against fakes, not yet a
  full ephemeral Docker stack — **[target]**.)
- **CD** — **[target — Phase 1/ops]** push-to-main SSH deploy → health check →
  rollback. **Today deploys are manual SSH** (`make deploy`); no `cd.yml` yet.
- **Eval framework** — **partly [in place], partly [target — Phase 7/9]**. In
  place: retrieval/extraction/categorization metrics, guardrails, starter synthetic
  gold data in `src/eval/`, **blocking CI regression gate** on synthetic gold
  (`scripts/run_eval_gate.py`, ADR 007 thresholds). Target: live-stack eval,
  expanded gold datasets, full cross-LLM extraction matrix (ADR 007/014).
- **Security** — **partly [in place], partly [target — Phase 9/security]**. In
  place: HTTPS (Caddy), an admin `X-API-Key` + JWT support on the API, basic auth on
  admin UIs, least-privilege backup key, gitleaks. Target (not yet built): PII filter
  (Aadhaar/PAN/keys), CORS allowlist, rate limiting. The OSS stack ships none of the
  target items — they are explicitly TODO, not done. See `docs/interfaces.md` §5.
- **ADRs** — **[in place]** in `docs/decisions/` for every major choice.
- **Supply chain** — **[target]** lockfile + dependency pinning + action SHA-pinning
  + Dependabot are not yet in place (BACKLOG; baseline scan gap).
<!-- generated:agents-practices end -->

## Build phases (with reality status)

Status as of 2026-06-11 — keep honest (COE 2026-06-10-delayed-memory-buildout):

- **0 scaffold + accounts** — ✅ done
- **1 IaC (Terraform/Compose/Caddy)** — ✅ done (deploy is manual SSH; no CD yet)
- **2 backup/restore + drills** — ✅ done
- **3 Chrome extension fork** — ✅ live
- **4 Claude + Cursor/VS Code MCP** — ✅ done (local stdio proxy + remote HTTP MCP)
- **5 migration (TDD)** — ✅ core pipeline (`src/migration/`); live bulk load pending
- **6 LifeGraph (TDD)** — ✅ in-memory POC (`src/life_graph/`); live Neo4j seed **[target]**
- **7 eval framework (TDD)** — ✅ starter metrics + synthetic gold; CI gate on synthetic gold ✅; live-stack eval **[target]**
- **8 observability** — ✅ metrics, drift, alerts, health checker
- **9 docs/polish** — ⬜ ongoing

## Conventions

- Python 3.12, `pyproject.toml` is source of truth (ruff/mypy/pytest configured).
- Tooling entrypoints are cross-platform: `scaffold.py`, not `scaffold.sh`.
- Secrets only via `.env` (gitignored) and CI secrets. Never in code/commits/logs.
- **Default API identity:** `user_id=primary-user`, `AI_MEMORY_BASE_URL=https://memory.example.com`
  in code/examples; operators override via env (see private `OPERATOR.md`).
- **Credential custody:** store secret values in the operator's password-manager vault
  (ADR 017) and index them (no value) in private
  `ai-memory-infra-private/docs/security/secrets-catalog.md` — purpose, where it
  lives, rotation, blast radius.
- When a fact about an external product/API could be stale, verify before coding.

## Working model (sessions, tooling, governance)

- **Short-lived, disposable sessions (tenet 16).** State lives in **files, not chat** —
  checkpoint `STATUS.md` after each logical step. Emit a Resume prompt only after a
  real handoff checkpoint, not while awaiting an operator action.
- **Workspace/root discipline:** parent `ai-memory` workspace; `ai-memory-infra` is the
  **control plane**; package repos are touched deliberately when they carry changes.
- **Repo integrity (tenet 11):** run `scripts/check-repo-health.*` at session start and
  before every commit.
- **Session bootstrap (ADR 030):** `scripts/session_bootstrap.py` injects compact context.
- **Completion gate (ADR 027/030):** `scripts/completion_gate.py` enforces commit+push
  at turn-end for every touched repo.
- **Hooks are portable (tenet 2, ADR 030):** `scripts/install_ide_hooks.py` generates
  per-IDE adapters from versioned Python in `scripts/`.
- **Completion gate:** when reversible work is verified, commit+push **every touched
  repo** in the same session. Standing authorization applies; do not ask "want me to
  commit?" at session end (COE 2026-06-10-session-end-commit-permission-ask).
- **"Park" semantics:** stop new work on the thread; still checkpoint and commit+push
  completed changes.
- **Final response gate:** touched repos pushed or blocker named; `STATUS.md` current;
  Resume prompt or explicit mid-step statement.

## Memory Daily Driver — conversational practice

The live memory bank is available via `scripts/memory.py` (spec
`docs/skills/operator-assistant-memory-daily-driver.md`):

- **"plan my day" / "what's on my plate?"** → `python scripts/memory.py agenda`
- **"log this / remind me / follow up <day>"** → `add-open-item` with resolved ISO dates
- **"we decided X because Y"** → `add-decision` (verbatim, `--occurred` date). Reversals:
  capture a superseding decision; never edit the old row.
- **"done / that happened"** → `close <id> --resolution "<what happened>"`
- **Confirmation contract:** after every write, echo exactly what was stored.
- Never store secrets or transcript dumps; repo files beat memory for project state.

Operator-specific verbs (e.g. career-tagged boards) are in private `OPERATOR.md`.

## Documentation discipline / Definition of Done

<!-- Generated from contract/dod.yaml by scripts/render_contract.py (ADR 033) — edit the YAML, not the text between the fences. -->
<!-- generated:agents-dod start -->
Tenet 10: restated facts must not drift. A change is **not done** until the docs
it touches are updated *in the same PR*. Use this trigger table — change-type →
docs to update:

| When you change… | Update these |
|---|---|
| Architecture / a component / a provider | `docs/architecture.md` (diagram + Components & cost), `README.md` summary, an ADR, private `ai-memory-infra-private/docs/interview_packet.md` if portfolio narrative needed |
| A major decision, or reverse one | new ADR (or set the old one **Superseded by NNN**), private `ai-memory-infra-private/docs/interview_packet.md` decision log (append, dated), `STATUS.md` last-decisions |
| A cross-cutting / data-contract decision (`user_id`, `source`, `type`, schema, auth, transport) | The decision is **a contract, not a document** (ADR 031): verify — and patch where needed — in **every** consumer repo (`ai-memory-extension`, MCP proxy `src/mcp_proxy/client.py`, the OpenClaw adapter, the future todo app) before it is done; register it in `docs/interfaces.md` (with enforcement status); add a "Propagation / conformance" section to the ADR; `scripts/check_memory_contract.py` must pass. A clean control-plane repo with a violating consumer is **not** done |
| A tenet | `docs/tenets.md` (PR + rationale), the tenet summary in `AGENTS.md` — **never** restate it in the editor pointer files (they stay pure pointers; see next row + ADR 018) |
| An editor pointer file (`.cursor/rules/*`, `CLAUDE.md`) | Keep it a **pure pointer** — frontmatter + "read `AGENTS.md`"; it carries **zero** tenets/rules/decisions (tenet 2, ADR 018). If you're adding substance here, it belongs in `AGENTS.md` instead |
| Infra/IaC (terraform, compose, Caddy, `.env`) | `docs/runbook.md` / `docs/setup.md` if ops or commands change, `README.md` quick-start if commands change, `STATUS.md` |
| A new phase, `src/` module, or capability | **a design doc first** (`docs/design/<name>.md` from `docs/design/TEMPLATE.md` — HLD + LLD: components, interfaces, data contracts, failure modes, test plan) **before code**, proportional to stakes (tenet 8); then tests first (TDD), `README.md`/`architecture.md` if user-facing, `docs/interfaces.md` if it adds/changes a contract, eval gold-standard with **synthetic** fixtures if applicable |
| Anything cost-relevant (plan, provider, bucket) | `docs/architecture.md` Components & cost |
| Security / guardrail behaviour | ADR 009 area, tests |
| Create / obtain / rotate any account, API token, key, or secret | Store the value **immediately** in the operator's password-manager vault (ADR 017) **and** add/update a row (no value) in the private `ai-memory-infra-private/docs/security/secrets-catalog.md` (purpose · where it lives · rotation · blast radius); note SSO logins for nominee access. **Never** commit it or paste it in chat/logs. Not done until it's in the vault **and** the catalog |
| End of any working session | (1) `docs/planning/STATUS.md` — **overwrite means replace**: current phase, the *current* session's decisions, open blockers, next action. **Never keep "Prior update" blocks or older dated sections** — superseded narrative moves to BUILD-LOG *in the same step* (it's already there if the DoD was followed). Shape is machine-enforced by `scripts/check_status_snapshot.py` (pre-commit gate 3 + CI; COE 2026-06-10-status-snapshot-log-drift). (2) **Append** a session entry to the private `docs/planning/BUILD-LOG.md` (steps · gotchas/micro-lessons · time: wall-clock + rough human/agent split) and a curated, no-personal-detail summary to public `docs/BUILD-JOURNEY.md` (keep them in agreement, tenet 10) |
| Every logical step + every response (tenet 16) | Checkpoint `STATUS.md` ("Next action" / "Done this session") at each logical step boundary — not just at session end — so the file is resume-ready at real handoff points. End a response with a copy-paste **Resume prompt** only when that checkpoint exists; otherwise say the work is mid-step and keep going in the current chat |

**Done means:** code tests green (if code) · the trigger row's docs updated · an
ADR exists for any major choice · `STATUS.md` refreshed · PR checklist ticked ·
no drift between any two places that state the same fact.
<!-- generated:agents-dod end -->
