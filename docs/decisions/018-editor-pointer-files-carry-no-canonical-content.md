# ADR 018: Editor pointer files carry zero canonical content

**Status:** Accepted
**Date:** 2026-06-07
**Deciders:** Chandra
**Type:** Governance correction (sharpens tenets 2 & 10)

### Context — the defect

`.cursor/rules/00-project.mdc` had grown to contain a **summarized copy of the
hard rules / tenets** from `AGENTS.md`. This violates:

- **Tenet 2** (portable / editor-agnostic): editor-specific files must be *thin
  pointers*, not content.
- **Tenet 10** (single source of truth / no drift): the same rules restated in two
  places will diverge.

The file even contained the line *"Do not duplicate AGENTS.md content into rules"*
**while duplicating it** — a self-contradicting artifact, the clearest possible
signal the governance lacked teeth. It then *did* drift: a tenet-13 bullet was
added to the pointer file in a prior step, extending the violation. (By contrast,
`CLAUDE.md` was a correct one-line pointer — proof the right pattern existed but
wasn't enforced.)

### Root cause

The full incident analysis (impact, timeline, detection, 5-whys, corrective
actions) is the canonical COE: **`docs/coe/2026-06-07-cursor-rule-drift.md`**. In
one line: the spec defined the *principle* of thin pointers but never the
*boundary* or its *enforcement*, and pointer files were never in the DoD's
scope — so defensive duplication entered the data plane unchecked.

### Decision

Fix the **control plane first, then the data plane** (so the instance can't
regenerate):

**Control plane (the governing spec):**
1. **Define "thin pointer" precisely** in tenet 2: an editor pointer file contains
   *only* the editor's required frontmatter/mechanics **plus** an instruction to
   read `AGENTS.md`. It carries **zero canonical content** — no tenets, rules,
   conventions, or decisions. "Pointer" means a content stub, **not a filesystem
   symlink** (tenet 3 forbids symlinks: Windows-hostile).
2. **Put pointer files in the DoD.** Add a trigger-table row: changing an editor
   pointer file → it must stay a pure pointer; never restate rules. And fix the
   "A tenet" row, whose *"`.cursor/rules` pointer if relevant"* wording had
   *invited* editing the rule — now explicit that pointer files are **not** updated
   with tenet content.

**Data plane (the instance):**
3. Strip `.cursor/rules/00-project.mdc` to a pure pointer (frontmatter + "read
   `AGENTS.md`; this file holds no rules"), removing every duplicated bullet
   (including the tenet-13 bullet that had been added).

### Consequences

- **Positive:** Pointer files can no longer drift from `AGENTS.md`; the rule that
  prevents recurrence is itself versioned and enforced by the DoD. One less place
  to keep in sync (tenet 10).
- **Negative:** The agent must actually read `AGENTS.md` (the original worry). This
  is acceptable: `alwaysApply: true` keeps the "read AGENTS.md" instruction in
  front of the agent every turn, fixing read-reliability *at the mechanism* instead
  of by copying content.
- **Deferred (tenet 13 — parked, not built now):** an automated guard (lint/CI or a
  `check-repo-health` extension) that fails if a pointer file exceeds N lines or
  contains tenet/rule keywords. Documentary control plane (spec + DoD) is the
  minimum that prevents recurrence; the automated check is belt-and-suspenders.

### Lessons (interview-ready)

See `interview_packet.md` §7 STAR bank ("Catching a governance defect…"). The
transferable principle: **a stated principle is not a control — you must define the
boundary and enforce it, and the meta-artifacts that govern a system are artifacts
too.**

---
