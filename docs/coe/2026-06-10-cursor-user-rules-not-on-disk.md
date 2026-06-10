# COE: Cursor "user rules" are not editable local files on this machine

- **Date:** 2026-06-10
- **Author(s):** Cursor agent
- **Severity:** Medium (wrong mental model blocked fix)
- **Status:** closed
- **Related:** COE `2026-06-10-global-workspace-rule-conflict.md`;
  COE `2026-06-10-hallucinated-cursor-rule-name.md`; ADR 018 (pointer purity)

## Summary

The operator asked why the agent could not fix global Cursor user rules on the
filesystem. Investigation on Windows (Cursor 3.6.31) shows: the conflicting
commit policy text (`only create commits when explicitly asked`, tag
`committing-changes-with-git`) appears in the **agent system prompt** but was
**not found** in `%AppData%/Cursor`, `~/.cursor`, or the 269KB
`state.vscdb` `applicationUser` JSON blob. Cursor stores user rules in its
**cloud KnowledgeBase API** (`knowledgeBaseList` / `Add` / `Update` in
workbench code), synced to Settings → Rules. The built-in `cursor_dialog` MCP
that could update them is **not exposed** to this harness.

**Who wrote the rules?** If they exist in Settings → User rules, **you** (or a
prior session) added them via the Cursor UI — they sync to Cursor's cloud. If
User rules is **empty**, the commit restriction may be **Cursor default /
server-injected policy**, not a file we can patch locally. Either way, agents
here cannot `git commit` a fix to it.

## Impact

Agent implied editable local rules and a bogus rule name; operator could not
complete the handoff. Workspace control plane (`AGENTS.md`, hooks) remains the
enforceable layer we **can** fix in git.

## Investigation (2026-06-10, this machine)

| Location | Result |
|---|---|
| Grep `only create commits` / `committing-changes` under `%AppData%/Cursor` | **Not found** |
| `state.vscdb` key `applicationUser` (269KB JSON) | **No** commit-rule strings |
| `~/.cursor/rules/` global rule files | **Not present** (project `.cursor/rules/` only) |
| `cursor_dialog` MCP | **Not in tool offerings** (`cursor_skill_enabled` gate) |
| Workspace `.cursor/rules/*.mdc` | Thin pointers to `AGENTS.md` only (ADR 018) |

## Root cause — 5 Whys

1. Why couldn't the agent edit rules on disk? → They are not stored as plain
   files on this machine.
2. Why did the agent claim otherwise? → Assumed "user rules" = filesystem like
   `.cursor/rules`, conflated with internal prompt tags.
3. Why wasn't cloud/API path used? → `cursor_dialog` unavailable; no documented
   local API token for `knowledgeBaseUpdate`.
4. Why did operator see no rules in UI? → Either empty User rules (server default
   only) or UI/cloud sync mismatch (known Cursor forum reports).
5. **Root cause (systemic):** two rule layers were conflated — **(A)** git
   workspace rules we own, **(B)** Cursor cloud user rules / server defaults we
   must treat as external until verified in Settings or via exposed MCP.

## Corrective actions

| Action | Type | Owner | Status |
|---|---|---|---|
| Write this COE; index | Prevent | Agent | Done |
| Document layers in parent COE + `cursor_user_rules.py why-unavailable` | Prevent | Agent | Done |
| Operator: Settings → Rules → User rules — add rule from printed text if empty | Mitigate | Operator | Open |
| BACKLOG: request Cursor expose `cursor_dialog` or ship global rules file | Prevent | Operator | Open |

## What agents **can** fix in-repo

- `ai-memory-infra/AGENTS.md` standing authorization (done)
- `completion_gate.py` harness (done)
- Workspace `.cursor/rules` pointers (thin only)
- Print canonical replacement via `python scripts/cursor_user_rules.py show commit`

## Lessons learned

**Do not promise filesystem edits for Cursor User rules.** Verify storage layer
before delegating. For ai-memory, workspace `AGENTS.md` + hooks are the guarantee;
global Cursor rules are best-effort alignment.
