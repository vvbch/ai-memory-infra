# Tenets

Durable principles for this project. Versioned on purpose: when a decision
later looks wrong, we trace it back here and learn. Changes to tenets go
through a PR with rationale.

## 1. Everything is versioned
Every artifact lives in source control — application code, infra (Terraform,
Compose, Caddy), CI/CD, scaffolding scripts and the exact setup commands, ADRs,
the planning doc, and the agent instructions themselves (`AGENTS.md`). The repo
is the single source of truth and the historical record. Nothing important
survives only in a chat window, a terminal, or one laptop. Corollary: prefer
committing the *generator* (a script) over hand-run commands, so the work is
reproducible and reviewable.

## 2. Portable / editor-agnostic
Tooling must not lock us to one vendor. Cursor must be replaceable by VS Code —
or any agent — tomorrow, with zero loss of context. So canonical agent context
lives in `AGENTS.md` (read by Cursor, VS Code/Copilot, and Claude Code), and
editor-specific files (`.cursor/rules/*`, `CLAUDE.md`) are thin pointers to it.
Same principle for the platform: Docker Compose runs anywhere, no managed-service
lock-in, LLM providers are swappable behind an OpenAI-compatible interface.

## 3. Cross-platform out of the box
Mac and Windows both work with no special setup. Prefer Python over shell for
project tooling (one runtime, no bash/PowerShell dialect split). Containers
normalize the actual runtime. Avoid symlinks (Windows-hostile) — use small
pointer files instead. Where a host command genuinely differs by OS, document
both. The committed scaffolder is `scaffold.py`, not `scaffold.sh`.

## 4. Graceful degradation
The VPS being down must never break daily work: every LLM still functions with
its own native memory. The memory layer enriches; it is never a hard dependency.

## 5. No firm IP in the public repo
This repo is the platform + LifeGraph POC, Apache-2.0, forkable by anyone.
Trading / social-media / RIA logic lives in separate private repos that plug
into the same infrastructure via REST API. The public repo demonstrates
capability without leaking LLP assets.
