# COE: Agent hallucinated Cursor Settings rule name `committing-changes-with-git`

- **Date:** 2026-06-10
- **Author(s):** Cursor agent
- **Severity:** Medium (operator trust / wasted time)
- **Status:** closed
- **Related:** COE `2026-06-10-global-workspace-rule-conflict.md`; `scripts/cursor_user_rules.py`

## Summary

The agent told the operator to open Cursor Settings and edit a rule named
`committing-changes-with-git`. That name does not exist in the Cursor UI. It is
an **internal XML tag** Cursor uses when injecting `<user_rule>` blocks into the
agent system prompt — not a user-visible label. The operator correctly called this
out.

## Impact

Operator spent time hunting a non-existent Settings entry. Eroded trust in
agent-delegated UI instructions. Did not block product work.

## Timeline

- `2026-06-10` — COE `2026-06-10-global-workspace-rule-conflict.md` and operator
  actions referenced `committing-changes-with-git` as a Settings rule title.
- `2026-06-10` — Operator: "i don't see such a rule. are you smoking?"
- `2026-06-10` — Agent corrected: internal tag vs UI label; COE UI note added.

## Detection

Human catch by operator.

## Root cause — 5 Whys

1. Why did the agent name a fake Settings rule? → It mapped an internal prompt tag
   directly to a UI label without verifying.
2. Why wasn't the UI verified? → The tag appeared in the agent's own context as
   `<committing-changes-with-git>` and was mistaken for the storage key/name.
3. Why did prior COEs repeat it? → The first COE baked in the wrong name and later
   docs copied it (tenet 10 drift).
4. Why no filesystem check for that string? → A grep of `%AppData%/Cursor` and
   `state.vscdb` finds **no** `committing-changes-with-git` string on disk.
5. **Root cause (systemic):** no rule that **agent prompt tags must never be cited
   as Cursor Settings UI labels** without a verified UI path or filesystem path.

## Corrective actions

| Action | Type | Owner | Status |
|---|---|---|---|
| Write this COE; index in `docs/coe/README.md` | Prevent | Agent | Done |
| Correct parent COE § Global rule replacement (UI note) | Prevent | Agent | Done |
| `cursor_user_rules.py`: never reference internal tag names in operator text | Prevent | Agent | Done |
| AGENTS.md: operator UI steps must be web/filesystem-verified | Prevent | Agent | Done |

## Lessons learned

**Prompt tags ≠ product UI.** If you cannot grep the name on disk or see it in
Settings, do not tell the operator to click it.
