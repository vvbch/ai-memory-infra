# COE: Clipboard delegation when print-in-chat was sufficient

- **Date:** 2026-06-10
- **Author(s):** Cursor agent
- **Severity:** Low–Medium (operator friction)
- **Status:** closed
- **Related:** COE `2026-06-10-hallucinated-cursor-rule-name.md`;
  `scripts/cursor_user_rules.py`; tenet 17 (minimize operator cognitive load)

## Summary

After drafting global user-rule replacement text, the agent defaulted to
`python scripts/cursor_user_rules.py copy commit` and told the operator the text
was "on your clipboard." The operator reported **nothing on the clipboard**.
Printing the text in chat (or opening the COE) would have worked immediately and
is verifiable.

## Impact

Failed handoff step; operator had to re-ask. Clipboard from agent subprocess is
unreliable (tkinter/clip sandbox, headless context, focus stealing).

## Timeline

- `2026-06-10` — Agent ran copy-to-clipboard twice; claimed success.
- `2026-06-10` — Operator: "i dont see anything on clipboard either. print it."

## Root cause — 5 Whys

1. Why was clipboard empty? → Subprocess clipboard APIs are unreliable from the
   agent shell; success stdout lied about operator-visible state.
2. Why use clipboard at all? → Assumed paste-into-Settings was faster than
   copy-from-chat.
3. Why not print first? → `cursor_user_rules.py` was designed copy-first; chat
   print treated as secondary.
4. Why is that wrong for concierge mode? → Operator cannot verify clipboard;
   chat text is immediately auditable (tenet 17).
5. **Root cause (systemic):** no rule that **text handoffs default to print in
   chat**; clipboard is opt-in only after operator asks.

## Corrective actions

| Action | Type | Owner | Status |
|---|---|---|---|
| Write this COE; index | Prevent | Agent | Done |
| `cursor_user_rules.py`: `show` is default; `copy` opt-in with warning | Prevent | Agent | Done |
| AGENTS.md concierge: print long text in chat; clipboard only on request | Prevent | Agent | Done |

## Lessons learned

**If the operator needs text, put it in the chat.** Clipboard is a bonus, not the
contract.
