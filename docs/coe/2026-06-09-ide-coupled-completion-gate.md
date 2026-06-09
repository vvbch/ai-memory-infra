# COE: Fixing the completion gate coupled it to one IDE (and it wasn't loading)

- **Date:** 2026-06-09
- **Author(s):** Cursor agent
- **Severity:** Medium
- **Status:** closed
- **Related:** Tenets 1, 2, 3, 16; ADR 027 (the fix this COE corrects); ADR 030
  (the systemic fix); ADR 018 (thin editor pointers); ADR 015 (installer model).
  Operator-caught immediately after ADR 027 shipped.

## Summary

ADR 027 escalated the completion gate from prose to a deterministic harness hook —
the right call — but implemented it as `ai-memory-infra/.cursor/hooks/
completion_gate.py` + `.cursor/hooks.json`. That **(a)** coupled the project's
load-bearing handoff guarantee to Cursor, violating **tenet 2** (editor-agnostic,
no tool lock-in), and **(b)** placed it in a directory the open workspace root
never loads: Cursor reads *project* hooks from `<workspace root>/.cursor/`, and
this workspace's root is the parent `ai-memory`, not the `ai-memory-infra` repo. So
the "hard layer" was almost certainly **inert**. The operator caught the tenet-2
violation directly ("I don't want Cursor to hold these hooks — they should be IDE
independent… in the process of this COE, you violated another tenet?").

## Impact

No production data or secrets exposed; control-plane only. Two harms: (1) the
deterministic guarantee promised by ADR 027 was likely not firing (a false sense
of safety — the exact recurrence ADR 027 existed to end could still happen); (2)
the project's portability tenet was breached in the very change that was supposed
to *strengthen* the control plane. Operator trust cost: a fix-introduced-a-defect
loop.

## Timeline

- `2026-06-09` — ADR 027 ships the gate inside `ai-memory-infra/.cursor/`.
- `2026-06-09` — Operator objects that the gate is Cursor-coupled (tenet 2) and
  asks for IDE-independent hooks; also asks for an IDE **startup** hook to stop the
  per-session control-plane rediscovery from burning tokens (tenet 16).
- `2026-06-09` — Investigation (web-verified, tenet 8) confirms Cursor loads
  project hooks from the workspace root, not a sub-repo's `.cursor/`; the existing
  hook was in the wrong place. Implemented ADR 030.

## Detection

Human catch by the operator, on review of the just-shipped ADR 027 — fast, but the
defect should not have shipped. The miss was self-documented: ADR 027 listed
"Cursor-only" under *Limitations* rather than treating it as a blocking tenet-2
violation. Demoting a tenet breach to a footnote is the detection gap.

## Industry benchmark

- **AWS/Amazon COE:** a corrective action that introduces a new defect of equal
  class is a recurrence; the bar is fixing the *systemic* enabler. Here that's "a
  control was placed on a layer without checking it against the portability tenet
  *and* without verifying it actually loads."
- **Google SRE postmortem:** actions must be verified, not assumed. ADR 027 said
  "verify in the Hooks tab" but the verification of *loading at this workspace
  root* was never done — the classic "assumed the mechanism was active" postmortem
  finding.

## Root cause — 5 Whys

1. Why was the gate Cursor-coupled and not loading? → It was written into
   `ai-memory-infra/.cursor/`, a Cursor-specific path that isn't the open root.
2. Why there? → "Make it a deterministic harness hook" was conflated with "put it
   in a Cursor file," and `ai-memory-infra` was assumed to be the hook root.
3. Why was that assumption unchecked? → No verification that Cursor loads hooks
   from the parent workspace root vs a sub-repo; the ADR reasoned about determinism
   but not about *discovery/placement*.
4. Why did the tenet-2 conflict get rationalized instead of blocking? → The DoD
   has no explicit "does this control plane change couple us to one editor?" gate;
   "editor-agnostic" was treated as advisory prose, not a checklist item.
5. **Root cause (systemic):** the project had a pattern for portable *content*
   (thin editor pointers, ADR 018) and portable *git hooks* (installer, ADR 015),
   but **no pattern for portable harness/lifecycle hooks** — so the first one was
   placed ad hoc, in the wrong layer and the wrong directory.

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| Move gate logic to editor-agnostic `scripts/completion_gate.py`; delete `ai-memory-infra/.cursor/hooks*` | Mitigate | Cursor agent | 2026-06-09 | Done |
| Establish the portable harness-hook pattern: canonical `scripts/` logic + thin per-IDE adapters generated at the workspace root by `scripts/install_ide_hooks.py` (ADR 030) | Prevent | Cursor agent | 2026-06-09 | Done |
| Apply the same pattern to the new `sessionStart` bootstrap (`scripts/session_bootstrap.py`) so the first use of the pattern is a *pair*, proving it generalizes | Prevent | Cursor agent | 2026-06-09 | Done |
| Verify both hooks fire from the real workspace root (tested gate fail-loud + bootstrap injection from `ai-memory/`) | Detect | Cursor agent | 2026-06-09 | Done |
| Name the portability requirement in tenet 11 + AGENTS.md ("hooks are portable, not Cursor-owned") so the next hook follows the pattern | Prevent | Cursor agent | 2026-06-09 | Done |

## Lessons learned

**"Deterministic" is not the same as "in a Cursor file."** A harness lifecycle
event is inherently per-harness, so the only portable design is *editor-agnostic
logic + a thin, generated per-IDE adapter* — the same shape the repo already uses
for editor pointer content (ADR 018) and git hooks (ADR 015). And **a control you
can't show firing is not a control**: placement and load-verification are part of
shipping a mechanism, not an afterthought. The transferable interview lesson
(mirrored to `interview_packet.md`): *a corrective action must be checked against
the rest of the tenets and actually verified live — a fix that breaks portability
or never loads is a new incident, not a closed one.*
