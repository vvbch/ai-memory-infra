# AGENTS.md — ai-memory-infra

> Canonical agent context for this repo. Editor-agnostic by design: read by
> Cursor (`.cursor/rules` point here), VS Code / Copilot, and Claude Code
> (`CLAUDE.md` points here). **Edit this file, not the pointers.**

## What we're building

Self-hosted, cross-platform AI memory infrastructure with a knowledge graph —
a persistent memory layer under Claude, ChatGPT, Gemini, and DeepSeek, on any
device. Also a portfolio showcase: it must read as production-grade infra.

## Who

**Chandra** — ex-Amazon SDE3 (3y) then SDM/EM (10y+), Bangalore. Direct,
action-oriented, pushback-tolerant. Skip Docker/Git/CLI basics. Be concise;
prefer one clear next action over option lists; flag scope creep.

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

## Architecture (summary)

Caddy (auto-HTTPS) → Mem0 (FastAPI REST + MCP) over PostgreSQL/pgvector, plus
Neo4j (dual namespace: Mem0 auto-managed graph + LifeGraph). Prometheus +
Grafana for observability. Reach: Chrome extension (desktop / ChromeOS) +
Claude MCP connector (iOS, Claude Code) + Cursor/VS Code as MCP clients.
Android extension coverage is best-effort only (Kiwi archived Jan 2025; see
ADR 004) and iOS non-Claude LLMs are a known gap.
Extraction via DeepSeek V4 Flash (OpenAI-compatible, `OPENAI_BASE_URL`).
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
