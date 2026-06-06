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
- When a fact about an external product/API could be stale, verify before coding.

## Working model (sessions, tooling, governance)

- **Everything runs in a single Cursor session (this one).** Planning,
  decisions, fact-verification, doc upkeep, **and execution/build** all happen
  here — there is no longer a separate CONTROL vs BUILD session. The earlier
  Claude.ai control surface and the parallel build session are both **retired**.
  One session owns the whole repo (public `docs/` + `infra/` + `src/` and the
  private companion repo).
- If a second Cursor session is ever opened in parallel, the rule still holds:
  sessions share **files, not chat memory** — **re-read a file before acting**,
  and never edit the same file from two sessions at once.
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
| A tenet | `docs/tenets.md` (PR + rationale), the tenet summary in `AGENTS.md`, `.cursor/rules` pointer if relevant |
| Infra/IaC (terraform, compose, Caddy, `.env`) | `docs/runbook.md` / `docs/setup.md` if ops or commands change, `README.md` quick-start if commands change, `STATUS.md` |
| A `src/` module or capability | tests first (TDD), `README.md`/`architecture.md` if user-facing, `interview_packet.md` (practice highlights / STAR), eval gold-standard if applicable |
| Anything cost-relevant (plan, provider, bucket) | `docs/architecture.md` Components & cost, `interview_packet.md` results/metrics |
| Security / guardrail behaviour | ADR 009 area, `interview_packet.md` security highlight, tests |
| End of any working session | `docs/planning/STATUS.md` — overwrite: current phase, last decisions, open blockers, next action |

**Done means:** code tests green (if code) · the trigger row's docs updated · an
ADR exists for any major choice · `STATUS.md` refreshed · PR checklist ticked ·
no drift between any two places that state the same fact.
