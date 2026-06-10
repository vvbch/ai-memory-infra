# COE: Agent delegated an automatable action to the operator

- **Date:** 2026-06-10
- **Author(s):** Build Agent (session with operator)
- **Severity:** low *(no data loss or production impact; wasted operator attention on a mechanical step the agent could have done itself)*
- **Status:** closed
- **Related:** tenet 17 (minimize operator cognitive load; act on reversible decisions), AGENTS.md concierge rules ("do the parts I can do; only delegate clicks I genuinely can't"), tenet 13 (critical path)

## Summary

The operator completed the one-time secret setup for the weekly-scan automation
(adding `CURSOR_API_KEY` and `PRIVATE_REPO_PAT` as repo secrets). The next step
was to trigger `weekly-scan.yml` once to smoke-test the secrets. Instead of
running `gh workflow run weekly-scan.yml --ref main` from the terminal — a
one-line, fully reversible action well within agent capabilities — the agent gave
the operator click-by-click instructions to do it manually through the GitHub
Actions UI. The operator caught it immediately: "why can't you run this?"

## Impact

- **Operator cognitive load:** one unnecessary manual task delegated for no
  reason. Small in isolation, but the whole concierge model depends on the agent
  *never* offloading work it can do itself — each violation erodes trust in the
  "zero cognitive load" promise.
- No production, data, cost, or security impact.

## Timeline

- `2026-06-10 ~10:10` — Agent resumes session, confirms both secrets are set,
  repo-health green.
- `2026-06-10 ~10:10` — Agent writes a click-by-click manual delegation asking
  the operator to trigger the workflow from the GitHub Actions UI.
- `2026-06-10 ~10:11` — **Operator detects the error** ("why can't you run
  this?").
- `2026-06-10 ~10:11` — Agent self-corrects: runs `gh workflow run` from
  terminal. Workflow runs; both agent steps succeed; PR-creation steps fail
  (separate permission issue, not related to this COE).

## Detection

**Human catch (operator), same turn.** No mechanism validates whether a
delegated action could have been performed by the agent itself. The agent's
decision to delegate vs. self-execute is pure LLM judgment with no checkpoint.

## Industry benchmark

- **Amazon COE / "mechanisms not good intentions":** the concierge rules say
  "do the parts I can do" — but this was prose guidance, not a mechanism. Amazon
  would note the absence of a forcing function. Met on blamelessness and
  5-Whys structure.
- **Google SRE postmortem practice:** written timeline/impact/root-cause with
  action items — met. SRE would flag the detection gap (human-only catch)
  as needing an automated or checklist-based control.

## Root cause — 5 Whys

1. Why did the agent delegate the workflow trigger? → It pattern-matched
   "GitHub Actions page" as a web-console action requiring operator clicks.
2. Why did it assume web-console = operator? → The concierge rules heavily
   emphasize click-by-click UI guidance, creating a heuristic that anything
   involving a web platform defaults to delegation.
3. Why didn't the agent check for a CLI alternative first? → No rule requires
   a **pre-delegation check** ("can I do this myself via CLI/API?") before
   composing operator instructions.
4. Why is there no pre-delegation check? → The concierge rules were written for
   genuinely operator-only actions (account creation, password entry, consent)
   and never anticipated the agent confusing "I know the UI path" with "only
   the operator can do this."
5. Why did the rules not anticipate this? → **Root cause (systemic):** the
   concierge mode rules specify *how* to delegate (one step at a time, ELI5,
   success condition) but never specify *when* delegation is appropriate. The
   missing gate is: "before delegating, verify the action cannot be performed
   via available CLI/API tools." Without that gate, the agent defaults to the
   path it can describe most confidently (UI steps), not the path that
   minimizes operator load.

## Corrective actions

| Action | Type (Prevent / Detect / Mitigate) | Owner | Due | Status |
|---|---|---|---|---|
| Add pre-delegation check to AGENTS.md concierge rules: "Before delegating any action to the operator, verify it cannot be performed via CLI/API (`gh`, `curl`, shell, MCP). Delegate only genuinely operator-exclusive actions (credentials, consent, account creation with PII)" | Prevent | Build Agent | 2026-06-10 | done |
| Update automation README and workflow comments with accurate PAT permission requirements (Contents + Pull requests: Read and write) and Bitwarden vault item name | Prevent | Build Agent | 2026-06-10 | done |

## Lessons learned

The concierge rules optimized for *how* to delegate but never asked *whether* to
delegate. Tenet 17 says "act on reversible decisions" — triggering a CI workflow
is as reversible as it gets. The fix is a one-line pre-delegation gate in the
concierge rules: check CLI/API first, delegate only what genuinely requires the
operator's hands (credentials, consent, identity). Interview-worthy: a process
designed to reduce operator load can *increase* it if the agent confuses "I can
describe the UI path" with "the operator must walk it."
