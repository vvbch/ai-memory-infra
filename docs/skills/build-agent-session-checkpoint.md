# Skill: Build Agent — session checkpoint

> First entry in the agent-owned skills set (`docs/agent-personas.md` build order
> #1). Skills are editor-agnostic mechanisms in `scripts/`, owned by a persona,
> with an explicit store/retrieve boundary and a visible success condition.

**Implementation:** `scripts/session_checkpoint.py`
**Owner persona:** Build Agent
**Related layer:** the *trigger* counterpart is `scripts/completion_gate.py`
(ADR 027/030). This skill is the *capture/format* layer; the gate is the *don't
let a missed handoff end the turn* layer.

## What pain it removes

Recurring handoff misses captured in the COEs:

- `2026-06-08-atomic-handoff-failure.md` — a touched repo (the package repo) was
  left uncommitted while the control plane looked clean.
- `2026-06-09-session-handoff-omission.md` — final responses claimed completion
  without an explicit, verified checkpoint.

A prose-only checkpoint lets the agent hand-wave "pushed", forget a touched repo,
or drift STATUS vs BUILD-LOG. This skill reads **git truth** for every project
repo and validates the handoff contract, so a checkpoint can't lie.

## What it does

1. **Gathers git facts** for every candidate repo (union of `AI_MEMORY_REPOS` +
   discovered siblings): branch, dirty?, ahead/behind, no-upstream, and the short
   HEAD commit id + subject.
2. **Validates the handoff contract** (`--check`): every touched repo is clean &
   pushed, and the required fields (`--work`, `--verify`, `--next`) are present.
   Exits non-zero when the contract is open — usable as a pre-final-response gate.
3. **Renders no-drift checkpoint text** from real facts:
   - a STATUS-ready `Done this session` + `Next action` snippet, naming each
     repo's latest pushed commit;
   - a private `BUILD-LOG.md` entry in the existing append-only format
     (`--write-log` appends it to the auto-located private log).

## Store / retrieve boundary

| | |
|---|---|
| **May write** | STATUS snippet, BUILD-LOG entry, repo git facts (branch, clean/pushed, short commit id + subject) |
| **Must never write** | secrets, raw vault values, long chat transcripts (it only reads git metadata + the fields you pass) |
| **Canonical truth** | the repo files. If memory disagrees with git/STATUS, the files win (Memory Steward rule) |

## Success condition

`python scripts/session_checkpoint.py --check` returns PASS (exit 0) — all
project repos clean & pushed and all required fields present — and the rendered
entry names each repo's latest pushed commit.

## Usage

```bash
# Pre-final-response gate (exit 1 if any repo is dirty/unpushed):
python scripts/session_checkpoint.py --check

# Render a checkpoint (repo facts + STATUS snippet + BUILD-LOG entry):
python scripts/session_checkpoint.py \
    --work "what this step did" \
    --verify "how it was verified" \
    --next "the single next action" \
    --phase "current phase"

# Also append the BUILD-LOG entry to the private log:
python scripts/session_checkpoint.py --work ... --verify ... --next ... --write-log
```

Cross-platform (tenet 3): pure Python stdlib + `git`, UTF-8 forced. Editor-
agnostic (tenet 2): any harness or a human can run it.
