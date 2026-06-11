---
name: operator-action
description: Use before asking the operator to click, type, or run anything (console steps, account setup, credentials, consent) — format the single operator-delegated action as purpose + exact action + visible success + wait point via scripts/operator_action.py.
---

# Operator Action Formatter (Operator Assistant — concierge mode)

Canonical spec: `ai-memory-infra/docs/skills/operator-assistant-concierge-action.md`
(governs). Concierge rules: `ai-memory-infra/AGENTS.md` § "How to teach / collaborate".
This skill is a thin trigger pointer.

Before delegating anything to the operator:

1. **Pre-delegation gate:** verify the action cannot be done via CLI/API/MCP
   (`gh`, `curl`, shell). Delegate only genuinely operator-exclusive steps
   (credentials entry, consent, account creation requiring PII). **Exception:**
   SSH passphrase / paste-once secrets → `operator-credential-handoff` skill
   (copy to clipboard only; agent runs `scripts/ssh_unlock.py`).
2. **Web-verify volatile UI steps** (console layouts drift) before giving
   click-by-click instructions.
3. Validate + render the action block from the `ai-memory-infra` repo root:

   `python scripts/operator_action.py --purpose "<ELI5 why>" --action "<exact single UI path or command>" --success "<visible success condition>" --check`

   then render it (drop `--check`) and end the response with it.

Rules:

- **One step at a time** — never a multi-step dump; wait for "tell me what you see".
- Vague "confirm it"-class verbs fail `--check` by design; fix the action, don't bypass.
- No Resume prompt while waiting on the operator inside the same flow.
