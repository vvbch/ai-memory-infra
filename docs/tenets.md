# Tenets

Durable principles for this project. Versioned on purpose: when a decision
later looks wrong, we trace it back here and learn. Changes to tenets go
through a PR with rationale.

<!-- Generated from contract/tenets.yaml by scripts/render_contract.py (ADR 033) — edit the YAML, not the text between the fences. -->
<!-- generated:tenets-full start -->
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
trade-off is always visible. **These `(~₹X/mo)` annotations are vendor *list
price*** (locale-neutral); the operator's **landed cost ≈ list × 1.3** — +18% GST
on imported digital services, +~4–6% forex (card markup + FX spread). **Budget
and size spend ceilings on landed cost, not the sticker.** The personal wallet
view (actual ₹ outflow) lives in the private operator financial ledger.

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
This includes operator-facing console/browser UI instructions: vendor UIs drift,
so check current official docs or the live UI before giving click-by-click
prompts, then name the exact target artifact and visible success condition.

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
`docs/architecture.md`, `docs/planning/STATUS.md` —
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

**Mechanism, not memory (ADR 027; placement corrected by ADR 030).** "Commit and
push every session" (point 2) is **not** left to the agent remembering it: it is
enforced by editor-agnostic logic in `scripts/completion_gate.py` that a harness
turn-end hook fires *regardless of which model is driving*, refusing to let a turn
end with a dirty/unpushed repo — the prose completion gate is the happy path, the
hook is the **hard layer**. This is the deterministic-execution-layer lesson:
rules/skills/`AGENTS.md` are run by the LLM (model-dependent), git hooks only
*validate* a commit already in flight, and only a harness lifecycle hook can
*trigger* the action deterministically. Added after a GPT-5.5 model switch ended a
session unpushed for the fourth time (COE
`2026-06-09-model-dependent-completion-gate.md`). **The gate is portable, not
Cursor-owned (tenet 2):** the logic lives in `scripts/`, and each IDE gets a thin
turn-end adapter generated at the workspace root by `scripts/install_ide_hooks.py`
(Cursor `stop`, Claude Code `Stop`). The same pattern carries the `sessionStart`
bootstrap (ADR 030). The placement was corrected after the original adapter was
written into a `.cursor/` directory that the open workspace root never loads
(COE `2026-06-09-ide-coupled-completion-gate.md`).

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
**detection** (a human catch is itself a gap), industry benchmark, 5-whys to a
**systemic** root cause, and corrective actions split **Prevent / Detect /
Mitigate** with owner + date.* Benchmark at least against AWS/Amazon COE practice
(blame-free 5 Whys, action ownership, recurrence prevention) and Google SRE
postmortem practice (written impact/timeline/root cause plus actions that improve
prevention, detection, mitigation, coordination, or communication).
Two rules carry the most weight:

1. **Fix the control plane before the data plane.** Correct the rule / spec /
   mechanism that *allowed* the defect before fixing the instance — or the instance
   regenerates (ADR 018 is the worked example).
2. **Capture the lesson where it compounds.** The systemic fix lands in a tenet or
   ADR; portfolio narrative lands in the private interview packet; follow-ups are ranked in
   `docs/planning/BACKLOG.md`.

**Blameless:** the target is always the system, never the operator or the agent.
Match COE depth to blast radius (tenets 13 & 8): a one-line note for the trivial, a
full COE for anything with teeth.

## 15. Fixed, capped cost beats variable — even at a mild premium
Prefer a **predictable, fixed monthly cost** over usage-based / on-demand pricing,
**even when on-demand pencils out mildly cheaper.** For a solo, self-funded project
with a possible income change, a *known* bill that cannot surprise us is worth more
than a few rupees of expected savings: it makes budgeting, pausing (tenet 12), and
forecasting clean, and — most importantly — it **caps the blast radius** of a
misconfiguration, a runaway loop, abuse, or an unexpected traffic spike. A cost
spiral is a far worse outcome than a small known premium.

Operating rules:
- **Default to flat-rate resources** — a fixed-size droplet, a reserved/annual plan —
  over autoscaling or per-request billing.
- **Anything that *must* be usage-based** (e.g. an LLM API) gets a **hard spend cap +
  billing alerts set at adoption** — never left uncapped.
- **Set billing alerts on every paying account** (DigitalOcean, Cloudflare, OpenAI)
  as a backstop, regardless of plan type.
- **Diverge only when the on-demand saving is *large*** (mirroring tenet 9's "unless
  the gap is vast"), the choice is **documented in an ADR**, and a hard cap/alert is
  *still* in place.

This sharpens tenet 6: tenet 6 says justify every rupee; tenet 15 says that between
two otherwise-acceptable options, choose the one whose cost **can't surprise you** —
predictability and a bounded worst case outrank marginal optimisation.

## 16. Sessions are stateless and disposable — checkpoint to the repo, don't accumulate context
A session is **one task** — the current `docs/planning/STATUS.md` "Next action" — run
**single-shot**, not a marathon follow-up thread. State lives in the **repo, not the
chat**: the session **checkpoints to `STATUS.md` after every execution step**, so any
step boundary is a clean resume point and a *fresh* session reconstructs full context
from files (`STATUS.md` + `AGENTS.md` + the append-only `BUILD-LOG.md`) — never from
chat scrollback. This is the **Twelve-Factor "stateless, share-nothing process + backing
store"** discipline (Factor VI) applied to agent sessions: the repo is the backing store
(tenet 1); the chat window is ephemeral, disposable compute.

**Why — the cost mechanism.** A long-lived conversational session is **stateful**: the
agent re-sends the *entire transcript* as input tokens on every turn, so cumulative token
cost grows **roughly quadratically** with session length — *context-window amplification*.
A single half-day monolithic session exhausted a whole month's Cursor plan credits
(`docs/coe/2026-06-08-cursor-credit-exhaustion.md`). Short, disposable sessions **cap the
blast radius** of token spend — the agent-tooling analog of tenet 15 (a bounded, known
cost can't spiral).

- **Anti-pattern:** the *monolithic, long-lived, stateful session* — an ever-growing
  context window re-billed every turn (the conversational cousin of a "sticky session").
- **Pattern:** *stateless, single-task sessions* + **checkpoint/restore** + a
  **continuation (resume) token** — externalize state, keep the live context bounded.

Operating rules:
- **Checkpoint per step, not just per session.** Keep `STATUS.md` ("Next action",
  "Done this session") current at each step boundary — overwrite as you go (DoD), so the
  file is *always* resume-ready, not only at session end.
- **Emit a resume token only after a real checkpoint and only for a true handoff.** A
  copy-paste **Resume prompt** is valid only when `STATUS.md` reflects a logical handoff
  point (read `STATUS.md` + `AGENTS.md`, run repo-health, do the Next action) **and** the
  response is not waiting on the operator to do the next click/command in the same flow. If the
  session is mid-step or awaiting an operator action, say that plainly and do not print a
  false resume token.
- **One task per session; prefer a new chat over a long thread.** When the task is done —
  or the context has grown large — start a fresh session rather than continuing. Reinforces
  tenet 13 (one goal in flight).
- **Files, not chat memory.** Re-read the relevant file before acting; never rely on
  conversational state (already the rule for parallel sessions — now the rule for *all*
  sessions).

Complements tenet 1 (everything versioned, so the repo *can* be the backing store),
tenet 13 (one goal per session), and tenet 15 (cap variable cost). Added after the
credit-exhaustion COE; the transferable lesson lives in the private interview packet.

## 17. Minimize operator cognitive load — act on reversible (two-way-door) decisions, deliberate only on one-way doors
The scarcest resource is the **operator's attention**, so the agent spends it sparingly.
For an easily-reversible action — a **"two-way door"** (the Amazon framing) — the agent
**just does it and reports the call**, rather than pausing to ask: a question has a real
cognitive cost, and leaving reversible work *hanging* (uncommitted, deferred, "I'll ask
first") adds load *and* drift risk for no benefit (tenets 1/11 want it committed, not
pending). The operator's deliberate decision is reserved for **one-way doors** —
irreversible or expensive-to-undo: spend, vendor lock-in, data deletion, history rewrites,
anything in tenet 12/15's scope — and for genuine matters of taste (a brand name, a spend
ceiling). This is **bias for action, bounded by reversibility**; it sharpens the `AGENTS.md`
"lead, don't quiz / pre-make every mechanical decision" rule and complements tenet 13 (stay
on the critical path without constant check-ins).

**Classify by the irreversibility of the *effect*, not of the code.** This is the
sharp edge that's easy to get wrong: a perfectly reversible *artifact* — a script, a
config, a `compose` change, all removable by a clean `git revert` — can still **encode an
irreversible *effect*** on data. A retention policy that *deletes* old backups, a
destructive whole-DB restore/overwrite, a `DROP`/`TRUNCATE`, a `--force` push, a TTL that
expires records — the revertibility of the *code* says nothing about the recoverability of
the *data it destroys*. **When code creates, deletes, or overwrites data — or sets the
policy that later will (retention counts, overwrite-without-snapshot, expiry windows) —
treat the data-loss semantics as a one-way door** needing operator sign-off, even though
the lines delivering them revert trivially. The test is "if this runs, can I get the data
back?", not "can I delete the script?". (Added 2026-06-08 after a backup/restore review
found destructive-restore + delete-on-prune semantics had been auto-made as "mechanical
defaults" because the *scripts* were reversible — ADR 023.)

Operating rules:
- **Two-way door → act, then report.** Commit every session (never leave changes hanging),
  pick a reasonable default (naming, formatting, structure, ordering), proceed — and *state
  the call* so it's visible and trivially reversible. A clean revert is the safety net.
  Do **not** introduce "operator will inspect/commit" gates for routine code: the operator
  reviews decisions and outcomes, while the agent owns reversible implementation,
  verification, and commits.
- **One-way door → stop and get a conscious go/no-go.** Money committed, lock-in entered,
  data/ history destroyed, scope materially changed, or any tenet-12/15-class decision —
  **including data-loss semantics delivered by otherwise-reversible code** (destructive
  restore, delete-on-prune retention, expiry/TTL): surface the *effect* for sign-off, not
  just the diff.
- **When genuinely unsure which it is, ask the cheap question once** — but default to
  action whenever the cost of being wrong is a quick `git revert`.

This is the *attention* corollary of tenet 7 (fewer moving parts): don't spend the
operator's focus on a decision that a revert can undo. **Reversibility of the effect, not
of the code — and not seniority — decides whether the agent acts or asks.**

## 18. Burn-in before hardening — defer non-critical cleanup to a tracked post-launch pass
When a system first goes live, it is legitimate to keep a few **convenience and
diagnostic affordances** that make the shake-out period easier — a credential note kept
handy for fast admin-UI logins, more verbose logging, a looser setting that aids
debugging. Ripping all of it out on day one optimises for a tidiness that nobody is
benefiting from yet, while the operator is still learning the live system's failure
modes. So we **run the system in first, then harden it** — the SRE "burn-in" idea: let
real usage (~a week) expose the rough edges, *then* do a deliberate cleanup/hardening
pass once the system has earned trust.

The discipline is **not** "skip the cleanup" — it's that the cleanup is **explicit,
tracked, and time-boxed**, never left to memory:

- **Park it, don't drop it (tenet 13).** Any deferred cleanup goes into
  `docs/planning/BACKLOG.md` as a concrete item with a trigger ("after ~1 week of full
  usage") — so it cannot silently rot into permanent tech/security debt.
- **Time-box the deferral.** "Later" means a named milestone (post-burn-in), not
  "someday". The whole point of burn-in is that it *ends*.
- **Never defer a real, active risk.** Burn-in covers *convenience scaffolding and
  cosmetic debt*, not live exposures: anything that is actively exploitable, or a
  one-way door (secrets reaching git history, data loss, public exposure) is fixed
  **now**, not parked. When in doubt, treat it as active and fix it.
- **Schedule the sweep.** The post-burn-in pass is itself a planned session (a STATUS
  "Next action"), not an afterthought — it removes the parked affordances, tightens
  settings, and closes the burn-in backlog items as a batch.

This complements tenet 13 (capture-don't-chase: the deferral is a conscious park, not
drift), tenet 14 (the backlog item is the Detect/Mitigate record), and tenet 7
(don't pay maintenance/attention cost before the value is real). The line it draws —
*reversible convenience may wait for burn-in; active risk and one-way doors may not* —
is the same reversibility test as tenet 17, applied to **cleanup timing**.

## 19. Vector store ≠ dedup; timeout ≠ failure on async memory writes
The pgvector index is a **retrieval** layer — it stores embeddings so `/search` can
find relevant memories. It is **not** a deduplication engine. Deduplication happens in
two places with different jobs:

1. **Write-time (online):** Mem0's extraction pipeline chooses ADD / UPDATE / DELETE by
   comparing new facts against *already-indexed* near neighbors via the LLM.
2. **Offline compaction:** `scripts/memory_compaction.py` clusters semantic near-dupes
   for **human review** (first pass is never unsupervised auto-merge — some near-dupes
   are intentionally distinct facts).

**Never reword on retry.** Rewording changes the content hash, bypasses exact-hash dedup,
and defeats the write-time neighbor check when the original is not yet indexed. Bulk and
scripted writes must carry a stable `metadata.external_id` and use
`scripts/bulk_seed_importer.py`, which checks existence before write.

**`infer=True` writes are async-commit.** A client read timeout is **not** proof the
write failed — Mem0 may commit extraction seconds later. On timeout: poll for the
`external_id` (or original verbatim text), then skip if found; if not found after the
verify window, surface `timeout_unverified` and stop — do not retry with new wording
(ADR 037; COE 2026-06-10-mcp-timeout-semantic-duplicates).

## 20. Event time, namespace, and inline entity qualifiers
**Store event time in metadata.** `created_at` is capture/write time only. When the
fact or decision actually happened, carry `event_date` (ISO date) in metadata — dual-write
`occurred_at` for ADR 029 compatibility. "What is the current status of X?" resolves by
**`max(event_date)`** among candidates, never by most recently written row.

**Namespace is a flat tag** on the single `user_id=primary-user` bank: `public` (default)
or `sensitive`. Reads default to `namespace=public`; sensitive reads require an explicit
filter.

**Qualify entities inline** in fact text (`Jordan, project contact` vs
`Jordan, project contact` vs `Jordan, team lead's sibling`) — vector retrieval cannot disambiguate bare tokens.
Read paths may rerank by qualifier overlap (`src/memory/retrieval.py`).

**Acceptance before bulk load:** run `scripts/acceptance_probe.py` — 5 throwaway facts,
3 contract queries, cleanup — and fix the contract if any query fails (ADR 037).
<!-- generated:tenets-full end -->
