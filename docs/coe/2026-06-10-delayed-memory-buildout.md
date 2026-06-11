# COE: Delayed execution of memory buildout

- **Date:** 2026-06-10
- **Author(s):** the operator + Cursor agent (joint — shared systemic ownership, blameless per tenet 14)
- **Severity:** medium *(no production/data/customer impact; opportunity-cost + credibility blast radius — half the build plan is unbuilt scaffolding and the core premise is still untested ~5 weeks in)*
- **Status:** actions-in-progress
- **Related:** tenets 7, 13, 16; AGENTS.md "Build phases" (0-9); `docs/planning/STATUS.md`;
  baseline scan `docs/reports/weekly-scan/2026-06-10-baseline.md`;
  COEs `2026-06-08-cursor-credit-exhaustion.md`, `2026-06-10-status-snapshot-log-drift.md`;
  pivot commit `f9b7f34`; ADR 005; BACKLOG P1 `[docs-drift]`.

## Summary

Across ~5 weeks the project built a strong control plane and infra phases 0-4 (live,
proven), but **phases 5-8 of the canonical plan — migration, LifeGraph, eval, observability —
are still empty 1-line stubs in `src/`**, the flagship knowledge-graph capability (ADR 005)
is undeployed and over-claimed in canonical docs, and the **core product premise (is this
memory layer genuinely useful?) has never been tested**. Effort was disproportionately spent
governing and polishing the build instead of executing the memory buildout and validating it.

## Impact

- **Opportunity cost, not an outage.** No production, data, customer, or security impact.
  The cost is time and confidence: ~5 weeks in, the question that decides whether phases 5-8
  are worth building at all is still open.
- **Misleading progress surface.** 26 of 28 `src/` modules are comment-only stubs; the 80%
  coverage gate and "implemented" impression run ahead of reality (baseline scan §Redundancy).
- **Doc-vs-reality drift accumulated** (Neo4j "dual namespace", stale model fallback, 4 CI
  stub workflows red on every push) because polish/governance moved faster than the code it
  describes.
- **Budget pressure compounded it** (see credit-exhaustion COE): expensive sessions made each
  unit of execution costlier, biasing work toward cheap doc/governance edits over build.

## Timeline

- `~2026-05` → `2026-06-07` — design + accounts + Phase 0/1 (scaffold, IaC). Architecture
  pivoted three times before code (`architecture-evolution.md`).
- `2026-06-08` — Phase 2 (backup/restore) expands from one plan line into two ADRs + ~8
  sessions; credit-exhaustion COE forces a working-model rewrite (tenet 16).
- `2026-06-08 → 09` — Phase 3 (extension) + Phase 4 (MCP) land, interleaved with **four
  handoff COEs** and the personas pre-build gate.
- `2026-06-09` — human pivot to "utility-first" Daily Driver v0 (`f9b7f34`), superseding
  further skills work — the correct turn toward validation.
- `2026-06-10` — control-plane hardening (STATUS gate, CI, weekly scan, interview packets);
  baseline scan + this retrospective surface that phases 5-8 are unstarted and the premise
  is untested.

## Detection

**Human-prompted, via a skeptical retrospective** — not by any standing control. There is no
mechanism that tracks "plan phases declared vs. actually implemented in `src/`," so stub-only
phases never raised a flag while governance artifacts multiplied. A human catch on schedule
drift is itself a detection gap → see Detect actions.

## Industry benchmark

- **AWS/Amazon COE:** find why the *operating system* allowed the drift, not who was slow.
  Met: the root cause is a missing execution-vs-governance balance signal, not "we were lazy."
- **Google SRE postmortem:** blameless, with actions that improve prevention/detection. Met;
  framed as shared systemic ownership.
- **Lean/Agile (WIP limits, vertical slices, validated learning):** the failure mode is
  classic — broad horizontal scaffolding + process investment ahead of a thin vertical slice
  that proves value. The corrective (premise test first, build phases 5-8 only on a proven
  premise) is the textbook fix: pull-based work gated on validated learning.

## Root cause — 5 Whys

1. **Why are phases 5-8 still stubs ~5 weeks in?** Execution time went to control-plane
   hardening, governance COEs, extension debugging, and docs/polish instead of building the
   memory features.
2. **Why did effort skew to governance/polish?** Those tasks are cheap, low-risk, and
   visibly "productive" — and several were *forced* by repeated handoff/credit failures
   (10 COEs). The agent optimizes per-session for completable, reversible work; the operator
   green-lit each as individually reasonable.
3. **Why did individually-reasonable choices add up to a stalled buildout?** No one was
   tracking the aggregate — there was no "are we executing the plan or grooming it?" signal.
   `STATUS.md` tracks the *next action*, not *plan-phase implementation vs. claim*.
4. **Why no such signal?** The Definition of Done governs per-change doc consistency, not
   program-level progress; "scaffold a phase" and "implement a phase" both look like activity.
   Scaffolding even inflated the metrics (coverage denominator), hiding the gap.
5. **Why did the project tolerate that?** **Root cause (systemic):** the operating model
   rewards *correctness and governance of the build process* but has **no countervailing
   force toward validated execution** — no WIP discipline, no premise-first gate, no
   plan-vs-reality check. Both parties contributed: the agent defaulted to safe governance
   work and baked unverified claims (mem0 graph, model defaults) that later needed repair;
   the operator added scope (personas gate, weekly scan, 5 interview packets, multi-editor
   portability) and deferred the premise test. Neither side held a "build the product, prove
   it, then harden" line.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| **Run the Phase 3 premise test before any phase 5-8 build** — real todos + recruiter reachouts, "plan my day" for several days, write a verdict on genuine utility | Mitigate (unblock value) | the operator (+agent) | next 1-2 sessions | ⏳ |
| Add a **plan-vs-reality gate**: a check (or STATUS section) that lists each build phase as `stub` / `partial` / `implemented` from `src/`, so a stub-only phase can't read as progress | Detect | agent | next session | ⏳ |
| **Freeze new governance/portfolio scope** (weekly-scan agent, extra interview packets, more editor adapters) until the premise test returns a verdict — WIP limit of one build track | Prevent | the operator | now | ⏳ |
| Fix the drift that polish outran: correct Neo4j "dual-namespace" claim, delete the 4 red stub workflows, add a boot-time assert on `MEM0_DEFAULT_LLM_MODEL` | Mitigate | agent | next session | ◑ Neo4j claim corrected 2026-06-10 (ADR 032); stub workflows handled in the maturity-honesty pass same date; `MEM0_DEFAULT_LLM_MODEL` boot-assert still ⏳ |
| Resolve the **graph-source decision** (LifeGraph-only vs. a mem0 build that ships graph) in an ADR before Phase 6 — it gates ADR 005's cross-namespace promise | Prevent | the operator (one-way-door call) | before Phase 6 | ⏳ |
| Verify facts at source **before** baking them into docs (mem0 graph, model defaults were not) — reaffirm tenet 8 as a pre-doc gate | Prevent | agent | ongoing | ⏳ |

## Lessons learned

**Governing a build is not the same as building it — and a process that only rewards
correctness will quietly optimize toward safe grooming over risky execution.** The
transferable principle: gate further build on *validated learning* (prove the premise with a
thin vertical slice) and keep a standing *plan-vs-reality* signal so horizontal scaffolding and
process investment can't masquerade as progress. Match depth to stakes (tenet 8/13): harden
after value is proven, not before. Shared ownership — the agent must resist defaulting to cheap
governance work and verify facts before documenting them; the operator must hold the
premise-first line and resist additive scope. Mirror to `interview_packet.md`; follow-ups
parked in `BACKLOG.md`.
