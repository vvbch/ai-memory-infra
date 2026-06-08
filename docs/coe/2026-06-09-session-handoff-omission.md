# COE: Session handoff omitted commit/push and resume prompt

- **Date:** 2026-06-09
- **Author(s):** Cursor agent
- **Severity:** Medium
- **Status:** actions-in-progress
- **Related:** Tenets 1, 14, 16, 17; `AGENTS.md`; `docs/planning/STATUS.md`

## Summary

After completing and verifying Phase 4 local MCP work, the agent ended the response
without committing/pushing touched repos and without an explicit copy-paste resume
prompt / fresh-session instruction. This violated the repo's standing completion
gate and stateless-session rule, even though the code and docs were verified.

## Impact

No production data or secrets were exposed. The impact was control-plane risk:
verified work was left local, the next session would have had to infer state from
an unpushed working tree, and the operator had to catch the missing fresh-session
handoff manually. Parent-workspace pointer files were also created outside a git
repo, so their live copies cannot be pushed even though their intent is now
documented in the control plane.

## Timeline

- `2026-06-08 23:56 IST` — Session resumed Phase 4 and added parent-workspace pointers.
- `2026-06-09 00:11 IST` — Final verification green: ruff, mypy, pytest, repo-health.
- `2026-06-09 00:12 IST` — Agent ended with "did not commit because you didn't explicitly ask" and no resume prompt.
- `2026-06-09 00:12 IST` — Operator detected the violation and requested a COE plus correction.

## Detection

Human catch by the operator. That is a detection gap: the agent had the repo's
completion gate in context, but there was no mechanical final-response checklist
forcing it to verify pushed commits and include the fresh-session prompt before
answering.

## Root cause — 5 Whys

1. Why was the work not committed/pushed? → The agent followed a generic tool-policy habit ("only commit when explicitly asked") instead of the repo-specific standing authorization already in `AGENTS.md`.
2. Why did the generic habit win? → The final response was written from memory after verification, without re-checking the repo's completion-gate lines.
3. Why was the resume prompt omitted? → The final-response path did not have an explicit, local checklist for tenet 16, even though the DoD states it.
4. Why did parent workspace files remain unpushed? → The parent `ai-memory` workspace is not itself a git repo, so files placed there are live local context but not versioned artifacts.
5. Why was this not caught before final? → **Root cause (systemic):** final handoff relied on agent recall rather than a mandatory checklist covering pushed commits, non-versioned artifacts, and the copy-paste resume prompt.

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| Add this COE and index it | Prevent | Cursor agent | 2026-06-09 | In progress |
| Sharpen `AGENTS.md`: final response is blocked until touched repos are committed/pushed or blockers are named, and a copy-paste resume prompt is included | Prevent | Cursor agent | 2026-06-09 | In progress |
| Update `STATUS.md` with the correction and next fresh-session instruction | Mitigate | Cursor agent | 2026-06-09 | In progress |
| Commit and push `ai-memory-infra` and `ai-memory-infra-private` after repo-health | Mitigate | Cursor agent | 2026-06-09 | In progress |
| Park/implement a final all-repo handoff verifier that detects uncommitted/unpushed touched repos and missing resume prompt | Detect | Cursor agent | Backlog P2 | Open |

## Lessons learned

Repo-local standing authorization must override generic agent habits when the user
has already agreed to that working model. "Done" is not just tests green; it is
state transfer: pushed commits, documented exceptions, and a fresh-session resume
prompt so the next chat starts cheaply and correctly.
