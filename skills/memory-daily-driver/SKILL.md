---
name: memory-daily-driver
description: Use when the operator says "plan my day", "what's on my plate", "what's overdue", "log this", "todo", "remind me", "follow up <day>", "career contact reached out", "show career follow-ups", "we decided X", "we're reversing X", "remember that <fact>", or "done / that happened" — read/write the live ai-memory bank via scripts/memory.py with the mandatory confirmation contract.
---

# Memory Daily Driver (Operator Assistant)

Canonical practice: `ai-memory-infra/AGENTS.md` § "Memory Daily Driver — conversational
practice" (governs). Spec: `ai-memory-infra/docs/skills/operator-assistant-memory-daily-driver.md`.
This skill is a thin trigger pointer — read those before acting; do not improvise.

Run all commands from the `ai-memory-infra` repo root:

| the operator says | Run |
|---|---|
| "plan my day" / "what's on my plate?" | `python scripts/memory.py agenda` |
| "log this / todo / remind me / follow up <day>" | `python scripts/memory.py add-open-item "<verbatim>" [--due YYYY-MM-DD] [--revisit YYYY-MM-DD] [--venture <tag>]` |
| recruiter reachout | `add-open-item … --venture career` |
| "show career follow-ups" | `python scripts/memory.py recruiters` |
| "we decided X because Y" | `python scripts/memory.py add-decision "<decision + reason>" [--occurred YYYY-MM-DD]` |
| reversal | new `add-decision "Supersedes <old-id> ('<gist>'): <new>. Reason: <why>."` — never edit the old one |
| "remember that <fact>" | `python scripts/memory.py add-fact "<fact>" [--venture <tag>]` |
| "done / that happened" | `python scripts/memory.py close <id> --resolution "<what happened>"` |

Non-negotiables:

- **Confirmation contract:** after every write, echo exactly what was stored
  (verbatim text, type, resolved dates, ventures, short id). A silent write is a violation.
- Resolve date phrases to ISO dates and state them ("Friday" → next Friday's date).
- Never store secrets or transcript dumps; repo files beat memory for project state.
