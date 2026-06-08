# COE: Cursor rules file drifted from canonical context

- **Date:** 2026-06-07
- **Author(s):** Chandra (detected), agent (analysis + fix)
- **Severity:** low *(internal governance artifact; no production/customer impact)*
- **Status:** actions-in-progress
- **Related:** ADR 018 · tenets 2, 10, 14 · `.cursor/rules/00-project.mdc`

## Summary

`.cursor/rules/00-project.mdc` had accumulated a **duplicated summary of the
project tenets/rules** from `AGENTS.md`, violating tenet 2 (editor files are thin
pointers) and tenet 10 (single source of truth / no drift). The file even
contained the line *"Do not duplicate AGENTS.md content into rules"* while doing
exactly that, and had just drifted further when a tenet-13 bullet was added to it.

## Impact

No production or customer impact (this is agent-context tooling). The real risk:
the agent could act on a **stale or divergent** copy of the rules, and the drift
was growing turn over turn. Confidence-in-governance impact > technical impact.

## Timeline

- (pre-existing) — `00-project.mdc` authored with an inlined rules summary.
- 2026-06-07 — a tenet-13 bullet was added to the pointer file, extending the drift.
- 2026-06-07 — **operator (Chandra) caught it** and asked for a root-cause + fix.
- 2026-06-07 — control plane fixed (tenet 2 boundary + DoD row), then data plane
  (file stripped to a pure pointer); ADR 018 recorded.

## Detection

**A human caught it**, not any automated control — that is itself a detection gap.
The no-drift machinery (DoD) did not cover pointer files, so nothing flagged the
duplication. → see the Detect action below.

## Industry benchmark

- **AWS/Amazon COE benchmark:** treat the issue as a mechanism failure and keep
  asking why until the missing control is visible. This COE meets that bar: the
  root cause is "meta-artifacts were ungoverned," not "someone copied text."
- **Google SRE postmortem benchmark:** a useful postmortem records impact,
  timeline, root cause, and follow-up actions that prevent recurrence. This COE
  has those elements and pushed the prevention fix into tenet 2 / ADR 018.
- **Benchmark gap:** the Detect action stayed parked as lint/backlog work. That
  was acceptable for low blast radius pointer drift, but later handoff COEs show
  that high-repeat governance failures need stronger detection priority.

## Root cause — 5 Whys

1. **Why did the rules file contain duplicated content?** A "helpful summary" was
   inlined so the agent would see rules without opening `AGENTS.md`.
2. **Why inline a summary instead of a pointer?** Defensive duplication — a
   perceived reliability gap (*"what if AGENTS.md isn't read?"*) answered by copying
   "to be safe."
3. **Why duplication instead of one enforced pointer?** "Thin pointer" was never
   **defined** — the pointer/content boundary was left to interpretation.
4. **Why no boundary/enforcement?** Tenet 2 stated the *principle*, but the
   **Definition of Done had no trigger for pointer files** — they weren't governed
   artifacts, so nothing kept them pointers or flagged drift.
5. **Why were pointer files outside DoD scope?** **Root cause (systemic):** the
   no-drift machinery was scoped to fact-restating docs and treated pointer files
   as inert plumbing. The **meta-artifacts that govern behaviour were themselves
   ungoverned** — a control-plane blind spot. Convenience filled the vacuum.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| Define "thin pointer" boundary precisely in tenet 2 (zero canonical content; not a symlink) | Prevent | agent | 2026-06-07 | ✅ done |
| Add DoD trigger row for editor pointer files; fix the "A tenet" row wording that invited duplication | Prevent | agent | 2026-06-07 | ✅ done |
| Strip `00-project.mdc` to a pure pointer | Mitigate (fix instance) | agent | 2026-06-07 | ✅ done |
| Record the decision + analysis (ADR 018, this COE) | Prevent | agent | 2026-06-07 | ✅ done |
| Codify the COE practice itself (tenet 14 + `docs/coe/`) | Prevent | agent | 2026-06-07 | ✅ done |
| Automated pointer-lint / generate pointers from `AGENTS.md` (close the **detection** gap) | Detect | Chandra+agent | Phase-1 CI | ⏳ backlog P2 |

## Lessons learned

**A stated principle is not a control — you must define the boundary and enforce
it; and the meta-artifacts that govern a system are artifacts too.** Fixing the
control plane (spec + DoD) before the data plane (the file) is what stops the
instance regenerating. Mirrored into `interview_packet.md` §7. Detection-layer
follow-up parked in `BACKLOG.md` (P2).
