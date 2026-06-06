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

## 6. Cost-conscious, not cost-blind
Default to the cheaper option and justify every recurring rupee — this is a
personal project, not a funded team. But cost is a guideline, not a religion:
while still employed and in launch/seed stage, a spend that buys materially
better reliability, capability, or time is acceptable when explicitly justified.
Optimize for total cost of ownership (including the operator's time), not just
the monthly invoice. Annotate components with their `(~₹X/mo)` cost so the
trade-off is always visible.

## 7. Fewer moving parts
For a one-person project, simplicity beats sophistication. Every container,
provider, service, and dependency is something to configure, secure, monitor,
back up, and debug at 2am — alone. Prefer one well-understood tool over two
clever ones; prefer a managed default over a bespoke wiring; collapse providers
and services where you can. Add a moving part only when its value clearly
exceeds its lifetime maintenance cost. (This is *simplicity*, not *minimalism* —
production-grade practices like IaC, TDD, and CI/CD stay; see AGENTS.md.)

## 8. Verify in the right tier
External facts about products and APIs go stale fast, so match the verification
effort to the question. In order of preference:
1. **Web search / official docs / the actual repo** — for anything time-sensitive:
   current providers, prices, model IDs, API shapes, what a compose file actually
   ships. The repo's own source is ground truth over any blog or summary.
2. **Deep research** — when a decision has real trade-offs and no single source
   settles it (e.g. comparing providers on cost *and* quality).
3. **Internal model knowledge** — least preferred for anything external and
   dated; fine for durable engineering judgement.
When sources conflict, prefer the most authoritative and most recent, and write
down the one-line command the operator can run to confirm before committing.

## 9. One provider across pipeline stages, unless the gap is vast
When a pipeline has multiple model-backed stages (e.g. fact *extraction* and
*embedding*), prefer a single provider for all of them: one key, one bill, one
SDK, one base URL, fewer failure modes (tenet 7). Split providers only when the
cost or capability difference is *vast* — not marginal. Whenever providers are
split, the architecture must keep them swappable behind an OpenAI-compatible
interface (tenet 2) and the split must be justified in an ADR.

## 10. Single source of truth; no instruction drift
The repo is the one authoritative record (tenet 1). When the same fact or
decision is restated across artifacts — `AGENTS.md`, ADRs, `README.md`,
`docs/architecture.md`, `docs/interview_packet.md`, `docs/planning/STATUS.md` —
they must agree. A change in one **triggers** updates to the others; this is
enforced by the Definition of Done in `AGENTS.md`. Prefer a pointer over a copy
(tenet 2) so there's less to keep in sync in the first place.

**Caveat — this does not govern dynamic memory.** The OpenMemory/Mem0 memory
*store* is reconciled at runtime by Mem0's dedup / conflict-resolution pipeline
(ADD / UPDATE / DELETE during extraction), not by manual single-source editing.
This tenet governs **authored artifacts** (docs, configs, decisions), never the
learned memory graph.
