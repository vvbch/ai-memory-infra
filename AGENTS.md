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
    5-whys to a systemic root cause · Prevent/Detect/Mitigate actions w/ owner+date).
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
    *every* step, and **end every response with a copy-paste Resume prompt** so a fresh
    chat resumes with zero loss. *Why:* a long-lived stateful session re-sends its whole
    transcript each turn → ~quadratic token cost (*context-window amplification*); one
    half-day session burned a month's Cursor credits. Bounded sessions cap that blast
    radius (agent-tooling analog of tenet 15). Twelve-Factor stateless-process + backing
    store. See COE 2026-06-08.
17. **Minimize operator cognitive load — act on reversible (two-way-door) decisions;
    deliberate only on one-way doors.** For easily-reversible work the agent **just does it
    and reports the call** (commit every session — never leave changes hanging; pick
    reasonable defaults; proceed); a clean `git revert` is the safety net. Reserve the
    operator's attention for **one-way doors** (spend, lock-in, deletion, scope change —
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

Caddy (auto-HTTPS) → Mem0 (FastAPI REST + MCP) over PostgreSQL/pgvector, plus
Neo4j (dual namespace: Mem0 auto-managed graph + LifeGraph). Prometheus +
Grafana for observability. Reach: Chrome extension (desktop / ChromeOS) +
Claude MCP connector (iOS, Claude Code) + Cursor/VS Code as MCP clients.
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

## Engineering practices (non-negotiable)

- **IaC**: Terraform for all infra. No manual console clicks.
- **TDD**: tests before implementation; 80%+ coverage on `src/`.
- **CI** on every PR: ruff + mypy + pytest against an ephemeral Docker stack.
- **CD** on push to main: SSH deploy → health check → rollback on failure.
- **Eval framework**: retrieval (precision@k, MRR), extraction (cross-LLM),
  categorization, guardrails. Weekly CI run; blocks on regression.
- **Security**: JWT auth, PII filter (Aadhaar/PAN/keys), HTTPS, CORS allowlist,
  rate limiting, basic auth on admin UIs. Stack ships with none of this — add it.
- **ADRs** in `docs/decisions/` for every major choice.

## Build phases

0 scaffold + accounts · 1 IaC (Terraform/Compose/Caddy) · 2 backup/restore ·
3 Chrome extension fork · 4 Claude + Cursor/VS Code MCP · 5 migration (TDD) ·
6 LifeGraph (TDD) · 7 eval framework (TDD) · 8 observability · 9 docs/polish.

## Conventions

- Python 3.12, `pyproject.toml` is source of truth (ruff/mypy/pytest configured).
- Tooling entrypoints are cross-platform: `scaffold.py`, not `scaffold.sh`.
- Secrets only via `.env` (gitignored) and CI secrets. Never in code/commits/logs.
- **Credential custody:** every account login, API token, and key for the project
  is stored in the **Bitwarden `ai-memory-infra` individual-vault folder** the moment
  it's created (ADR 017). The vault is the single home for secrets, mirroring how git
  (tenet 1) is the single home for everything non-secret — nothing important lives
  only in a chat window. For SSO logins, store a note (e.g. "DigitalOcean = Google
  SSO, <email>") so the nominee can still get in.
- When a fact about an external product/API could be stale, verify before coding.

## Working model (sessions, tooling, governance)

- **One surface (Cursor), but sessions are short-lived and disposable (tenet 16).**
  Planning, decisions, fact-verification, doc upkeep, **and execution/build** all happen
  in Cursor — there is no separate CONTROL vs BUILD *surface* (the earlier Claude.ai
  control surface + the parallel build session are both **retired**). But a session is
  **one task, single-shot**, not a marathon thread: a long-lived chat re-sends its whole
  transcript every turn (≈quadratic token cost — *context-window amplification*) and once
  burned a month's Cursor plan credits in half a day (COE 2026-06-08). So **state lives in
  files, not chat** — checkpoint `STATUS.md` after *each* step, and **end every response
  with a copy-paste Resume prompt** so the operator can start a fresh chat at any point
  with zero loss. Prefer a new chat over a long follow-up thread.
- Sessions (sequential *or* parallel) share **files, not chat memory** — **re-read a file
  before acting**, and never edit the same file from two sessions at once.
- **The safeguard against agent error is the Definition-of-Done verification
  gate below — not a second tool.** Trust comes from the DoD + tests + ADRs +
  no-drift check, applied every change, not from which editor is open.
- **Repo integrity (Tenet 11), third/soft layer:** run
  `scripts/check-repo-health.*` **at session start and before every commit**.
  (The hard layers are the git pre-commit hook + the daily scheduled run; this
  line is the human/agent reminder so a missing hook never means a missing check.)

## Documentation discipline / Definition of Done

Tenet 10: restated facts must not drift. A change is **not done** until the docs
it touches are updated *in the same PR*. Use this trigger table — change-type →
docs to update:

| When you change… | Update these |
|---|---|
| Architecture / a component / a provider | `docs/architecture.md` (diagram + Components & cost), `README.md` summary, an ADR, `docs/interview_packet.md` (arch-at-a-glance + decision log) |
| A major decision, or reverse one | new ADR (or set the old one **Superseded by NNN**), `interview_packet.md` decision log (append, dated), `STATUS.md` last-decisions |
| A tenet | `docs/tenets.md` (PR + rationale), the tenet summary in `AGENTS.md` — **never** restate it in the editor pointer files (they stay pure pointers; see next row + ADR 018) |
| An editor pointer file (`.cursor/rules/*`, `CLAUDE.md`) | Keep it a **pure pointer** — frontmatter + "read `AGENTS.md`"; it carries **zero** tenets/rules/decisions (tenet 2, ADR 018). If you're adding substance here, it belongs in `AGENTS.md` instead |
| Infra/IaC (terraform, compose, Caddy, `.env`) | `docs/runbook.md` / `docs/setup.md` if ops or commands change, `README.md` quick-start if commands change, `STATUS.md` |
| A `src/` module or capability | tests first (TDD), `README.md`/`architecture.md` if user-facing, `interview_packet.md` (practice highlights / STAR), eval gold-standard if applicable |
| Anything cost-relevant (plan, provider, bucket) | `docs/architecture.md` Components & cost, `interview_packet.md` results/metrics |
| Security / guardrail behaviour | ADR 009 area, `interview_packet.md` security highlight, tests |
| Create / obtain any account, API token, key, or secret | Store it **immediately** in the Bitwarden `ai-memory-infra` individual-vault folder (ADR 017); note SSO logins so the nominee can get in. **Never** commit it or paste it in chat/logs. Not done until it's in the vault |
| End of any working session | (1) `docs/planning/STATUS.md` — overwrite: current phase, last decisions, open blockers, next action. (2) **Append** a session entry to the private `docs/planning/BUILD-LOG.md` (steps · gotchas/micro-lessons · time: wall-clock + rough human/agent split) and a curated, no-personal-detail summary to public `docs/BUILD-JOURNEY.md` (keep them in agreement, tenet 10) |
| Every step + every response (tenet 16) | Checkpoint `STATUS.md` ("Next action" / "Done this session") at each step boundary — not just at session end — so the file is always resume-ready. End **every** response with a copy-paste **Resume prompt** reflecting the latest checkpoint (read `STATUS.md` + `AGENTS.md` → repo-health → Next action) so a fresh chat resumes with zero loss |

**Done means:** code tests green (if code) · the trigger row's docs updated · an
ADR exists for any major choice · `STATUS.md` refreshed · PR checklist ticked ·
no drift between any two places that state the same fact.
