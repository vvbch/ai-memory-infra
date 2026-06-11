---
name: session-checkpoint
description: Use at every logical step boundary, before any session handoff, and before emitting a Resume prompt in the ai-memory workspace — validate and render the STATUS.md/BUILD-LOG checkpoint from real git facts via scripts/session_checkpoint.py.
---

# Session Checkpoint (Build Agent)

Canonical spec: `ai-memory-infra/docs/skills/build-agent-session-checkpoint.md` (governs).
Working model: `ai-memory-infra/AGENTS.md` § "Working model" (tenet 16 — state lives in
files, not chat). This skill is a thin trigger pointer.

From the `ai-memory-infra` repo root:

- Validate the handoff contract (every touched repo committed+pushed, STATUS current):

  `python scripts/session_checkpoint.py --check`

- Render the STATUS-ready snippet + private BUILD-LOG entry from real facts:

  `python scripts/session_checkpoint.py --work "<what was done>" --verify "<how verified>" --next "<single next action>"`

- Append the BUILD-LOG entry to the private log: add `--write-log`.

Rules:

- A copy-paste **Resume prompt** is valid only after `--check` passes AND the response
  is a true handoff — never while waiting on the operator mid-flow.
- `STATUS.md` is **overwrite means replace** (no "prior update" blocks); shape is
  machine-enforced by `scripts/check_status_snapshot.py`.
- Before the final response also run `python scripts/handoff_verify.py` (final
  all-repo handoff verifier) and act on any failure it reports.
