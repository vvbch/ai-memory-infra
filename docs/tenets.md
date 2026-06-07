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

**What "thin pointer" means (precise boundary — ADR 018).** An editor pointer file
contains *only*: (a) the editor's required frontmatter/mechanics, and (b) an
instruction to read `AGENTS.md`. It carries **zero canonical content** — no
tenets, rules, conventions, or decisions — so it *cannot* drift (tenet 10). If you
feel the urge to add a rule to a pointer file, that rule belongs in `AGENTS.md`
instead. "Pointer" is a content stub, **not a filesystem symlink** (tenet 3 forbids
symlinks — Windows-hostile). Read-reliability is solved at the mechanism
(`alwaysApply: true` keeps "read AGENTS.md" in front of the agent), never by
copying content.

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

## 11. Drive-synced repos: remote is truth, integrity is checked
Both repos (including their `.git` internals) live inside a Google Drive
"Mirror" folder. This is a deliberate operator choice — it gives a second,
always-on off-machine copy and lets large gitignored firm artifacts ride the
same Drive backup. It also carries a real, accepted **risk**: Drive syncing
`.git` internals can corrupt the repo — conflicted-copy files inside `.git`,
half-synced pack/ref files, or a stale `index.lock`. There is no reliable way to
exclude `.git` from a Mirror-mode sync, so we **mitigate** rather than avoid:

1. **GitHub is the source of truth, not the local working copy.** The Drive copy
   is a convenience and a backup-of-last-resort, never the canonical record.
2. **Commit and push every session — never batch.** The smaller the window of
   un-pushed work, the smaller the blast radius if the local `.git` corrupts.
3. **Integrity is checked, not assumed.** `scripts/check-repo-health.*` runs
   `git fsck`, scans for Drive conflicted-copy files in `.git`, detects stale
   `index.lock`, and reports ahead/behind vs the remote — at session start, on a
   daily schedule, and as a fast pre-commit subset.
4. **On any red check: do not hand-repair.** Re-clone from GitHub into a clean
   path and re-apply uncommitted work. Repairing a Drive-corrupted `.git` in
   place is a time sink with no guaranteed-clean end state.
5. **Never commit large firm artifacts into git history** — that is a one-way
   door (history rewrites are painful and break every clone). Large files stay
   gitignored and Drive-backed, outside git.
6. **Quit Drive while actively working in the repo** when practical, so a sync
   pass can't race a `git` write.

Decision, risk, and this mitigation contract are recorded in **ADR 015**; the
session-start / pre-commit / scheduled firing of the integrity check is the
operational expression of this tenet.

## 12. Vendors are deliberated, documented, and reversible
No external dependency — registrar, cloud, DNS host, object store, SaaS, model/
API provider, paid tool — gets adopted *suddenly*. Before committing to one, weigh
and **write down (in an ADR, at the right verification tier — tenet 8)** these
dimensions, not just the sticker price:

1. **Total cost over time** — setup + recurring + cost-at-scale, **and the
   exit/migration cost**. A cheap service with painful lock-in is not cheap.
2. **Portability / lock-in** — can we export our data and config and leave on
   *standard formats* (S3, DNS zone files, OpenAI-compatible APIs, plain SQL)?
   Prefer open standards; name the exit path before entering (tenet 2).
3. **Reliability & track record** — uptime/SLA, status-page and incident history,
   support quality, how it behaves under failure.
4. **Company viability** — ownership, reputation, and financial health/longevity:
   will they plausibly still exist and be well-run in 5–10 years? Treat recent
   acquisitions and price-hike histories as yellow flags.
5. **Ecosystem & standards** — what else the vendor powers, how mainstream it is,
   and whether it speaks portable protocols so we stay swappable.

Recommend a default, but **surface the trade-off and let the operator decide** —
this is a one-way-door check (tenet 6/7/9 all feed it). Every adoption ships with
its **decommission/exit path** documented (`docs/decommission.md`), so anything we
turn on, we (or an executor) can cleanly turn off.

## 13. Stay on the critical path; diverge only deliberately
Every working session has one current goal — the **"Next action" in
`docs/planning/STATUS.md`**. Work serves that goal until it is done or the goal is
*explicitly* re-scoped. The failure mode this guards against is not laziness, it's
the opposite: enthusiasm leaking into **scope creep, gold-plating, premature
depth, yak-shaving, and tangential-but-good ideas** that quietly displace the
actual task. This is the *attention-and-effort* analog of tenet 7 (which governs
*architecture* simplicity); tenet 13 governs **where the operator's and the
agent's time go over a session.**

Operating rules:
- **Match depth to stakes (tenet 8).** Don't research a ₹1,000/yr decision like a
  ₹10-lakh one. Ground choices in first principles, then stop at the layer the
  decision actually needs — depth beyond that is a cost, not a virtue.
- **Capture, don't chase.** A good idea that isn't this session's goal gets
  **parked** ("Parked / deferred ideas" in `STATUS.md`), not followed and not
  lost. Discipline must never cost a good idea.
- **One goal in flight.** Finish or consciously re-scope before starting another.

The agent's duty — **graduated, escalate only as far as needed:**
1. **Caution** (default, cheap, frequent) — name the divergence and its cost:
   "this is expanding from X to Y; that adds Z."
2. **Advise** — recommend a path: *proceed / park / defer to a separate session*,
   with a one-line reason, then continue.
3. **Stop & redirect** (*rare*) — only for a real derailment: the session goal
   would be abandoned, money/time spent with no decision reached, or a one-way
   door approached unplanned. Pause new depth, restate the actual goal, and get a
   conscious go/no-go before continuing.

The operator can always overrule — a deliberate, **eyes-open** divergence is fine
(that's exactly what "park vs proceed" makes explicit). What this tenet forbids is
the *accidental* drift.

## 14. Errors are mechanisms — run a COE, fix the control plane first
When something goes wrong — a tenet/rule violated, a defect shipped, an incident,
a security near-miss, or the agent not adhering to guidance — we treat it as a
**mechanism to improve the system**, not a one-off to patch and forget (the Amazon
"Correction of Errors" discipline). For anything beyond trivial we open a
**structured COE** in `docs/coe/` (template + index there): *impact, timeline,
**detection** (a human catch is itself a gap), 5-whys to a **systemic** root cause,
and corrective actions split **Prevent / Detect / Mitigate** with owner + date.*
Two rules carry the most weight:

1. **Fix the control plane before the data plane.** Correct the rule / spec /
   mechanism that *allowed* the defect before fixing the instance — or the instance
   regenerates (ADR 018 is the worked example).
2. **Capture the lesson where it compounds.** The systemic fix lands in a tenet or
   ADR; the narrative lands in `interview_packet.md`; follow-ups are ranked in
   `docs/planning/BACKLOG.md`.

**Blameless:** the target is always the system, never the operator or the agent.
Match COE depth to blast radius (tenets 13 & 8): a one-line note for the trivial, a
full COE for anything with teeth.
