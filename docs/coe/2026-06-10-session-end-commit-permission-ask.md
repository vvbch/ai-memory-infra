# COE: Session end asked permission to commit despite standing authorization

- **Date:** 2026-06-10
- **Author(s):** Cursor agent
- **Severity:** Medium
- **Status:** closed
- **Related:** Tenets 1, 10, 14, 16, 17; COE `2026-06-09-session-handoff-omission.md`;
  `AGENTS.md` completion gate; ADR 027 (`completion_gate.py`)

## Summary

After completing ChatGPT registration, consent redirect fix, live verification, and
doc updates, the agent ended with "say if you want that committed and pushed" —
treating session-end commit+push as optional operator confirmation. The workspace
already grants **standing authorization** for reversible completion commits; asking
again added friction and left GitHub behind the live droplet (patched via SCP).

## Impact

No production outage — the droplet was ahead of git. Impact was control-plane /
integrity risk (tenet 11): verified code and docs lived only locally + on the
server until the operator had to remind the agent that commit is routine. Same
class as `2026-06-09-session-handoff-omission.md` (generic "only commit when
asked" habit beating repo rules).

## Timeline

- `2026-06-10 evening IST` — ChatGPT OAuth connected; consent HTML redirect fix
  deployed to droplet via SCP; `search_memories` verified in proxy logs.
- `2026-06-10 evening IST` — Agent updated `architecture.md`, `STATUS.md`,
  `setup.md` locally; ended with optional commit ask.
- `2026-06-10 evening IST` — Operator: "isn't commit part of routine for each
  session? write a COE and take corrective actions."

## Detection

Human catch by the operator — recurrence of a known failure mode documented in
COE 2026-06-09. `completion_gate.py` enforces dirty-repo blocking at turn-end but
does not prevent the agent from *asking* instead of *doing* when the tree is still
clean mid-response.

## Industry benchmark

- **AWS/Amazon COE:** blame-free systemic fix required; this recurrence shows the
  2026-06-09 prose sharpen was insufficient without an explicit anti-pattern for
  permission-asking at session end.
- **Google SRE:** action items must change behavior; adding this COE + AGENTS.md
  negative rule meets the bar; full prevention still relies on harness
  `completion_gate.py` on the next dirty turn.

## Root cause — 5 Whys

1. Why did the agent ask before committing? → It applied a generic tool-policy
   habit ("only commit when explicitly asked") at session close.
2. Why did that habit override repo rules? → The final response was drafted from
   habit without re-reading `AGENTS.md` completion-gate / standing-authorization
   lines written for exactly this workspace.
3. Why was standing authorization ignored? → The agent treated "reversible work
   done" as needing a *second* commit prompt, not as already authorized.
4. Why was droplet ahead of git? → SCP deploy was used mid-session without an
   immediate matching commit+push in the same step (deploy-without-version-control
   drift).
5. Why was this not caught mechanically? → **Root cause (systemic):** session-end
   handoff still mixes two conflicting instructions in agent context (global
   "ask before commit" vs workspace "commit every session is standing auth") with
   no explicit negative rule forbidding permission-asks at handoff.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| Write this COE; index in `docs/coe/README.md` | Prevent | Cursor agent | 2026-06-10 | Done |
| Sharpen `AGENTS.md` completion gate: **never ask** "want me to commit?" at session end when standing authorization applies; commit+push is default, blockers must be named | Prevent | Cursor agent | 2026-06-10 | Done |
| Commit+push all session work (`ai-memory-infra` + private BUILD-LOG); align git with droplet | Mitigate | Cursor agent | 2026-06-10 | Done |
| Deploy path: prefer `git pull` + compose rebuild on droplet after push, not SCP-only (document in runbook if missing) | Prevent | Build Agent | BACKLOG | Open |

## Lessons learned

**Standing authorization is not "no commits until asked again."** For this
workspace, verified reversible session work → commit+push in the same session is
the default happy path. The operator should never have to negotiate routine
hygiene. If a global agent policy conflicts with `AGENTS.md`, **the workspace
control plane wins.**
