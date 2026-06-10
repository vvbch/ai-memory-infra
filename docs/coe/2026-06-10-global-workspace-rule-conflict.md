# COE: Global Cursor user rules conflicted with workspace commit+push standing authorization

- **Date:** 2026-06-10
- **Author(s):** Cursor agent + operator (Chandra)
- **Severity:** Medium
- **Status:** actions-in-progress (control plane done; global Cursor rule update is operator step)
- **Related:** Tenets 2, 10, 11, 14, 16, 17; COEs `2026-06-08-atomic-handoff-failure.md`,
  `2026-06-09-session-handoff-omission.md`, `2026-06-10-session-end-commit-permission-ask.md`;
  ADR 027 (`completion_gate.py`); `AGENTS.md` completion gate

## Summary

Four handoff COEs in eight days traced to the same systemic cause: a global Cursor
user rule ("only commit when explicitly asked") fighting `AGENTS.md` standing
authorization (commit+push every touched repo for reversible work). Workspace
fixes sharpened prose and added `completion_gate.py`, but the global rule was
never updated — so agents kept defaulting conservative. Operator confirmed:
**workspace rules win**; park still commits; push is part of handoff; on conflict,
ask once then fix control plane same session.

## Impact

No production outage. Repeated control-plane / handoff friction: verified work left
local, permission-asks at session end, operator had to catch omissions manually.
Eroded trust that "done" means "on GitHub."

## Timeline

- `2026-06-08 → 2026-06-10` — Three prior COEs in this class; workspace prose +
  harness hook added; global user rule untouched.
- `2026-06-10` — Operator requested COE on why conflict persisted; agent sweep +
  structured questions.
- `2026-06-10` — Operator locked decisions: workspace wins, park+commit, push with
  commit, keep one-way-door pause list, ask-once-then-fix protocol.
- `2026-06-10` — `AGENTS.md` park + conflict-protocol sharpened; this COE written;
  global rule replacement text drafted (operator UI step remains).

## Detection

Human catch (operator) — recurrence after prior COEs proved workspace-only fixes
were insufficient without updating the global rule source.

## Industry benchmark

- **AWS/Amazon COE:** systemic root cause required; blame-free. Met — root cause is
  dual instruction sources with only half updated.
- **Google SRE:** action items must change behavior. Partially met — workspace
  layer done; global rule layer pending operator step (cannot be edited via repo).

## Root cause — 5 Whys

1. Why did agents keep not committing? → Global "only commit when asked" beat
   workspace standing authorization.
2. Why did workspace COEs not stop it? → They fixed `AGENTS.md` and hooks, not the
   global Cursor user rule in Settings.
3. Why wasn't the global rule updated? → No mechanism assigned an owner for
   cross-layer rule hygiene; agents cannot edit Cursor Settings programmatically
   (`cursor_dialog` MCP not exposed — see § cursor_dialog limitation below).
4. Why did agents not ask the operator? → Git safety is a conservative default;
   conflict was rationalized as "being helpful" rather than escalated.
5. Why is that possible? → **Root cause (systemic):** two instruction layers
   (global user rules + workspace `AGENTS.md`) with no versioned contract linking
   them; workspace said "generic habits lose" but global rule still said the
   opposite.

## Corrective actions

| Action | Type | Owner | Due | Status |
|---|---|---|---|---|
| Operator decisions locked via structured questions | Prevent | Operator | 2026-06-10 | Done |
| Sharpen `AGENTS.md`: park semantics + rule-conflict protocol | Prevent | Cursor agent | 2026-06-10 | Done |
| Write this COE + index | Prevent | Cursor agent | 2026-06-10 | Done |
| Replace global Cursor user rules per § Global rule replacement below | Prevent | Operator | 2026-06-10 | Open |
| Add `scripts/cursor_user_rules.py` clipboard workaround (cursor_dialog substitute) | Mitigate | Cursor agent | 2026-06-10 | Done |
| Commit+push control-plane + private BUILD-LOG | Mitigate | Cursor agent | 2026-06-10 | Done |

## Lessons learned

**Fix every layer that injects instructions.** Sharpening `AGENTS.md` while leaving
a contradictory global user rule is half a fix — the model sees both. Workspace
rules win for ai-memory, but the global rule must be updated to match so agents
stop re-litigating every handoff.

## cursor_dialog limitation (cannot fix from this repo)

Cursor 3.6.x ships `cursor_dialog` inside the built-in `cursor-app-control` MCP,
but the agent harness only exposes a subset of tools (`move_agent_to_root`,
`create_project`, `rename_chat`, …). `cursor_dialog` is **not** in
`listOfferings()` and is gated behind the `cursor_skill_enabled` feature flag —
so `CallMcpTool(cursor_dialog)` fails even though INSTRUCTIONS.md mentions it.

User rules are stored in Cursor's cloud KnowledgeBase API (`knowledgeBaseAdd` /
`List` / `Update`), not in a local file agents can edit.

**Workaround (versioned):** from `ai-memory-infra`, run
`python scripts/cursor_user_rules.py copy commit` — copies the replacement block
below to the clipboard for paste into **Cursor Settings → Rules**.

## Global rule replacement

Replace the full text of **`committing-changes-with-git`** in **Cursor Settings →
Rules** with:

---

**Commits — default vs ai-memory workspace**

- **Other projects:** only create commits when I explicitly ask. If unclear, ask first.
- **ai-memory workspace** (`ai-memory`, `ai-memory-infra`, and sibling repos): follow
  `ai-memory-infra/AGENTS.md` completion gate — commit and push every touched repo for
  verified reversible work without asking. Never end with "want me to commit?" Standing
  authorization applies. Pause only for one-way doors (spend, lock-in, deletion, data
  overwrite/retention, secrets, destructive ops) or explicit "don't commit yet."
- **"Park"** in ai-memory: stop new work on that thread; still checkpoint STATUS and
  commit+push completed changes.
- **Rule conflicts:** if a global user rule conflicts with workspace `AGENTS.md`, ask me
  once which wins; for ai-memory the answer is always workspace. Then update the
  conflicting rule or doc in the same session.

Git Safety Protocol (all projects):

- NEVER update the git config
- NEVER run destructive/irreversible git commands unless I explicitly request them
- NEVER skip hooks unless I explicitly request it
- NEVER force push to main/master; warn me if I request it
- Avoid git commit --amend except per the amend conditions in the original rule
- NEVER commit secrets (.env, credentials.json, etc.)
- When I **do** explicitly ask for a commit: run git status, git diff, git log in parallel;
  draft message; add; commit via HEREDOC; verify with git status
- DO NOT push to remote unless I explicitly ask — **except in ai-memory workspace,
  where push is part of routine reversible handoff per AGENTS.md tenet 11**

---

In **`creating-pull-requests`**, add this line after "DO NOT push to the remote
repository unless the user explicitly asks":

> **Exception — ai-memory workspace:** push is part of routine handoff when
> committing reversible work per `ai-memory-infra/AGENTS.md`; still do not push
> outside that standing authorization.
