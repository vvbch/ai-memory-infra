# Skill: Operator Assistant — concierge action formatter

> Third entry in the agent-owned skills set (`docs/agent-personas.md` build order
> #3). Skills are editor-agnostic mechanisms in `scripts/`, owned by a persona,
> with an explicit store/retrieve boundary and a visible success condition.

**Implementation:** `scripts/operator_action.py`
**Owner persona:** Operator Assistant
**Related layer:** the Build Agent's `scripts/session_checkpoint.py` (capture) and
`scripts/completion_gate.py` (trigger) protect *repo* handoffs; this protects the
*operator* handoff — the moment the agent must delegate a step to Chandra.

## What pain it removes

`docs/coe/2026-06-09-concierge-handoff-regression.md`: the agent gave a vague
"confirm it" instruction and printed a resume prompt while operator action was
still pending. AGENTS.md already requires every delegated action to carry four
parts and to be one step at a time, but that was prose the model had to remember
— and a model forgot it.

This skill turns the rule into a deterministic mechanism. A delegated action
can no longer silently drop a part, ship a vague verb, or balloon into a
checklist, because `--check` fails before the operator ever sees it.

## What it does

1. **Validates the concierge contract** (`--check`): all four parts present, none
   vague, and the action is a **single step**. Exits non-zero when not — usable
   as a pre-show gate, the operator-facing analog of the checkpoint `--check`.
   - Required parts: `--purpose` (ELI5 why), `--action` (exact UI path/command),
     `--success` (visible success condition). `--wait` has a safe default.
   - Vague-phrase rejection: "confirm it", "verify that", "make sure",
     "set it up", "do the needful", "somewhere", etc.
   - One-step enforcement: an `--action` containing "then", "after that", a
     numbered/bulleted list, or semicolon-chained imperatives fails the gate.
2. **Renders the operator action block** in the AGENTS.md format:
   purpose → exact action → visible success → wait point ("tell me what you see").

## Store / retrieve boundary

| | |
|---|---|
| **May write** | the rendered operator action block (purpose, action, success, wait) + the date |
| **Must never write** | secrets, API keys, recovery codes, passwords, or any copied vault value — the action must **point at** where a secret lives (e.g. the Bitwarden `ai-memory-infra` folder), never contain it |
| **Canonical truth** | AGENTS.md "How to teach / collaborate" (Operator-delegated action format) + `docs/agent-personas.md` Operator Assistant success criteria |

## Success condition

`python scripts/operator_action.py --check --purpose ... --action ... --success ...`
returns PASS (exit 0) — all four parts present, none vague, single step — and the
rendered block reads as exactly one concierge-formatted action ending in a wait
point.

## Usage

```bash
# Pre-show gate (exit 1 if not concierge-safe):
python scripts/operator_action.py --check \
    --purpose "..." --action "..." --success "..."

# Render the single operator action block:
python scripts/operator_action.py \
    --purpose "Save the master API key off the server so it's never lost" \
    --action  "Open Bitwarden, unlock, open the 'ai-memory-infra' folder" \
    --success "You see an item named 'ADMIN_API_KEY' with a 43-character value" \
    --wait    "Tell me what you see and we'll continue."

# Machine-readable:
python scripts/operator_action.py --json --purpose ... --action ... --success ...
```

## When to use vs credential handoff

| Situation | Use |
|---|---|
| Operator must click/consent in a web UI | `operator_action.py` |
| Operator copies a secret to clipboard; agent runs the consumer | `operator-credential-handoff` / `scripts/ssh_unlock.py` |
| No secret; agent can run everything | Neither — just run it |

Cross-platform (tenet 3): pure Python stdlib, UTF-8 forced. Editor-agnostic
(tenet 2): any harness or a human can run it.
