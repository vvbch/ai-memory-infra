# COE: Concierge and handoff controls regressed after prior correction

- **Date:** 2026-06-09
- **Author(s):** the operator (detected), Cursor agent (analysis + fix)
- **Severity:** high *(no production/customer/data impact, but repeated governance failure after an earlier COE; operator attention and trust were directly affected)*
- **Status:** closed
- **Related:** tenets 14, 16, 17; `AGENTS.md`; `docs/coe/2026-06-09-session-handoff-omission.md`

## Summary

After repo-health passed and the MCP environment variable was confirmed, the agent
gave a vague instruction: reload Cursor and "confirm the `ai-memory` MCP server
appears." It did not provide the exact Cursor UI path, the purpose of the step,
or the visible success condition, and it printed a fresh-session resume prompt
even though the stage had not been checkpointed into `STATUS.md`, logs, or git.

This is a regression, not a novel miss. The previous COEs had already identified
human-caught handoff failures and prose-only final gates. The new failure shows
that the control plane still depended on agent recall instead of a mandatory
operator-action and final-response mechanism.

## Impact

- Operator cognitive load increased at exactly the point where concierge mode is
  supposed to reduce it.
- The operator had to interrupt and correct the process again, consuming paid
  agent turns and attention.
- No secrets, production data, or live service behavior were affected.
- Governance impact is high because this repeated after multiple COEs and after
  the control plane already said not to do it.

## Timeline

- `2026-06-09 00:22 IST` — Agent resumed Phase 4, read `STATUS.md` and
  `AGENTS.md`, and ran repo-health green.
- `2026-06-09 00:23 IST` — Agent confirmed `AI_MEMORY_API_KEY` was set in the
  user environment and `ai-memory-mcp` resolved on PATH.
- `2026-06-09 00:24 IST` — Agent told the operator to reload Cursor and confirm
  the MCP server appeared, without exact UI instructions.
- `2026-06-09 00:24 IST` — Agent printed a fresh-session resume prompt without
  updating `STATUS.md`, build logs, or committing/pushing a checkpoint.
- `2026-06-09 00:25 IST` — Operator detected the regression and requested COEs,
  updates to prior COEs, and industry benchmarking.
- `2026-06-09 00:38 IST` — After the correction was committed, operator confirmed
  Cursor listed the workspace `ai-memory` MCP server and caught one more edge case:
  the final answer still printed a resume prompt while waiting on an operator UI
  action in the same active flow.

## Detection

Human catch by the operator. This is the same detection gap as prior handoff
COEs: the agent had the rules in context but no mechanical gate forced them into
the final response. A human catch after a repeat incident means the previous
Detect actions were not strong enough or were left too low-priority.

## Industry benchmark

- **AWS/Amazon COE benchmark:** a COE is not just a write-up; it is a mechanism to
  prevent recurrence, using blame-free 5 Whys, named action owners, and corrective
  actions. AWS guidance explicitly warns not to stop at "human error"; ask why
  the system allowed the error.
- **Google SRE postmortem benchmark:** a useful postmortem is written,
  blameless, shared, and produces action items that improve prevention,
  detection, mitigation, coordination, or communication. Repeated incidents are
  signals for trend analysis and stronger systemic controls.
- **Gap against benchmark:** the project met the written/blameless standard, but
  failed the recurrence-prevention standard. Prior actions stayed as prose gates
  and backlog items; they did not create a blocking mechanism for final answers
  or operator-delegated steps. That is why the same class of failure resurfaced.

## Root cause — 5 Whys

1. **Why did the agent give a vague MCP-check instruction?** It treated the next
   action as a simple status check instead of an operator-facing console/UI task.
2. **Why did concierge mode not trigger?** `AGENTS.md` described concierge
   behavior, but did not require a fixed operator-action format with purpose,
   exact path, visible success condition, and a wait point.
3. **Why was a resume prompt printed at the wrong time?** Tenet 16 said to end
   every response with a resume prompt, so the agent followed the words
   mechanically even though no logical checkpoint had been written to repo state.
4. **Why did this repeat after earlier COEs?** Earlier corrective actions
   sharpened prose rules but left the final-response verifier and all-repo
   handoff checker as backlog work.
5. **Why were prose rules insufficient?** **Root cause (systemic):** the control
   plane still relied on agent memory and instruction-following at the exact
   moment of highest failure risk: final response / handoff. There was no
   mandatory, local checklist that blocked a final answer unless the operator
   step was concierge-formatted and the repo was checkpointed or explicitly
   declared mid-step.

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| Add this regression COE and index it | Prevent | Cursor agent | 2026-06-09 | Done |
| Add an `Industry benchmark` section to the COE template and retrofit all existing COEs | Prevent / Detect | Cursor agent | 2026-06-09 | Done |
| Update `AGENTS.md` and `docs/tenets.md`: operator-delegated actions must use a concierge action format (purpose, exact UI/command, visible success, wait) | Prevent | Cursor agent | 2026-06-09 | Done |
| Update `AGENTS.md` and `docs/tenets.md`: a resume prompt is valid only after a logical checkpoint is written; mid-step responses must say no resume prompt is available yet | Prevent | Cursor agent | 2026-06-09 | Done |
| Tighten `AGENTS.md` and `docs/tenets.md`: no resume prompt while waiting on the operator to perform the next action in the same active flow, even if the checkpoint is current | Prevent | Cursor agent | 2026-06-09 | Done |
| Promote the final all-repo handoff verifier from P2 to P1 because the failure repeated after a COE | Detect | Cursor agent | 2026-06-09 | Done |
| Update `STATUS.md`, public build journey, and private build log, then run repo-health, commit, and push touched repos | Mitigate | Cursor agent | 2026-06-09 | Done |

## Lessons learned

Repeated agent non-adherence means the control is not strong enough. The fix is
not a louder instruction; it is a narrower mechanism at the failure point:
operator actions must be formatted like runbook steps, and final answers must be
blocked unless the workspace is either checkpointed or explicitly mid-step.

The industry benchmark reframes the miss: a COE that does not prevent recurrence
has not finished its job. Blamelessness prevents shame; mechanisms prevent
repeat incidents. We need both.
