# AGENTS.md — ai-memory-infra

> Canonical agent context for this repo. Editor-agnostic by design: read by
> Cursor (`.cursor/rules` point here), VS Code / Copilot, and Claude Code
> (`CLAUDE.md` points here). **Edit this file, not the pointers.**
>
> **▶ Resuming / "what's next?" → read `docs/planning/STATUS.md` first** (current
> phase, last decisions, blockers, next action). Then `docs/setup.md` for the
> live operational walkthrough, and `docs/interview_packet.md` for the narrative.

## What we're building

Self-hosted, cross-platform AI memory infrastructure with a knowledge graph —
a persistent memory layer under Claude, ChatGPT, Gemini, and DeepSeek, on any
device. Also a portfolio showcase: it must read as production-grade infra.

## Who

**Chandra** — ex-Amazon SDE3 (3y) then SDM/EM (10y+), Bangalore. Direct,
action-oriented, pushback-tolerant. Be concise; prefer one clear next action
over option lists; flag scope creep; call out trade-offs explicitly.

**How to teach / collaborate (apply every interaction):**
- **Architecture / system design:** he's senior here, but still ground each
  discussion in **basics and first principles** — don't skip the "why it works
  this way." Explain concepts as **ELI5 → one layer technical → trade-offs + how
  industry actually uses it**, with concrete *where-used-vs-not* examples.
- **Hands-on ops (git / cloud / docker / deploy) — concierge mode, zero cognitive
  load.** Treat Chandra as computer-illiterate *for ops/account/console setup*
  (this is about saving his attention, not ability). Rules:
  - **One step at a time. Never dump a multi-step list and ask him to execute it.**
    Give exactly one action, wait for "done", then the next.
  - **Lead, don't quiz.** Pre-make every mechanical decision and state a single
    recommended default; only ask him for things that are genuinely his choice
    (e.g. a brand name, a spend ceiling) — and even then, propose concrete options.
  - **Hand-hold web consoles click-by-click:** exact button/link text, what page
    he'll land on, and what to ignore (consoles push templates/upsells/wizards —
    pre-empt those: "the homepage will try to make you pick a template; skip it,
    go straight to X"). Anticipate the thing that will throw him off.
  - **Operator-delegated action format:** before asking Chandra to click/type/run
    anything, give exactly one action with: (1) ELI5 purpose, (2) exact UI path or
    command, (3) visible success condition, and (4) "tell me what you see." If any
    of those four are unknown, verify first; do not hand him a vague "confirm it"
    instruction.
  - **No resume prompt while waiting on Chandra.** If the response asks Chandra to do
    the next step in the current flow, it is not a fresh-session handoff, even if
    `STATUS.md` is current. End with the single requested action and wait.
  - **Web-verify volatile UI steps before prompting.** Browser and SaaS console
    layouts drift; check current official docs or the live UI immediately before
    giving click-by-click instructions. State the exact artifact to pick (e.g.,
    "select the folder containing `manifest.json`") and the success condition
    ("OpenMemory appears on `chrome://extensions`"). If a prompt is stale, update
    these control-plane instructions and the affected docs in the same session.
  - **Pre-delegation gate (COE 2026-06-10):** before delegating any action to
    the operator, verify it cannot be performed via CLI/API (`gh`, `curl`,
    shell, MCP). Delegate only genuinely operator-exclusive actions
    (credentials entry, consent, account creation requiring PII). If the agent
    can describe the UI path, it can almost certainly run the CLI equivalent.
  - Say what each command/click does (**ELI5 → one layer deeper**) *before* he or
    I run it. Do the parts I can do; only delegate clicks I genuinely can't.
- **Research discipline:** web-verify volatile facts (model IDs, prices, API
  shapes, what a compose file ships) *before* baking them in, and **state which
  source you used** (tenet 8).

## Tenets (non-negotiable — see docs/tenets.md)

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
   ₹ outflow lives in the private `financial-decisions.md`.
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
    capture the lesson in a tenet/ADR + `interview_packet.md`. Depth ∝ blast radius.
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

## Architecture (summary)

Caddy (auto-HTTPS) → Mem0 (FastAPI REST) over PostgreSQL/pgvector, plus
Neo4j (running + backed up but **not yet written**: reserved for LifeGraph,
Phase 6; the deployed Mem0 ships no graph store, so it writes no graph today —
ADR 032, corrects the earlier "dual namespace" claim). A local stdio MCP
proxy (ADR 025) lets Claude Code, Cursor, and VS Code call the live REST API.
Prometheus + Grafana for observability. Reach: Chrome extension (desktop / ChromeOS) +
Claude remote MCP connector still needs a later HTTP endpoint for iOS; Claude Code +
Cursor/VS Code use the local MCP proxy.
Android extension coverage is best-effort only (Kiwi archived Jan 2025; see
ADR 004) and iOS non-Claude LLMs are a known gap.
Models: single OpenAI provider — `gpt-5-mini` (extraction, Mem0's current
default) + `text-embedding-3-small` (embeddings), swappable (ADR 013, supersedes
ADR 002).
Full diagram: `docs/architecture.md`.

## Ventures (metadata tags for memory categorization)

`trading_firm` (algo LLP, ETF pledge + Iron Condor; co-founder Vijaya) ·
`social_media` (YouTube; Vijaya + cousin) · `ria` (future) ·
`personal` / `career` / `migration` (job search, Germany/Australia, PhD Dec 2026).

## Engineering practices (standards — with honest status)

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
- **Eval framework** — **[target — Phase 7]** retrieval (precision@k, MRR),
  extraction (cross-LLM), categorization, guardrails, blocking on regression.
  Designed (ADR 007/014); `src/eval/` is still a stub.
- **Security** — **partly [in place], partly [target — Phase 9/security]**. In
  place: HTTPS (Caddy), an admin `X-API-Key` + JWT support on the API, basic auth on
  admin UIs, least-privilege backup key, gitleaks. Target (not yet built): PII filter
  (Aadhaar/PAN/keys), CORS allowlist, rate limiting. The OSS stack ships none of the
  target items — they are explicitly TODO, not done. See `docs/interfaces.md` §5.
- **ADRs** — **[in place]** in `docs/decisions/` for every major choice.
- **Supply chain** — **[target]** lockfile + dependency pinning + action SHA-pinning
  + Dependabot are not yet in place (BACKLOG; baseline scan gap).

## Build phases (with reality status)

Status as of 2026-06-10 — keep honest (a stub-only phase must not read as progress;
COE 2026-06-10-delayed-memory-buildout):

- **0 scaffold + accounts** — ✅ done
- **1 IaC (Terraform/Compose/Caddy)** — ✅ done (deploy is manual SSH; no CD yet)
- **2 backup/restore + drills** — ✅ done (nightly timer, dead-man's-switch, monthly drill)
- **3 Chrome extension fork** — ✅ live (some polish parked, BACKLOG)
- **4 Claude + Cursor/VS Code MCP** — ✅ done (local stdio proxy)
- **3-premise** *(product premise test — the current STATUS Next action)* — ⬜ not started
- **5 migration (TDD)** — ⬜ stub (`src/migration/` placeholder)
- **6 LifeGraph (TDD)** — ⬜ stub (`src/life_graph/` placeholder; Neo4j reserved, ADR 032)
- **7 eval framework (TDD)** — ⬜ stub (`src/eval/` placeholder; designed in ADR 007/014)
- **8 observability** — ⬜ stub (`src/observability/`, `src/health/` placeholders; `monitor.` reserved)
- **9 docs/polish** — ⬜ ongoing

`⬜ stub` means the `src/` module is a placeholder file, not an implementation.

## Conventions

- Python 3.12, `pyproject.toml` is source of truth (ruff/mypy/pytest configured).
- Tooling entrypoints are cross-platform: `scaffold.py`, not `scaffold.sh`.
- Secrets only via `.env` (gitignored) and CI secrets. Never in code/commits/logs.
- **Credential custody:** every account login, API token, and key for the project
  is stored in the **Bitwarden `ai-memory-infra` individual-vault folder** the moment
  it's created (ADR 017) **and** indexed (no value) in the private
  `docs/security/secrets-catalog.md` — purpose, where it lives, rotation, blast
  radius. The vault is the single home for secret *values*; the catalog is the single
  index of *what exists and where to find/rotate it*, mirroring how git (tenet 1) is
  the single home for everything non-secret — nothing important lives only in a chat
  window. For SSO logins, store a note (e.g. "DigitalOcean = Google SSO, <email>") so
  the nominee can still get in.
- When a fact about an external product/API could be stale, verify before coding.

## Working model (sessions, tooling, governance)

- **One surface (Cursor), but sessions are short-lived and disposable (tenet 16).**
  Planning, decisions, fact-verification, doc upkeep, **and execution/build** all happen
  in Cursor — there is no separate CONTROL vs BUILD *surface* (the earlier Claude.ai
  control surface + the parallel build session are both **retired**). But a session is
  **one task, single-shot**, not a marathon thread: a long-lived chat re-sends its whole
  transcript every turn (≈quadratic token cost — *context-window amplification*) and once
  burned a month's Cursor plan credits in half a day (COE 2026-06-08). So **state lives in
  files, not chat** — checkpoint `STATUS.md` after *each logical step*. A copy-paste
  Resume prompt is allowed only after that checkpoint is current **and** the response is
  a true handoff/closeout, not while waiting for Chandra to perform the next action in
  the same flow. If the session is mid-step or awaiting an operator action, say so plainly
  and do **not** print a false resume token. Prefer a new chat over a long follow-up
  thread once a checkpoint exists.
- **Workspace/root discipline:** the root operating surface is the parent `ai-memory`
  workspace containing the three sibling repos. Treat `ai-memory-infra` as the
  **control plane** for cross-package planning, rules, docs, STATUS, and orchestration,
  with the parent workspace `AGENTS.md` and `.cursor/rules/00-workspace-control-plane.mdc`
  kept as thin pointers into this repo.
  while `ai-memory-extension` and other package repos are first-class touched repos when
  they carry implementation changes. Do **not** move the agent/chat root into
  `ai-memory-extension` or another package repo just to gain context; use package repos
  only as targeted data-plane workspaces for the files being edited. If a package needs
  changes, make the package edits deliberately, verify in that repo, commit+push that repo,
  then return the checkpoint/control-plane updates to `ai-memory-infra`.
- Sessions (sequential *or* parallel) share **files, not chat memory** — **re-read a file
  before acting**, and never edit the same file from two sessions at once.
- **The safeguard against agent error is the Definition-of-Done verification
  gate below — not a second tool.** Trust comes from the DoD + tests + ADRs +
  no-drift check, applied every change, not from which editor is open. The
  commit/push portion of that gate is now a **deterministic mechanism, not a
  prose hope**: `scripts/completion_gate.py` (ADR 027), invoked by a harness
  turn-end adapter, enforces it for any model (the long-promised repo handoff
  verifier). The adapter is generated at the workspace root, not Cursor-owned
  (tenet 2; ADR 030).
- **Repo integrity (Tenet 11), third/soft layer:** run
  `scripts/check-repo-health.*` **at session start and before every commit**.
  (The hard layers are the git pre-commit hook + the daily scheduled run; this
  line is the human/agent reminder so a missing hook never means a missing check.)
- **Session bootstrap, soft layer (ADR 030):** a harness `sessionStart` adapter
  runs `scripts/session_bootstrap.py`, which injects a compact block (control
  plane = `ai-memory-infra`, current phase, the Next action from `STATUS.md`) so a
  fresh session does **not** re-read all of `AGENTS.md`/`STATUS.md` just to learn
  where it is and what's next (token cost, tenet 16). The script is canonical and
  editor-agnostic; `additional_context` injection is best-effort (a known Cursor
  timing bug can drop it), so the script also exports `env` pointers and prints the
  same block to the Hooks output channel.
- **Completion gate, hard layer (ADR 027; placement ADR 030):** `scripts/
  completion_gate.py` checks every project repo at turn-end and, if any is dirty/
  unpushed, forces the agent to finish the commit/push DoD (and after a few loops,
  surfaces a loud operator-facing blocker). Two distinct mechanisms: the **git
  pre-commit** hook *validates* a commit's content (integrity + gitleaks); the
  **harness turn-end** adapter *triggers* the commit/push that would otherwise be
  skipped. The prose gate is the happy path; the hook is the model-independent
  guarantee.
- **Hooks are portable, not Cursor-owned (tenet 2, ADR 030).** Both the bootstrap
  and the completion gate live as editor-agnostic Python in `scripts/`. Cursor
  reads project hooks from the **workspace root** (`ai-memory/.cursor/hooks.json`),
  not from `ai-memory-infra/.cursor/`, and the parent workspace is not a git repo —
  so `scripts/install_ide_hooks.py` (versioned) generates the thin per-IDE adapters
  (`<root>/.cursor/hooks.json` for Cursor, `<root>/.claude/settings.json` for
  Claude Code) from one definition. **Re-run it after any re-clone** (same model as
  the git-hook installer, ADR 015). VS Code has no native session hook — wire the
  bootstrap as a folder-open task (see `docs/setup.md`).
- **Completion gate:** when a reversible work item is done and verified, commit the
  relevant changes and push **every touched repo** to remote in the same session, including
  package repos such as `ai-memory-extension` and private docs repos such as
  `ai-memory-infra-private`. Do **not** leave a routine "operator will commit/push" gate
  or push only the control-plane docs while package code remains local/ahead. Pause before
  commit/push only for one-way-door effects (spend, lock-in, deletion, data overwrite/
  retention policy), secrets, destructive operations, or an explicit operator pause.
  The instruction to read `AGENTS.md`/`STATUS.md` and continue the next action is the
  standing operator authorization for this workspace's reversible completion commit+push;
  do not require a second "please commit" prompt. If a higher-level tool policy or a
  real blocker prevents commit/push, say that before the final answer and leave the
  repo in a clearly documented handoff state.
- **Final response gate:** before any final answer, explicitly verify and satisfy all
  handoff requirements: (1) every touched git repo is committed and pushed, or the blocker
  is named plainly; (2) `STATUS.md` and required logs have been updated to a logical
  checkpoint; (3) the answer either ends with a copy-paste **Resume prompt** that tells the
  next fresh chat to read `docs/planning/STATUS.md` + `AGENTS.md`, run repo-health, and do
  the latest Next action, or explicitly says no resume prompt is valid because the work is
  mid-step or awaiting an operator action. Missing any item is a COE-class handoff failure.

## Memory Daily Driver — conversational practice (Operator Assistant)

The live memory bank is part of every conversation, via `scripts/memory.py`
(contract-enforcing helper; spec `docs/skills/operator-assistant-memory-daily-driver.md`):

- **"plan my day" / "what's on my plate?"** → run `python scripts/memory.py agenda`,
  present the buckets plain-English (overdue first), recommend one next action.
- **"log this / remind me / follow up <day>"** → `add-open-item` with resolved ISO
  dates (+ `--venture career` for recruiter reachouts); **"show recruiters"** → `recruiters`.
- **"we decided X because Y"** → `add-decision` (verbatim, `--occurred` date).
  **Reversals**: never edit the old decision — capture a new one:
  `"Supersedes <old-id> ('<gist>'): <new decision>. Reason: <why>."` The trail is
  the history; the latest decision is the snapshot.
- **"done / that happened"** → `close <id> --resolution "<what happened>"`.
- **Confirmation contract:** after every write, echo exactly what was stored
  (verbatim text, type, resolved dates, ventures, short id). Silent writes are a
  violation — mis-tags must be catchable immediately.
- Never store secrets or transcript dumps; repo files beat memory for project
  state (the bank is for *personal operating* items: todos, reachouts, decisions, facts).

## Documentation discipline / Definition of Done

Tenet 10: restated facts must not drift. A change is **not done** until the docs
it touches are updated *in the same PR*. Use this trigger table — change-type →
docs to update:

| When you change… | Update these |
|---|---|
| Architecture / a component / a provider | `docs/architecture.md` (diagram + Components & cost), `README.md` summary, an ADR, `docs/interview_packet.md` (arch-at-a-glance + decision log) |
| A major decision, or reverse one | new ADR (or set the old one **Superseded by NNN**), `interview_packet.md` decision log (append, dated), `STATUS.md` last-decisions |
| A cross-cutting / data-contract decision (`user_id`, `source`, `type`, schema, auth, transport) | The decision is **a contract, not a document** (ADR 031): verify — and patch where needed — in **every** consumer repo (`ai-memory-extension`, MCP proxy `src/mcp_proxy/client.py`, the OpenClaw adapter, the future todo app) before it is done; register it in `docs/interfaces.md` (with enforcement status); add a "Propagation / conformance" section to the ADR; `scripts/check_memory_contract.py` must pass. A clean control-plane repo with a violating consumer is **not** done |
| A tenet | `docs/tenets.md` (PR + rationale), the tenet summary in `AGENTS.md` — **never** restate it in the editor pointer files (they stay pure pointers; see next row + ADR 018) |
| An editor pointer file (`.cursor/rules/*`, `CLAUDE.md`) | Keep it a **pure pointer** — frontmatter + "read `AGENTS.md`"; it carries **zero** tenets/rules/decisions (tenet 2, ADR 018). If you're adding substance here, it belongs in `AGENTS.md` instead |
| Infra/IaC (terraform, compose, Caddy, `.env`) | `docs/runbook.md` / `docs/setup.md` if ops or commands change, `README.md` quick-start if commands change, `STATUS.md` |
| A new phase, `src/` module, or capability | **a design doc first** (`docs/design/<name>.md` from `docs/design/TEMPLATE.md` — HLD + LLD: components, interfaces, data contracts, failure modes, test plan) **before code**, proportional to stakes (tenet 8); then tests first (TDD), `README.md`/`architecture.md` if user-facing, `docs/interfaces.md` if it adds/changes a contract, `interview_packet.md` (practice highlights / STAR), eval gold-standard if applicable |
| Anything cost-relevant (plan, provider, bucket) | `docs/architecture.md` Components & cost, `interview_packet.md` results/metrics |
| Security / guardrail behaviour | ADR 009 area, `interview_packet.md` security highlight, tests |
| Create / obtain / rotate any account, API token, key, or secret | Store the value **immediately** in the Bitwarden `ai-memory-infra` individual-vault folder (ADR 017) **and** add/update a row (no value) in the private `docs/security/secrets-catalog.md` (purpose · where it lives · rotation · blast radius); note SSO logins so the nominee can get in. **Never** commit it or paste it in chat/logs. Not done until it's in the vault **and** the catalog |
| End of any working session | (1) `docs/planning/STATUS.md` — **overwrite means replace**: current phase, the *current* session's decisions, open blockers, next action. **Never keep "Prior update" blocks or older dated sections** — superseded narrative moves to BUILD-LOG *in the same step* (it's already there if the DoD was followed). Shape is machine-enforced by `scripts/check_status_snapshot.py` (pre-commit gate 3 + CI; COE 2026-06-10-status-snapshot-log-drift). (2) **Append** a session entry to the private `docs/planning/BUILD-LOG.md` (steps · gotchas/micro-lessons · time: wall-clock + rough human/agent split) and a curated, no-personal-detail summary to public `docs/BUILD-JOURNEY.md` (keep them in agreement, tenet 10) |
| Every logical step + every response (tenet 16) | Checkpoint `STATUS.md` ("Next action" / "Done this session") at each logical step boundary — not just at session end — so the file is resume-ready at real handoff points. End a response with a copy-paste **Resume prompt** only when that checkpoint exists; otherwise say the work is mid-step and keep going in the current chat |

**Done means:** code tests green (if code) · the trigger row's docs updated · an
ADR exists for any major choice · `STATUS.md` refreshed · PR checklist ticked ·
no drift between any two places that state the same fact.
