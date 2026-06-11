# ADR 010: Portability and versioning tenets

**Status:** Accepted
**Date:** 2026-06-04
**Source:** Tenets defined in initial project session, consolidated here.

### Tenets

**1. Everything is versioned.** All artifacts in source control: code, configs, scaffolding scripts, the exact setup commands, ADRs, planning docs, and agent instructions (AGENTS.md). The repo is the historical record. Corollary: commit the generator (a script) over hand-run commands.

**2. Portable / editor-agnostic.** Cursor must be swappable for VS Code, Claude Code, or any agent tomorrow with zero loss. Canonical context lives in `AGENTS.md`; editor-specific files are thin pointers. Extends to platform: Docker Compose (not Railway), OpenAI-compatible LLM interface (not vendor-specific), standard Postgres (not managed-service lock-in).

**3. Cross-platform out of the box.** Mac and Windows both work with no special setup. Prefer Python over shell for tooling, no symlinks, containers normalize the runtime, document OS-specific commands where they differ. This is why `scaffold.py` replaced `scaffold.sh`.

**4. Graceful degradation.** VPS down means every LLM still works with its own native memory. The Chrome extension silently fails. Claude's built-in memory still works. The MCP memory path gracefully degrades. When VPS recovers, enrichment resumes. No data loss (Postgres persists to disk, daily backups). The memory layer enriches but is never a hard dependency.

**5. No firm IP in the public repo.** Platform + LifeGraph POC only. Trading firm, social media, and RIA logic stays in private repos that plug in via REST API. High-level venture descriptions (names, tags) are fine — they're what you'd say in any interview. Proprietary strategy code, backtest results, market data schemas, SEBI compliance logic — all private.

### Consequences

These tenets constrain every technical decision. "Should we use Railway?" fails tenet 2 (proprietary). "Should we write a bash script?" fails tenet 3 (cross-platform). "Should we add a firm-specific trading backtest to the README?" fails tenet 5 (IP leakage). They're enforced via `AGENTS.md` so that any AI agent working in the repo follows them automatically.

---
