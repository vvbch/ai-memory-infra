# COE: Completion gate was model-dependent (prose, not a mechanism)

- **Date:** 2026-06-09
- **Author(s):** Cursor agent
- **Severity:** Medium
- **Status:** closed
- **Related:** Tenets 1, 2, 11, 14, 16, 17; ADR 027; `AGENTS.md`;
  `.cursor/hooks.json`; `.cursor/hooks/completion_gate.py`. Third in a series:
  `2026-06-08-atomic-handoff-failure.md`, `2026-06-09-session-handoff-omission.md`,
  `2026-06-09-concierge-handoff-regression.md`.

## Summary

When the operator switched the agent model to **GPT-5.5 (reasoning = high)**, the
session ended without committing/pushing work to origin, despite the completion
gate being spelled out in `AGENTS.md`. This is the same commit/push-omission
class as three prior COEs, but the new signal is decisive: the gate's adherence
**varies by model**, so a prose rule executed by the LLM can never be a guarantee.
The fix escalates the gate from prose to a **harness-level Cursor `stop` hook**
that fires on every turn-end regardless of model.

## Impact

No production data or secrets exposed. The impact was control-plane and operator
trust: verified work was left local/unpushed (Drive-sync blast-radius risk per
tenet 11), and the operator had to manually catch the omission — again — which is
exactly the cognitive load tenet 17 exists to remove. The recurring nature added
frustration and eroded confidence that "done" means "pushed."

## Timeline

- `2026-06-08 → 2026-06-09` — Three prior COEs document commit/push-omission and
  twice promote a "final all-repo handoff verifier" (P2 → P1), but the control
  stayed mostly prose (sharpened `AGENTS.md` wording).
- `2026-06-09` — Operator runs a session on GPT-5.5 (reasoning = high); the agent
  finishes without committing/pushing to origin.
- `2026-06-09` — Operator reports the model-switch correlation and asks for a
  deterministic fix (hooks vs git hooks vs skills vs workflows) plus industry
  research and a plan.
- `2026-06-09` — Implemented the deterministic completion gate: `stop` hook +
  `completion_gate.py`; ADR 027; tenet/AGENTS sharpening.

## Detection

Human catch by the operator, for the fourth time in this class — a strong
detection-gap signal. The prior "Detect" action (sharpen the prose gate / promote
a verifier) was too weak because it still depended on the model choosing to run
git. The new Detect/Prevent control is mechanical and model-independent.

## Industry benchmark

- **AWS/Amazon COE:** blame-free 5-Whys to a systemic cause, owners/dates,
  recurrence prevention. The prior COEs documented well but failed the
  recurrence-prevention bar (the same class recurred across model switches). This
  COE meets it by moving the control off the LLM's judgment entirely.
- **Google SRE postmortem:** actions must improve prevention/detection, not just
  describe. Replacing a prose checklist with a harness hook is the textbook move
  from "tell the human/agent to remember" to "make the system enforce it."
- **Agent-tooling benchmark (web-verified, tenet 8):** the convergent industry
  pattern is a **`stop` hook**. GitButler uses Cursor's `stop` hook as its commit
  signal and states plainly that *hooks are deterministic while rules/MCP are
  non-deterministic because the LLM runs them*
  ([GitButler](https://blog.gitbutler.com/cursor-hooks-deep-dive)). Claude Code's
  canonical auto-commit is a `Stop` hook
  ([BleepingSwift](https://bleepingswift.com/blog/claude-code-auto-commit)), and
  `agent-better-checkpoint` ships exactly the layered model — a SKILL (soft) plus
  a `stop` hook (deterministic safety net)
  ([repo](https://github.com/alienzhou/agent-better-checkpoint)). Cursor's own
  team confirms git-rule adherence is a known, model-dependent weakness
  ([forum](https://forum.cursor.com/t/cannot-instruct-agent-to-auto-commit/155811)).

## Root cause — 5 Whys

1. Why was the work not committed/pushed under GPT-5.5-high? → The model did not
   execute the commit/push step that the completion gate requires.
2. Why didn't it execute it? → The gate lives as prose in `AGENTS.md`, which is
   advisory context the LLM must *choose* to act on.
3. Why does choosing vary? → Instruction adherence is model-dependent; a
   different model weighted the standing authorization differently (confirmed as a
   known Cursor behavior, not a config error).
4. Why was prose ever expected to be deterministic? → Prior fixes treated the
   problem as "wording not strong enough" rather than "wrong enforcement layer."
5. Why was the wrong layer chosen? → **Root cause (systemic):** the project had no
   *harness-level* enforcement point; every control (rules, skills, AGENTS.md, even
   the git pre-commit hook) either runs inside the LLM's judgment or only fires
   *after* a commit is already initiated — none could deterministically *trigger*
   the commit/push independent of the model.

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| Add Cursor `stop` hook (`.cursor/hooks.json`) running `completion_gate.py` that detects dirty/unpushed repos and forces DoD completion via `followup_message`, model-independent | Prevent + Detect | Cursor agent | 2026-06-09 | Done |
| Fail-loud after the loop cap (operator-facing blocker report) instead of silently capping | Mitigate | Cursor agent | 2026-06-09 | Done |
| Record the decision + determinism ladder + alternatives in ADR 027 | Prevent | Cursor agent | 2026-06-09 | Done |
| Name the `stop` hook as the *hard* layer of the completion gate in tenet 11 + AGENTS.md (prose becomes the happy path, not the guarantee) | Prevent | Cursor agent | 2026-06-09 | Done |
| Close the long-promised "repo handoff verifier" (P1) — this hook is its deterministic implementation | Detect | Cursor agent | 2026-06-09 | Done |
| Commit + push every touched repo this session and verify via the new gate | Mitigate | Cursor agent | 2026-06-09 | Done |

## Lessons learned

**Determinism is a property of the execution layer, not the wording.** Rules,
skills, AGENTS.md, and slash-workflows are all executed by the LLM, so their
adherence is model-dependent by construction; git hooks are deterministic but only
*validate* a commit already in flight — they cannot *initiate* one. The only layer
that can guarantee an action happens regardless of model is the **harness
lifecycle hook**. When you need "this must always happen," move it off the model's
judgment and onto the harness. The soft layer (prose/skill) then exists only to
make the deterministic layer rarely needed — not to be the guarantee.

This is the transferable interview lesson (mirrored to `interview_packet.md`):
*four human catches of the same class proved the fix had to change layers, not
wording.*
